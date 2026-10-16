from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Status = Literal["pending", "approved", "excluded", "amended"]


class ProjectTitleBlock(BaseModel):
    """Consensus fields from drawing title blocks (sheet title block)."""

    display_name: str | None = None
    location: str | None = None
    client: str | None = None
    architect: str | None = None
    mep: str | None = None
    mep_address: str | None = None
    mep_web: str | None = None
    stage: str | None = None
    scale: str | None = None
    paper: str | None = None
    disclaimer: str | None = None
    revision: str | None = None
    latest_date: str | None = None
    job_series: list[str] = Field(default_factory=list)
    floors: list[str] = Field(default_factory=list)


class ProjectOut(BaseModel):
    id: int
    uuid: str
    name: str
    premise: str | None = None
    owner: str | None = "Seneca Group Ltd"
    client: str | None = None
    architect: str | None = None
    drawing_count: int = 0
    occurrence_count: int = 0
    pending_count: int = 0
    title_block: ProjectTitleBlock | None = None


class DrawingOut(BaseModel):
    id: int
    project_id: int
    project_uuid: str | None = None
    drawing_number: str
    key: str  # URL key: drawing_number (unique in project)
    floor_tab_name: str | None = None
    scale: str | None = None
    revision: str | None = None
    source_pdf: str | None = None
    item_count: int = 0
    pending_count: int = 0
    approved_count: int = 0
    excluded_count: int = 0


class ItemOut(BaseModel):
    id: int
    document_id: int
    project_id: int
    item_id: str | None = None
    item_label: str | None = None
    legacy_item_id: str | None = None
    annotation: str | None = None
    linked_to: str | None = None
    qty: float = 0
    unit: str = "no."
    length_m: float | None = None
    size: str | None = None
    measurement_type: str | None = None
    measurement_type_help: str | None = None
    scope: str | None = None
    symbol_class: str | None = None
    confidence: float | None = None
    amber_flag: bool = False
    notes: str | None = None
    status: Status = "pending"
    amended_qty: float | None = None
    amended_notes: str | None = None
    reviewed_at: str | None = None
    effective_qty: float = 0
    category: str | None = None  # gold Excel section band (primary)
    excel_category: str | None = None
    catalog_category: str | None = None


class CategoryFacet(BaseModel):
    category: str
    count: int


class DrawingFacets(BaseModel):
    categories: list[CategoryFacet]
    statuses: list[dict]
    measurement_types: list[dict]


class ItemPatch(BaseModel):
    status: Status | None = None
    amended_qty: float | None = None
    amended_notes: str | None = None


class BulkAction(BaseModel):
    action: Literal["approve", "exclude"]
    # When true, only rows currently pending. When false, flip any non-target
    # status (so approve works after exclude-all and the reverse).
    only_pending: bool = False
    # Optional view filters — bulk applies to the same set as the table.
    status: str | None = None
    category: str | None = None
    measurement_type: str | None = None
    q: str | None = None


class SummaryRow(BaseModel):
    key: str
    label: str
    qty: float
    unit: str | None = None
    item_count: int = 0
    excluded_count: int = 0
