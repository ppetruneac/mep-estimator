"""Phase 2 — rules-first symbol identification.

Starter classes (inventory-guided):
  fcu_wall, fcu_cass, hbc, panel_heater, door_curtain, ahu, ashp, tray_note

Rules use tag proximity + CAD layer + colour + compact geometry.
YOLO is optional residual (see ``riser_extract.yolo``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from riser_extract.classify import is_bedroom_floor
from riser_extract.ids import CATALOGUE
from riser_extract.paths import PathSeg, filter_by_colour, is_reddish
from riser_extract.schema import SymbolDetection
from riser_extract.tags import TagHit


# YOLO / decision-log class names (stable keys)
CLASS_FCU_WALL = "fcu_wall"
CLASS_FCU_CASS = "fcu_cass"
CLASS_HBC = "hbc"
CLASS_PANEL = "panel_heater"
CLASS_CURTAIN = "door_curtain"
CLASS_AHU = "ahu"
CLASS_ASHP = "ashp"
CLASS_TRAY = "tray_note"

CLASS_TO_ITEM = {
    CLASS_FCU_WALL: "MEC-FCU-WALL",
    CLASS_FCU_CASS: "MEC-FCU-CASS",
    CLASS_HBC: "MEC-HBC",
    CLASS_PANEL: "ELEC-PNL",
    CLASS_CURTAIN: "ELEC-CUR",
    CLASS_AHU: "VENT-AHU",
    CLASS_ASHP: "PLUM-ASHP-DHW",
    CLASS_TRAY: None,  # size-specific; set by caller
}

# Classes rules solve on the Hubby Seneca set (decision log)
RULE_SOLVED_CLASSES = [
    CLASS_FCU_WALL,
    CLASS_FCU_CASS,
    CLASS_HBC,
    CLASS_PANEL,
    CLASS_CURTAIN,
    CLASS_AHU,
    CLASS_ASHP,
    CLASS_TRAY,
]

# Residual classes seen on drawings but not reliably typed by rules yet
YOLO_RESIDUAL_CANDIDATES = [
    "odu_module",
    "damper",
    "valve",
    "smoke_extract_fan",
    "calorifier",
]


@dataclass
class _GeomHit:
    bbox: list[float]
    layer: str | None
    colour: str | None
    dist_pt: float


def _expand(bbox: list[float], pad: float) -> list[float]:
    return [bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad]


def _clamp_bbox(bbox: list[float], page_w: float, page_h: float) -> list[float]:
    return [
        max(0.0, min(page_w, bbox[0])),
        max(0.0, min(page_h, bbox[1])),
        max(0.0, min(page_w, bbox[2])),
        max(0.0, min(page_h, bbox[3])),
    ]


def _centroid(bbox: list[float]) -> list[float]:
    return [0.5 * (bbox[0] + bbox[2]), 0.5 * (bbox[1] + bbox[3])]


def _is_compact(seg: PathSeg, max_side: float = 70.0, min_side: float = 3.0) -> bool:
    if not seg.bbox or len(seg.bbox) != 4:
        return False
    w = seg.bbox[2] - seg.bbox[0]
    h = seg.bbox[3] - seg.bbox[1]
    return min_side <= w <= max_side and min_side <= h <= max_side


def _nearest_compact(
    tag: TagHit,
    paths: list[PathSeg],
    *,
    max_dist: float = 120.0,
    prefer_layers: tuple[str, ...] = ("00AC Units", "MP-REFRIG", "TRAY"),
    prefer_colours: tuple[str, ...] = ("#ffff00", "#00dda5", "#139b48", "#00dd00"),
) -> _GeomHit | None:
    cands: list[tuple[float, float, PathSeg]] = []  # score, dist, seg
    for p in paths:
        if not _is_compact(p):
            continue
        d = math.hypot(p.cx - tag.cx, p.cy - tag.cy)
        if d < 5 or d > max_dist:
            continue
        score = d
        if p.layer in prefer_layers:
            score -= 25
        if p.colour_hex in prefer_colours:
            score -= 15
        if p.layer == "00AC Units":
            score -= 10
        cands.append((score, d, p))
    if not cands:
        return None
    cands.sort(key=lambda x: x[0])
    _, d, p = cands[0]
    return _GeomHit(bbox=list(p.bbox), layer=p.layer, colour=p.colour_hex, dist_pt=d)


def _fallback_box(tag: TagHit, size_pt: float = 36.0) -> list[float]:
    """Box centred just past the tag (symbol usually sits next to the label)."""
    half = size_pt / 2
    # Prefer a point slightly left of vertical text stacks (rotated labels)
    cx = tag.cx - 18.0
    cy = tag.cy
    return [cx - half, cy - half, cx + half, cy + half]


def _detection(
    symbol_class: str,
    bbox: list[float],
    *,
    confidence: float,
    source: str,
    linked_tag: str | None,
    layer: str | None,
    colour: str | None,
    m_per_pt: float,
    page_h: float,
    page_w: float,
    item_id_override: str | None = None,
    notes: str | None = None,
    amber: bool = False,
) -> SymbolDetection:
    bbox = _clamp_bbox(bbox, page_w, page_h)
    cx, cy = _centroid(bbox)
    item_id = item_id_override or CLASS_TO_ITEM.get(symbol_class)
    legacy = None
    if item_id and item_id in CATALOGUE:
        legacy = CATALOGUE[item_id].legacy_item_id
    return SymbolDetection(
        symbol_class=symbol_class,
        item_id=item_id,
        legacy_item_id=legacy,
        confidence=round(confidence, 3),
        source=source,
        amber_flag=amber or confidence < 0.55,
        pixel_bbox=[round(x, 2) for x in bbox],
        centroid_px=[round(cx, 2), round(cy, 2)],
        real_world_coords={
            "x_m": round(cx * m_per_pt, 3),
            "y_m": round((page_h - cy) * m_per_pt, 3),
        },
        linked_tag=linked_tag,
        linked_path_layer=layer,
        colour=colour,
        notes=notes,
    )


def identify_symbols_rules(
    tags: list[TagHit],
    paths: list[PathSeg],
    *,
    floor_tab_name: str,
    m_per_pt: float,
    page_width: float,
    page_height: float,
) -> list[SymbolDetection]:
    """Deterministic symbol detections from tags + nearby geometry."""
    bedroom = is_bedroom_floor(floor_tab_name)
    out: list[SymbolDetection] = []
    used_bboxes: list[list[float]] = []

    def overlaps(b: list[float], iou_thresh: float = 0.35) -> bool:
        for u in used_bboxes:
            ix0, iy0 = max(b[0], u[0]), max(b[1], u[1])
            ix1, iy1 = min(b[2], u[2]), min(b[3], u[3])
            iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
            inter = iw * ih
            if inter <= 0:
                continue
            a1 = max(1.0, (b[2] - b[0]) * (b[3] - b[1]))
            a2 = max(1.0, (u[2] - u[0]) * (u[3] - u[1]))
            if inter / min(a1, a2) >= iou_thresh:
                return True
        return False

    for tag in tags:
        if tag.is_label:
            continue

        symbol_class: str | None = None
        item_override: str | None = None
        base_conf = 0.9

        if tag.kind == "fcu":
            symbol_class = CLASS_FCU_WALL if bedroom else CLASS_FCU_CASS
            # Basement wall unit: FCU.B.10 is wall-mounted in gold
            if not bedroom and tag.normalised.endswith(".10") and floor_tab_name == "Basement":
                # weak prior — still cassette unless nearby says WALL (pipeline may refine)
                pass
            if "WALL" in (tag.text or "").upper():
                symbol_class = CLASS_FCU_WALL
        elif tag.kind == "hbc":
            symbol_class = CLASS_HBC
        elif tag.kind == "panel":
            symbol_class = CLASS_PANEL
        elif tag.kind == "curtain":
            symbol_class = CLASS_CURTAIN
        elif tag.kind == "ahu":
            symbol_class = CLASS_AHU
        elif tag.kind == "ashp":
            symbol_class = CLASS_ASHP
        elif tag.kind in {"tray400", "tray300"}:
            symbol_class = CLASS_TRAY
            item_override = "MEC-TRAY-400" if tag.kind == "tray400" else "MEC-TRAY-300"
        else:
            continue

        geom = _nearest_compact(tag, paths)
        if geom is not None:
            bbox = _expand(geom.bbox, pad=6.0)
            conf = base_conf
            if geom.dist_pt > 80:
                conf -= 0.15
            notes = f"tag-anchored compact geom d={geom.dist_pt:.1f}pt"
            layer, colour = geom.layer, geom.colour
        else:
            # Red electric bars for panel/curtain
            if symbol_class in {CLASS_PANEL, CLASS_CURTAIN}:
                reds = filter_by_colour(paths, red=True)
                best = None
                best_d = 1e9
                for p in reds:
                    d = math.hypot(p.cx - tag.cx, p.cy - tag.cy)
                    if d < best_d and d < 200:
                        best_d = d
                        best = p
                if best is not None:
                    bbox = _expand(best.bbox, pad=8.0)
                    conf = 0.82
                    notes = f"red bar near electric tag d={best_d:.1f}pt"
                    layer, colour = best.layer, best.colour_hex
                else:
                    bbox = _fallback_box(tag, size_pt=40.0)
                    conf = 0.55
                    notes = "fallback box — no red bar found"
                    layer = colour = None
            else:
                bbox = _fallback_box(tag, size_pt=40.0 if symbol_class != CLASS_HBC else 48.0)
                conf = 0.6
                notes = "fallback box — no compact geom near tag"
                layer = colour = None

        if overlaps(bbox):
            # nudge slightly so we still keep one detection per tag
            bbox = [bbox[0] + 4, bbox[1] + 4, bbox[2] + 4, bbox[3] + 4]

        det = _detection(
            symbol_class,
            bbox,
            confidence=conf,
            source="rule",
            linked_tag=tag.normalised,
            layer=layer,
            colour=colour,
            m_per_pt=m_per_pt,
            page_h=page_height,
            page_w=page_width,
            item_id_override=item_override,
            notes=notes,
            amber=conf < 0.55,
        )
        out.append(det)
        used_bboxes.append(det.pixel_bbox)

    # One tray symbol per size even if the note is printed twice
    tray_kept: set[str] = set()
    deduped: list[SymbolDetection] = []
    for det in out:
        if det.symbol_class == CLASS_TRAY:
            key = det.item_id or CLASS_TRAY
            if key in tray_kept:
                continue
            tray_kept.add(key)
        deduped.append(det)
    return deduped


def enrich_occurrences_with_symbols(
    occurrences: list,
    symbols: list[SymbolDetection],
) -> None:
    """Copy symbol fields onto matching Phase 1 occurrences (in place)."""
    by_tag: dict[str, SymbolDetection] = {}
    for s in symbols:
        if s.linked_tag:
            by_tag[s.linked_tag.upper()] = s

    for occ in occurrences:
        key = occ.annotation.upper()
        # FCU.B.01 style
        sym = by_tag.get(key)
        if sym is None:
            for tag, s in by_tag.items():
                if tag in key or key in tag:
                    sym = s
                    break
        if sym is None and occ.item_id:
            # match first unused symbol of same item_id
            for s in symbols:
                if s.item_id == occ.item_id and s.linked_tag:
                    # prefer exact later; skip bulk
                    continue
        if sym is not None:
            occ.symbol_class = sym.symbol_class
            occ.confidence = sym.confidence
            occ.source = sym.source
            occ.amber_flag = sym.amber_flag
            occ.centroid_px = sym.centroid_px
            if sym.pixel_bbox:
                occ.pixel_bbox = sym.pixel_bbox
