from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import connect
from app.models import DrawingOut

router = APIRouter(prefix="/api", tags=["drawings"])


@router.get("/projects/{project_id}/drawings", response_model=list[DrawingOut])
def list_drawings(project_id: int):
    conn = connect(readonly=True)
    try:
        proj = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not proj:
            raise HTTPException(404, "project not found")
        rows = conn.execute(
            """
            SELECT d.id, d.project_id, d.drawing_number, d.floor_tab_name, d.scale, d.revision, d.source_pdf,
              (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id) AS item_count,
              (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id AND COALESCE(o.status,'pending')='pending') AS pending_count,
              (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id AND o.status='approved') AS approved_count,
              (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id AND o.status='excluded') AS excluded_count
            FROM documents d
            WHERE d.project_id = ?
            ORDER BY d.floor_tab_name
            """,
            (project_id,),
        ).fetchall()
        return [DrawingOut(**dict(r)) for r in rows]
    finally:
        conn.close()


@router.get("/drawings/{drawing_id}", response_model=DrawingOut)
def get_drawing(drawing_id: int):
    conn = connect(readonly=True)
    try:
        r = conn.execute(
            """
            SELECT d.id, d.project_id, d.drawing_number, d.floor_tab_name, d.scale, d.revision, d.source_pdf,
              (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id) AS item_count,
              (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id AND COALESCE(o.status,'pending')='pending') AS pending_count,
              (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id AND o.status='approved') AS approved_count,
              (SELECT COUNT(*) FROM occurrences o WHERE o.document_id = d.id AND o.status='excluded') AS excluded_count
            FROM documents d WHERE d.id = ?
            """,
            (drawing_id,),
        ).fetchone()
        if not r:
            raise HTTPException(404, "drawing not found")
        return DrawingOut(**dict(r))
    finally:
        conn.close()
