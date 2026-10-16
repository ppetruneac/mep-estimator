"""Detect and deduplicate equipment tags (FCU.*, HB:, AHU:, etc.)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from riser_extract.text import Word, join_nearby_words

# FCU.B.01, FCU.02.01, FCU.0B.01 variants
FCU_RE = re.compile(r"\bFCU[.\s:_-]*([A-Z0-9]+)[.\s:_-]*(\d{1,3})\b", re.IGNORECASE)
# HB:0B:01, HB:02:01, HB.02.01
HB_RE = re.compile(r"\bHB[C]?[.\s:_-]*([A-Z0-9]+)[.\s:_-]*(\d{1,3})\b", re.IGNORECASE)
AHU_RE = re.compile(r"\bAHU[.\s:_-]*(\d{1,3})\b", re.IGNORECASE)
ASHP_RE = re.compile(r"\bASHP\b", re.IGNORECASE)
PANEL_RE = re.compile(r"ELECTRIC\s+PANEL\s+HEATER", re.IGNORECASE)
CURTAIN_RE = re.compile(r"(?:OVER\s*DOOR|DOOR)\s+CURTAIN|ELECTRIC\s+OVER\s+DOOR", re.IGNORECASE)
TRAY_400_RE = re.compile(r"400\s*MM\s*(?:WIDE\s*)?TRAY|TRAY[^\n]{0,40}400\s*MM", re.IGNORECASE)
TRAY_300_RE = re.compile(r"300\s*MM\s*(?:WIDE\s*)?TRAY|TRAY[^\n]{0,40}300\s*MM", re.IGNORECASE)
WALL_VRF_RE = re.compile(r"WALL\s+MOUNTED\s+(?:INTERNAL\s+)?VRF", re.IGNORECASE)
CASSETTE_LABEL_RE = re.compile(r"CEILING\s+MOUNTED\s+CASSETTE\s+FCU", re.IGNORECASE)
HBC_LABEL_RE = re.compile(r"HBC\s+CONTROLLER", re.IGNORECASE)
REFRIG_HBC_ROOMS_RE = re.compile(r"REFRIGERANT\s+FROM\s+HBC\s+TO\s+ROOMS", re.IGNORECASE)
RISER_RA_TB_RE = re.compile(r"R\s*/\s*A\s*&\s*T\s*/\s*B|RISE(?:R)?\s+.*(?:REFRIGERANT|R/A)", re.IGNORECASE)
PASSING_RE = re.compile(r"PASSING\s+(?:ROOM[- ]CONDITIONING\s+)?SYSTEMS", re.IGNORECASE)


@dataclass
class TagHit:
    kind: str  # fcu | hbc | ahu | panel | curtain | tray400 | tray300 | label | note
    text: str
    normalised: str
    x0: float
    y0: float
    x1: float
    y1: float
    is_label: bool = False  # typical-detail call-out, not a unit

    @property
    def cx(self) -> float:
        return 0.5 * (self.x0 + self.x1)

    @property
    def cy(self) -> float:
        return 0.5 * (self.y0 + self.y1)

    @property
    def bbox(self) -> list[float]:
        return [self.x0, self.y0, self.x1, self.y1]


def _norm_fcu(level: str, num: str) -> str:
    return f"FCU.{level.upper()}.{int(num):02d}"


def _norm_hb(level: str, num: str) -> str:
    return f"HB:{level.upper()}:{int(num):02d}"


def find_tags(words: list[Word]) -> list[TagHit]:
    phrases = join_nearby_words(words, max_gap_pt=18.0)
    # Wider merge pass for multi-word call-outs ("ELECTRIC PANEL HEATER")
    wide_phrases = join_nearby_words(words, max_gap_pt=36.0)
    hits: list[TagHit] = []

    def add_from_text(text: str, x0: float, y0: float, x1: float, y1: float) -> None:
        for m in FCU_RE.finditer(text):
            hits.append(
                TagHit(
                    kind="fcu",
                    text=m.group(0),
                    normalised=_norm_fcu(m.group(1), m.group(2)),
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                )
            )
        for m in HB_RE.finditer(text):
            # Avoid matching "HBC CONTROLLER" as HB:CON:…
            level = m.group(1)
            if level.upper() in {"CONTROLLER", "CONT", "BOX"}:
                continue
            hits.append(
                TagHit(
                    kind="hbc",
                    text=m.group(0),
                    normalised=_norm_hb(level, m.group(2)),
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                )
            )
        for m in AHU_RE.finditer(text):
            hits.append(
                TagHit(
                    kind="ahu",
                    text=m.group(0),
                    normalised=f"AHU:{int(m.group(1)):02d}",
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                )
            )
        if PANEL_RE.search(text):
            hits.append(
                TagHit("panel", text, "ELECTRIC PANEL HEATER", x0, y0, x1, y1)
            )
        if CURTAIN_RE.search(text):
            hits.append(
                TagHit("curtain", text, "ELECTRIC DOOR CURTAIN", x0, y0, x1, y1)
            )
        if TRAY_400_RE.search(text):
            hits.append(TagHit("tray400", text, "400 mm TRAY", x0, y0, x1, y1))
        if TRAY_300_RE.search(text):
            hits.append(TagHit("tray300", text, "300 mm TRAY", x0, y0, x1, y1))
        if WALL_VRF_RE.search(text):
            hits.append(
                TagHit("label", text, "WALL MOUNTED INTERNAL VRF", x0, y0, x1, y1, is_label=True)
            )
        if CASSETTE_LABEL_RE.search(text):
            hits.append(
                TagHit(
                    "label",
                    text,
                    "CEILING MOUNTED CASSETTE FCU",
                    x0,
                    y0,
                    x1,
                    y1,
                    is_label=True,
                )
            )
        if HBC_LABEL_RE.search(text):
            hits.append(
                TagHit("label", text, "HBC CONTROLLER", x0, y0, x1, y1, is_label=True)
            )
        if REFRIG_HBC_ROOMS_RE.search(text):
            hits.append(
                TagHit(
                    "note",
                    text,
                    "REFRIGERANT FROM HBC TO ROOMS",
                    x0,
                    y0,
                    x1,
                    y1,
                )
            )
        if RISER_RA_TB_RE.search(text):
            hits.append(TagHit("note", text, "RISER R/A & T/B", x0, y0, x1, y1))
        if PASSING_RE.search(text):
            hits.append(TagHit("note", text, "PASSING SYSTEMS", x0, y0, x1, y1))
        if ASHP_RE.search(text):
            hits.append(TagHit("ashp", text, "ASHP", x0, y0, x1, y1))

    for p in phrases + wide_phrases:
        add_from_text(p.text, p.x0, p.y0, p.x1, p.y1)

    # Rotated AutoCAD labels often put sibling words in parallel columns
    # (HEATER beside ELECTRIC/PANEL). Cluster known vocab by proximity.
    hits.extend(_cluster_phrase_hits(words, ("ELECTRIC", "PANEL", "HEATER"), "panel", "ELECTRIC PANEL HEATER"))
    hits.extend(
        _cluster_phrase_hits(
            words, ("ELECTRIC", "OVER", "DOOR", "CURTAIN"), "curtain", "ELECTRIC DOOR CURTAIN", min_hits=2
        )
    )
    hits.extend(
        _cluster_phrase_hits(
            words, ("WALL", "MOUNTED", "FCU"), "label", "WALL MOUNTED FCU", min_hits=2, is_label=True
        )
    )

    return dedupe_tags(hits)


def _cluster_phrase_hits(
    words: list[Word],
    vocab: tuple[str, ...],
    kind: str,
    normalised: str,
    *,
    min_hits: int = 3,
    is_label: bool = False,
    radius_pt: float = 55.0,
) -> list[TagHit]:
    """Group nearby words from a vocab into one annotation hit."""
    vocab_u = {v.upper() for v in vocab}
    candidates = [w for w in words if w.text.upper().strip(".,;:") in vocab_u]
    if len(candidates) < min_hits:
        return []
    used = [False] * len(candidates)
    out: list[TagHit] = []
    for i, seed in enumerate(candidates):
        if used[i]:
            continue
        cluster = [seed]
        used[i] = True
        changed = True
        while changed:
            changed = False
            for j, w in enumerate(candidates):
                if used[j]:
                    continue
                for c in cluster:
                    if (w.cx - c.cx) ** 2 + (w.cy - c.cy) ** 2 <= radius_pt * radius_pt:
                        cluster.append(w)
                        used[j] = True
                        changed = True
                        break
        kinds_present = {w.text.upper().strip(".,;:") for w in cluster}
        if kind == "panel":
            if not {"ELECTRIC", "PANEL", "HEATER"} <= kinds_present:
                continue
        elif len(kinds_present) < min_hits:
            continue
        x0 = min(w.x0 for w in cluster)
        y0 = min(w.y0 for w in cluster)
        x1 = max(w.x1 for w in cluster)
        y1 = max(w.y1 for w in cluster)
        out.append(
            TagHit(
                kind=kind,
                text=" ".join(w.text for w in cluster),
                normalised=normalised,
                x0=x0,
                y0=y0,
                x1=x1,
                y1=y1,
                is_label=is_label,
            )
        )
    return out


def dedupe_tags(hits: list[TagHit], radius_pt: float = 42.0) -> list[TagHit]:
    """Collapse identical normalised tags whose centroids are within radius_pt.

    42 pt ≈ 15 mm on A1 sheet.
    """
    kept: list[TagHit] = []
    for h in sorted(hits, key=lambda t: (t.kind, t.normalised, t.cx, t.cy)):
        dup = False
        for k in kept:
            if k.kind != h.kind or k.normalised != h.normalised:
                continue
            dx = k.cx - h.cx
            dy = k.cy - h.cy
            if dx * dx + dy * dy <= radius_pt * radius_pt:
                dup = True
                break
        if not dup:
            kept.append(h)
    return kept


def fcu_tags(hits: list[TagHit]) -> list[TagHit]:
    return [h for h in hits if h.kind == "fcu"]


def hbc_tags(hits: list[TagHit]) -> list[TagHit]:
    return [h for h in hits if h.kind == "hbc"]
