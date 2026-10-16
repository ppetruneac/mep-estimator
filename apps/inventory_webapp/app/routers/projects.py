from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import connect
from app.models import ProjectOut

router = APIRouter(prefix="/api", tags=["projects"])


@router.get("/projects", response_model=list[ProjectOut])
def list_projects():
    conn = connect(readonly=True)
    try:
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.premise,
              (SELECT COUNT(*) FROM documents d WHERE d.project_id = p.id) AS drawing_count,
              (SELECT COUNT(*) FROM occurrences o WHERE o.project_id = p.id) AS occurrence_count,
              (SELECT COUNT(*) FROM occurrences o
                 WHERE o.project_id = p.id AND COALESCE(o.status, 'pending') = 'pending') AS pending_count
            FROM projects p
            ORDER BY p.name
            """
        ).fetchall()
        return [ProjectOut(**dict(r)) for r in rows]
    finally:
        conn.close()


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int):
    conn = connect(readonly=True)
    try:
        r = conn.execute(
            """
            SELECT p.id, p.name, p.premise,
              (SELECT COUNT(*) FROM documents d WHERE d.project_id = p.id) AS drawing_count,
              (SELECT COUNT(*) FROM occurrences o WHERE o.project_id = p.id) AS occurrence_count,
              (SELECT COUNT(*) FROM occurrences o
                 WHERE o.project_id = p.id AND COALESCE(o.status, 'pending') = 'pending') AS pending_count
            FROM projects p WHERE p.id = ?
            """,
            (project_id,),
        ).fetchone()
        if not r:
            raise HTTPException(404, "project not found")
        return ProjectOut(**dict(r))
    finally:
        conn.close()
