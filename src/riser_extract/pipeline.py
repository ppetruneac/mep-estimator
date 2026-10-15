"""End-to-end extraction for one MEP PDF drawing."""

from __future__ import annotations

import logging
from pathlib import Path

from riser_extract.classify import is_bedroom_floor, occurrence_from_tag
from riser_extract.export import drawing_slug, write_json
from riser_extract.leaders import propose_leaders
from riser_extract.overlay import write_overlay
from riser_extract.page import open_page
from riser_extract.paths import (
    extract_paths,
    filter_by_colour,
    longest_cluster_length_m,
    paths_near,
    total_length_m,
)
from riser_extract.scale import (
    normalise_drawing_number,
    parse_drawing_number,
    parse_floor_tab,
    parse_title_fields,
    resolve_scale,
)
from riser_extract.schema import ExtractionResult, MeasurementType, Occurrence, Scope, TitleBlock
from riser_extract.tags import TagHit, find_tags, fcu_tags, hbc_tags
from riser_extract.text import extract_words, full_text, words_near

log = logging.getLogger(__name__)


def extract_drawing(pdf_path: str | Path) -> ExtractionResult:
    path = Path(pdf_path)
    # Phase 1 primary path is PyMuPDF. planlens is a declared dependency for
    # future IR/leader enrichment (GR-2) but is not required at runtime here.
    backend = "pymupdf"
    try:
        import planlens  # noqa: F401

        backend = "pymupdf (planlens installed)"
    except Exception as exc:  # pragma: no cover
        log.debug("planlens not importable: %s", exc)

    doc, page, info = open_page(path)
    try:
        words = extract_words(page)
        text = full_text(words)
        scale = resolve_scale(info, text)
        fields = parse_title_fields(text)
        drawing_number = normalise_drawing_number(
            parse_drawing_number(text, path.name)
        ) or path.stem
        floor = parse_floor_tab(text, path.name) or "Unknown"
        scale_str = scale.scale_str

        title = TitleBlock(
            project=fields.get("project"),
            drawing_number=drawing_number,
            title=None,
            floor=floor,
            floor_tab_name=floor,
            revision=fields.get("revision"),
            stage=fields.get("stage"),
            date=fields.get("date"),
            scale=scale_str,
            scale_ratio=scale.ratio,
            paper=scale.paper or "A1",
            disclaimer=fields.get("disclaimer"),
            page_width_pt=info.display_width,
            page_height_pt=info.display_height,
            rotation=info.rotation,
            measure_m_per_cm=info.measure_m_per_cm,
            m_per_pt=scale.m_per_pt,
            source_pdf=str(path),
            layers=info.layers,
            notes=f"scale_source={scale.source}; creator={info.creator}",
        )

        tags = find_tags(words)
        paths = extract_paths(page, scale.m_per_pt)
        links = {id(l.tag): l for l in propose_leaders(tags, paths)}

        occurrences: list[Occurrence] = []
        bedroom = is_bedroom_floor(floor)

        # Discrete equipment tags
        for hit in tags:
            if hit.kind in {"tray400", "tray300", "note"}:
                continue  # handled as length rows below
            link = links.get(id(hit))
            nearby = " ".join(w.text for w in words_near(words, hit.cx, hit.cy, 60))
            occ = occurrence_from_tag(
                hit,
                drawing_number=drawing_number,
                floor_tab_name=floor,
                scale=scale_str,
                linked_to=link.target_desc if link else None,
                nearby=nearby[:240] if nearby else None,
                layer=link.path.layer if link and link.path else None,
                colour=link.path.colour_hex if link and link.path else None,
            )
            if occ:
                # Wall vs cassette refinement from nearby text / floor type
                if hit.kind == "fcu":
                    near_u = (nearby or "").upper()
                    if bedroom or "WALL" in near_u or "WALL" in hit.text.upper():
                        occ.item_id = "MEC-FCU-WALL"
                        occ.legacy_item_id = "HC-FCU-WALL"
                        occ.category = "Indoor terminals"
                    elif "CASS" in near_u or "CEILING" in near_u:
                        occ.item_id = "MEC-FCU-CASS"
                        occ.legacy_item_id = "HC-FCU-CASS"
                        occ.category = "Indoor terminals"
                occurrences.append(occ)

        # Geometry: FCU → nearest HBC (bedroom / basement home-runs)
        fcus = fcu_tags(tags)
        hbcs = hbc_tags(tags)
        if fcus and hbcs:
            for fcu in fcus:
                nearest = min(
                    hbcs,
                    key=lambda h: (h.cx - fcu.cx) ** 2 + (h.cy - fcu.cy) ** 2,
                )
                dist_pt = ((nearest.cx - fcu.cx) ** 2 + (nearest.cy - fcu.cy) ** 2) ** 0.5
                plan_m = dist_pt * scale.m_per_pt
                # Crow-flies underestimates corridor routes — mark geometry
                occurrences.append(
                    Occurrence(
                        drawing_number=drawing_number,
                        floor_tab_name=floor,
                        scale=scale_str,
                        category="Refrigerant / F+R pipe",
                        item_id="MEC-CU-IN",
                        legacy_item_id="HC-CU-IN",
                        annotation=f"F+R / pair — {fcu.normalised} to {nearest.normalised}",
                        linked_to=nearest.normalised,
                        count=plan_m,
                        unit="m",
                        measurement_type=MeasurementType.GEOMETRY,
                        scope=Scope.IN,
                        length_m=round(plan_m, 2),
                        pixel_bbox=fcu.bbox,
                        real_world_coords={
                            "from": {"x_m": round(fcu.cx * scale.m_per_pt, 3), "y_m": round((info.display_height - fcu.cy) * scale.m_per_pt, 3)},
                            "to": {"x_m": round(nearest.cx * scale.m_per_pt, 3), "y_m": round((info.display_height - nearest.cy) * scale.m_per_pt, 3)},
                            "method": "tag-to-HBC crow-flies",
                        },
                        notes="Geometry estimate (crow-flies). Corridor route will be longer; Phase 4 applies tender conversion.",
                        colour=None,
                    )
                )

        # Tray lengths — prefer CAD layer "TRAY", then cyan near a tray note.
        # Do not sum every cyan stroke on the sheet (that over-counts grids).
        tray_hits = [t for t in tags if t.kind in {"tray400", "tray300"}]
        cyan = filter_by_colour(paths, cyan=True)
        layer_tray = [p for p in paths if p.layer and "TRAY" in (p.layer or "").upper()]

        def measure_tray(hit: TagHit | None) -> tuple[float, str]:
            if layer_tray:
                length = longest_cluster_length_m(layer_tray, gap_pt=50.0)
                if length >= 5.0:
                    return length, "TRAY layer cluster"
            if hit is not None:
                near = paths_near(cyan, hit.cx, hit.cy, radius_pt=200)
                length = longest_cluster_length_m(near, gap_pt=35.0) if near else 0.0
                if length >= 5.0:
                    return length, f"cyan near tray note ({len(near)} segs)"
            return 0.0, "unresolved"

        # One row per tray size even if the note is printed twice
        seen_tray_kinds: set[str] = set()
        unique_tray_hits: list[TagHit] = []
        for hit in tray_hits:
            if hit.kind in seen_tray_kinds:
                continue
            seen_tray_kinds.add(hit.kind)
            unique_tray_hits.append(hit)

        emitted_tray = False
        for hit in unique_tray_hits:
            item_id = "MEC-TRAY-400" if hit.kind == "tray400" else "MEC-TRAY-300"
            legacy = "HC-TRAY-400" if hit.kind == "tray400" else "HC-TRAY-300"
            length, how = measure_tray(hit)
            mtype = MeasurementType.SCALED if length >= 5.0 else MeasurementType.PRINTED
            occurrences.append(
                Occurrence(
                    drawing_number=drawing_number,
                    floor_tab_name=floor,
                    scale=scale_str,
                    category="Tray / containment",
                    item_id=item_id,
                    legacy_item_id=legacy,
                    annotation=hit.normalised,
                    linked_to="tray hatch/spine",
                    count=round(length, 2),
                    unit="m",
                    size="400 mm" if hit.kind == "tray400" else "300 mm",
                    measurement_type=mtype,
                    scope=Scope.IN,
                    length_m=round(length, 2) if length else None,
                    pixel_bbox=hit.bbox,
                    notes=(
                        f"Scaled via {how}. No flood-fill."
                        if length
                        else "Tray note found; spine length not resolved from vectors."
                    ),
                    layer="TRAY",
                )
            )
            emitted_tray = True

        if not emitted_tray:
            length, how = measure_tray(None)
            if length >= 5.0:
                size = "300 mm" if floor == "Basement" else "400 mm"
                item_id = "MEC-TRAY-300" if floor == "Basement" else "MEC-TRAY-400"
                legacy = "HC-TRAY-300" if floor == "Basement" else "HC-TRAY-400"
                occurrences.append(
                    Occurrence(
                        drawing_number=drawing_number,
                        floor_tab_name=floor,
                        scale=scale_str,
                        category="Tray / containment",
                        item_id=item_id,
                        legacy_item_id=legacy,
                        annotation=f"{size} tray (layer)",
                        count=round(length, 2),
                        unit="m",
                        size=size,
                        measurement_type=MeasurementType.SCALED,
                        scope=Scope.IN,
                        length_m=round(length, 2),
                        notes=f"No tray text hit; length from {how}.",
                        layer="TRAY",
                    )
                )

        # Refrigerant / riser notes
        for hit in tags:
            if hit.kind != "note":
                continue
            nearby = " ".join(w.text for w in words_near(words, hit.cx, hit.cy, 80))
            if "REFRIGERANT FROM HBC" in hit.normalised:
                # Aggregate of geometry home-runs already emitted; keep note as printed
                occurrences.append(
                    Occurrence(
                        drawing_number=drawing_number,
                        floor_tab_name=floor,
                        scale=scale_str,
                        category="Refrigerant / F+R pipe",
                        item_id="MEC-CU-IN",
                        legacy_item_id="HC-CU-IN",
                        annotation=hit.normalised,
                        count=float(len(fcus)),
                        unit="no.",
                        measurement_type=MeasurementType.PRINTED,
                        scope=Scope.IN,
                        pixel_bbox=hit.bbox,
                        notes="Printed note. Per-FCU geometry lengths listed separately.",
                        raw_text_nearby=nearby[:240],
                    )
                )
            elif "RISER" in hit.normalised or "PASSING" in hit.normalised:
                occurrences.append(
                    Occurrence(
                        drawing_number=drawing_number,
                        floor_tab_name=floor,
                        scale=scale_str,
                        category="Refrigerant / F+R pipe",
                        item_id="MEC-CU-RISER",
                        legacy_item_id="HC-CU-RISER",
                        annotation=hit.normalised,
                        linked_to="riser box",
                        count=1.0,
                        unit="no.",
                        measurement_type=MeasurementType.PRINTED,
                        scope=Scope.INTERFACE,
                        pixel_bbox=hit.bbox,
                        notes="Riser / passing-systems note. Vertical metres need storey height (Phase 4).",
                        raw_text_nearby=nearby[:240],
                    )
                )

        result = ExtractionResult(
            title_block=title,
            occurrences=occurrences,
            backend=backend,
        )
        # stash for overlay callers
        result._tags = tags  # type: ignore[attr-defined]
        result._paths = paths  # type: ignore[attr-defined]
        return result
    finally:
        doc.close()


def extract_and_write(
    pdf_path: str | Path,
    out_dir: str | Path,
    *,
    overlay: bool = True,
) -> tuple[ExtractionResult, Path]:
    path = Path(pdf_path)
    result = extract_drawing(path)
    slug = drawing_slug(result.title_block.drawing_number, path.stem)
    json_dir = Path(out_dir) / "inventory_json"
    json_path = write_json(result, json_dir, slug)
    if overlay:
        tags: list[TagHit] = getattr(result, "_tags", [])
        paths = getattr(result, "_paths", [])
        overlay_path = Path(out_dir) / "overlays" / f"{slug}.pdf"
        write_overlay(path, overlay_path, tags=tags, paths=paths, result=result)
    return result, json_path
