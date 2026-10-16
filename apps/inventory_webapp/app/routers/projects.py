from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import connect, get_project_by_uuid
from app.models import ProjectOut, ProjectTitleBlock
from app.titleblock import project_titleblock_summary

router = APIRouter(prefix="/api", tags=["projects"])


def _project_out(conn, row) -> ProjectOut:
    pid = row["id"]
    counts = conn.execute(
        """
        SELECT
          (SELECT COUNT(*) FROM documents d WHERE d.project_id = ?) AS drawing_count,
          (SELECT COUNT(*) FROM occurrences o WHERE o.project_id = ?) AS occurrence_count,
          (SELECT COUNT(*) FROM occurrences o
             WHERE o.project_id = ? AND COALESCE(o.status, 'pending') = 'pending') AS pending_count
        """,
        (pid, pid, pid),
    ).fetchone()
    # Always derive parties from stored title blocks / PDF so cards stay populated
    tb = project_titleblock_summary(conn, pid)
    client = tb.get("client")
    architect = tb.get("architect")
    owner = row["owner"] if "owner" in row.keys() else None
    owner = owner or tb.get("mep") or "Seneca Group Ltd"
    return ProjectOut(
        id=pid,
        uuid=row["uuid"],
        name=row["name"],
        premise=row["premise"],
        owner=owner,
        client=client,
        architect=architect,
        drawing_count=counts["drawing_count"],
        occurrence_count=counts["occurrence_count"],
        pending_count=counts["pending_count"],
        title_block=ProjectTitleBlock(**{k: v for k, v in tb.items() if k in ProjectTitleBlock.model_fields}),
    )


@router.get("/projects", response_model=list[ProjectOut])
def list_projects():
    conn = connect(readonly=True)
    try:
        rows = conn.execute("SELECT * FROM projects ORDER BY name").fetchall()
        return [_project_out(conn, r) for r in rows]
    finally:
        conn.close()


@router.get("/projects/{project_uuid}", response_model=ProjectOut)
def get_project(project_uuid: str):
    conn = connect(readonly=True)
    try:
        row = get_project_by_uuid(conn, project_uuid)
        if not row:
            raise HTTPException(404, "project not found")
        return _project_out(conn, row)
    finally:
        conn.close()
