from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import connect, get_project_by_uuid
from app.models import DrawingOut
from app.services import resolve_drawing

router = APIRouter(prefix="/api", tags=["drawings"])


def _drawing_out(row, project_uuid: str | None = None) -> DrawingOut:
    puuid = project_uuid
    if puuid is None and "project_uuid" in row.keys():
        puuid = row["project_uuid"]
    number = row["drawing_number"]
    return DrawingOut(
        id=row["id"],
        project_id=row["project_id"],
        project_uuid=puuid,
        drawing_number=number,
        key=number,
        floor_tab_name=row["floor_tab_name"],
        scale=row["scale"],
        revision=row["revision"],
        source_pdf=row["source_pdf"],
        item_count=row["item_count"],
        pending_count=row["pending_count"],
        approved_count=row["approved_count"],
        excluded_count=row["excluded_count"],
    )


_DRAWING_SELECT = """
SELECT d.id, d.project_id, d.drawing_number, d.floor_tab_name, d.scale, d.revision, d.source_pdf,
  p.uuid AS project_uuid,
  (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id) AS item_count,
  (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id AND COALESCE(o.status,'pending')='pending') AS pending_count,
  (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id AND o.status='approved') AS approved_count,
  (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id AND o.status='excluded') AS excluded_count
FROM documents d
JOIN projects p ON p.id = d.project_id
"""


@router.get("/projects/{project_uuid}/drawings", response_model=list[DrawingOut])
def list_drawings(project_uuid: str):
    conn = connect(readonly=True)
    try:
        proj = get_project_by_uuid(conn, project_uuid)
        if not proj:
            raise HTTPException(404, "project not found")
        rows = conn.execute(
            _DRAWING_SELECT + " WHERE d.project_id = ? ORDER BY d.floor_tab_name",
            (proj["id"],),
        ).fetchall()
        return [_drawing_out(r, project_uuid) for r in rows]
    finally:
        conn.close()


@router.get("/projects/{project_uuid}/drawings/{drawing_key}", response_model=DrawingOut)
def get_drawing_by_key(project_uuid: str, drawing_key: str):
    conn = connect(readonly=True)
    try:
        doc = resolve_drawing(conn, project_uuid, drawing_key)
        if not doc:
            raise HTTPException(404, "drawing not found")
        r = conn.execute(
            _DRAWING_SELECT + " WHERE d.id = ?",
            (doc["id"],),
        ).fetchone()
        return _drawing_out(r, project_uuid)
    finally:
        conn.close()


@router.get("/drawings/{drawing_id}", response_model=DrawingOut)
def get_drawing(drawing_id: int):
    conn = connect(readonly=True)
    try:
        r = conn.execute(
            _DRAWING_SELECT + " WHERE d.id = ?",
            (drawing_id,),
        ).fetchone()
        if not r:
            raise HTTPException(404, "drawing not found")
        return _drawing_out(r)
    finally:
        conn.close()
