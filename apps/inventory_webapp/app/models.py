from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Status = Literal["pending", "approved", "excluded", "amended"]


class ProjectTitleBlock(BaseModel):
    """Consensus fields from drawing title blocks (sheet bottom-left)."""

    display_name: str | None = None
    location: str | None = None
    client: str | None = None
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
    drawing_count: int = 0
    occurrence_count: int = 0
    pending_count: int = 0
    title_block: ProjectTitleBlock | None = None


class DrawingOut(BaseModel):
    id: int
    project_id: int
    project_uuid: str | None = None
    drawing_number: str
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
    legacy_item_id: str | None = None
    annotation: str | None = None
    linked_to: str | None = None
    qty: float = 0
    unit: str = "no."
    length_m: float | None = None
    size: str | None = None
    measurement_type: str | None = None
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
    category: str | None = None


class ItemPatch(BaseModel):
    status: Status | None = None
    amended_qty: float | None = None
    amended_notes: str | None = None


class BulkAction(BaseModel):
    action: Literal["approve", "exclude"]
    only_pending: bool = True


class SummaryRow(BaseModel):
    key: str
    label: str
    qty: float
    unit: str | None = None
    item_count: int = 0
    excluded_count: int = 0
