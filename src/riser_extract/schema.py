"""Phase 1 extraction schema.

Coordinates
-----------
* ``pixel_bbox`` — displayed page frame (rotation applied, origin top-left, y down),
  PDF points. Matches a rendered page image / overlay.
* ``real_world_coords`` — metres on site, origin bottom-left of the plotted sheet.

Item IDs
--------
Live IDs use trade prefixes: ``MEC`` / ``ELEC`` / ``PLUM`` / ``VENT``.

The drawings-reader skill still documents the heating-and-cooling package
prefix ``HC-*`` (and ``VT-*`` / ``PH-*``). Every occurrence that gets a live
``item_id`` also carries ``legacy_item_id`` with that skill ID so rate books
and GR-3 can join either side.

``length_m`` is the one-way plan route in metres. Do not bake tender conversion
(×2 pipes × 1.15 + tails) into it — that is Phase 4.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MeasurementType(str, Enum):
    PRINTED = "printed"
    SCALED = "scaled"
    GEOMETRY = "geometry"
    VERTICAL = "vertical"
    SPECIFIED_NOT_DRAWN = "specified-not-drawn"
    EXCLUDED = "excluded"


class Scope(str, Enum):
    IN = "in"
    INTERFACE = "interface"
    OUT = "out"


class PointM(BaseModel):
    x: float
    y: float


class TitleBlock(BaseModel):
    project: str | None = None
    client: str | None = None
    drawing_number: str | None = None
    title: str | None = None
    floor: str | None = None
    floor_tab_name: str | None = None
    revision: str | None = None
    stage: str | None = None
    date: str | None = None
    scale: str | None = None
    scale_ratio: int | None = None  # N in 1:N
    paper: str | None = None
    disclaimer: str | None = None
    page_width_pt: float | None = None
    page_height_pt: float | None = None
    rotation: int = 0
    measure_m_per_cm: float | None = None
    m_per_pt: float | None = None
    source_pdf: str | None = None
    layers: list[str] = Field(default_factory=list)
    notes: str | None = None


class Occurrence(BaseModel):
    drawing_number: str
    page: int = 1
    floor_tab_name: str
    scale: str
    category: str | None = None
    item_id: str | None = None
    legacy_item_id: str | None = None
    annotation: str
    linked_to: str | None = None
    count: float = 1.0
    unit: str = "no."
    size: str | None = None
    measurement_type: MeasurementType = MeasurementType.PRINTED
    scope: Scope = Scope.IN
    length_m: float | None = None
    pixel_bbox: list[float] | None = None  # [x0, y0, x1, y1] displayed frame
    real_world_coords: dict[str, Any] | None = None
    layer: str | None = None
    colour: str | None = None
    notes: str | None = None
    raw_text_nearby: str | None = None


class ExtractionResult(BaseModel):
    title_block: TitleBlock
    occurrences: list[Occurrence] = Field(default_factory=list)
    extractor_version: str = "0.1.0"
    backend: str = "pymupdf"

    def summary(self) -> dict[str, Any]:
        by_id: dict[str, float] = {}
        for occ in self.occurrences:
            key = occ.item_id or occ.annotation
            if occ.unit == "m" and occ.length_m is not None:
                by_id[key] = by_id.get(key, 0.0) + float(occ.length_m)
            else:
                by_id[key] = by_id.get(key, 0.0) + float(occ.count)
        return {
            "drawing_number": self.title_block.drawing_number,
            "floor_tab_name": self.title_block.floor_tab_name,
            "scale": self.title_block.scale,
            "n_occurrences": len(self.occurrences),
            "backend": self.backend,
            "totals": by_id,
        }
