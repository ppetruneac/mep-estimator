"""Map tag hits and notes to provisional trade item_ids."""

from __future__ import annotations

from riser_extract.ids import CATALOGUE, ItemSpec, spec_for
from riser_extract.schema import MeasurementType, Occurrence, Scope
from riser_extract.tags import TagHit


def classify_tag(hit: TagHit, *, wall_floor: bool = False) -> ItemSpec | None:
    """Return an ItemSpec for a discrete tag, or None for labels/notes."""
    if hit.is_label:
        return None
    if hit.kind == "fcu":
        # Basement tags are mostly cassettes; bedroom floors are wall VRF.
        if wall_floor:
            return CATALOGUE["MEC-FCU-WALL"]
        # Heuristic: FCU.B.* on basement → cassette unless text says wall
        if "WALL" in hit.text.upper():
            return CATALOGUE["MEC-FCU-WALL"]
        return CATALOGUE["MEC-FCU-CASS"]
    if hit.kind == "hbc":
        return CATALOGUE["MEC-HBC"]
    if hit.kind == "ahu":
        return CATALOGUE["VENT-AHU"]
    if hit.kind == "panel":
        return CATALOGUE["ELEC-PNL"]
    if hit.kind == "curtain":
        return CATALOGUE["ELEC-CUR"]
    if hit.kind == "ashp":
        return CATALOGUE["PLUM-ASHP-DHW"]
    if hit.kind == "tray400":
        return CATALOGUE["MEC-TRAY-400"]
    if hit.kind == "tray300":
        return CATALOGUE["MEC-TRAY-300"]
    if hit.kind == "note":
        if hit.normalised.startswith("REFRIGERANT FROM HBC"):
            return CATALOGUE["MEC-CU-IN"]
        if "RISER" in hit.normalised or "PASSING" in hit.normalised:
            return CATALOGUE["MEC-CU-RISER"]
    return None


def is_bedroom_floor(floor_tab_name: str | None) -> bool:
    if not floor_tab_name:
        return False
    return floor_tab_name in {
        "First Floor",
        "Second Floor",
        "Third Floor",
        "Fourth Floor",
        "Fifth Floor",
        "Sixth Floor",
        "Seventh Floor",
        "Eighth Floor",
        "Ninth Floor",
    }


def occurrence_from_tag(
    hit: TagHit,
    *,
    drawing_number: str,
    floor_tab_name: str,
    scale: str,
    page: int = 1,
    linked_to: str | None = None,
    nearby: str | None = None,
    length_m: float | None = None,
    measurement_type: MeasurementType = MeasurementType.PRINTED,
    layer: str | None = None,
    colour: str | None = None,
) -> Occurrence | None:
    wall_floor = is_bedroom_floor(floor_tab_name)
    spec = classify_tag(hit, wall_floor=wall_floor)
    if hit.is_label:
        return Occurrence(
            drawing_number=drawing_number,
            page=page,
            floor_tab_name=floor_tab_name,
            scale=scale,
            category=None,
            item_id=None,
            legacy_item_id=None,
            annotation=hit.normalised,
            linked_to=linked_to,
            count=0.0,
            unit="no.",
            measurement_type=MeasurementType.PRINTED,
            scope=Scope.IN,
            pixel_bbox=hit.bbox,
            notes="Typical-detail / call-out label — not an extra unit",
            raw_text_nearby=nearby,
            layer=layer,
            colour=colour,
        )

    if spec is None and hit.kind == "note":
        # Still emit the note for audit even without a firm ID
        return Occurrence(
            drawing_number=drawing_number,
            page=page,
            floor_tab_name=floor_tab_name,
            scale=scale,
            annotation=hit.normalised,
            linked_to=linked_to,
            count=1.0,
            unit="no.",
            measurement_type=measurement_type,
            scope=Scope.IN,
            length_m=length_m,
            pixel_bbox=hit.bbox,
            notes="Annotation note — provisional",
            raw_text_nearby=nearby,
            layer=layer,
            colour=colour,
        )

    if spec is None:
        return None

    unit = spec.unit
    count = 1.0
    if unit == "m":
        count = float(length_m) if length_m is not None else 0.0
    return Occurrence(
        drawing_number=drawing_number,
        page=page,
        floor_tab_name=floor_tab_name,
        scale=scale,
        category=spec.category,
        item_id=spec.item_id,
        legacy_item_id=spec.legacy_item_id,
        annotation=hit.normalised if hit.kind in {"fcu", "hbc", "ahu"} else hit.text,
        linked_to=linked_to,
        count=count if unit != "m" else (length_m or 0.0),
        unit=unit,
        size="400 mm" if spec.item_id == "MEC-TRAY-400" else ("300 mm" if spec.item_id == "MEC-TRAY-300" else None),
        measurement_type=measurement_type,
        scope=Scope(spec.scope),
        length_m=length_m if unit == "m" else None,
        pixel_bbox=hit.bbox,
        notes=None,
        raw_text_nearby=nearby,
        layer=layer,
        colour=colour,
    )


def apply_spec(occ: Occurrence, item_id: str) -> Occurrence:
    spec = spec_for(item_id)
    if not spec:
        return occ
    occ.item_id = spec.item_id
    occ.legacy_item_id = spec.legacy_item_id
    occ.category = spec.category
    occ.unit = spec.unit
    occ.scope = Scope(spec.scope)
    return occ
