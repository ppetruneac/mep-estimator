from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import connect, get_project_by_uuid
from app.models import SummaryRow
from app.services import effective_qty

router = APIRouter(prefix="/api", tags=["summary"])


@router.get("/projects/{project_uuid}/summary/by-floor", response_model=list[SummaryRow])
def summary_by_floor(project_uuid: str):
    conn = connect(readonly=True)
    try:
        proj = get_project_by_uuid(conn, project_uuid)
        if not proj:
            raise HTTPException(404, "project not found")
        project_id = proj["id"]
        docs = conn.execute(
            "SELECT id, floor_tab_name, drawing_number FROM documents WHERE project_id = ? ORDER BY floor_tab_name",
            (project_id,),
        ).fetchall()
        out: list[SummaryRow] = []
        for d in docs:
            rows = conn.execute(
                "SELECT * FROM occurrences WHERE document_id = ?",
                (d["id"],),
            ).fetchall()
            qty = 0.0
            approved_n = 0
            excluded_n = 0
            unit = None
            for r in rows:
                st = r["status"] or "pending"
                if st == "excluded":
                    excluded_n += 1
                    continue
                if st in ("approved", "amended"):
                    qty += effective_qty(r)
                    approved_n += 1
                    unit = unit or r["unit"]
            label = d["floor_tab_name"] or d["drawing_number"]
            out.append(
                SummaryRow(
                    key=str(d["id"]),
                    label=label,
                    qty=round(qty, 3),
                    unit=unit,
                    item_count=approved_n,
                    excluded_count=excluded_n,
                )
            )
        return out
    finally:
        conn.close()


@router.get("/projects/{project_uuid}/summary/by-category", response_model=list[SummaryRow])
def summary_by_category(project_uuid: str):
    conn = connect(readonly=True)
    try:
        proj = get_project_by_uuid(conn, project_uuid)
        if not proj:
            raise HTTPException(404, "project not found")
        project_id = proj["id"]
        rows = conn.execute(
            """
            SELECT o.*, c.category AS cat
            FROM occurrences o
            LEFT JOIN catalog_items c ON c.item_id = o.item_id
            WHERE o.project_id = ?
            """,
            (project_id,),
        ).fetchall()
        buckets: dict[str, dict] = {}
        for r in rows:
            cat = r["cat"] or "Unclassified"
            b = buckets.setdefault(
                cat, {"qty": 0.0, "unit": None, "item_count": 0, "excluded_count": 0}
            )
            st = r["status"] or "pending"
            if st == "excluded":
                b["excluded_count"] += 1
                continue
            if st in ("approved", "amended"):
                b["qty"] += effective_qty(r)
                b["item_count"] += 1
                b["unit"] = b["unit"] or r["unit"]
        return [
            SummaryRow(
                key=k,
                label=k,
                qty=round(v["qty"], 3),
                unit=v["unit"],
                item_count=v["item_count"],
                excluded_count=v["excluded_count"],
            )
            for k, v in sorted(buckets.items())
        ]
    finally:
        conn.close()
