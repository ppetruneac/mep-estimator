from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.db import connect, now_iso
from app.models import BulkAction, ItemOut, ItemPatch
from app.services import item_dict

router = APIRouter(prefix="/api", tags=["items"])


@router.get("/drawings/{drawing_id}/items", response_model=list[ItemOut])
def list_items(
    drawing_id: int,
    status: str | None = None,
    measurement_type: str | None = None,
    scope: str | None = None,
    item_id: str | None = None,
    q: str | None = Query(None, description="Search annotation"),
):
    conn = connect(readonly=True)
    try:
        doc = conn.execute("SELECT id FROM documents WHERE id = ?", (drawing_id,)).fetchone()
        if not doc:
            raise HTTPException(404, "drawing not found")
        sql = "SELECT * FROM occurrences WHERE document_id = ?"
        params: list = [drawing_id]
        if status:
            sql += " AND COALESCE(status,'pending') = ?"
            params.append(status)
        if measurement_type:
            sql += " AND measurement_type = ?"
            params.append(measurement_type)
        if scope:
            sql += " AND scope = ?"
            params.append(scope)
        if item_id:
            sql += " AND item_id = ?"
            params.append(item_id)
        if q:
            sql += " AND annotation LIKE ?"
            params.append(f"%{q}%")
        sql += " ORDER BY item_id, id"
        rows = conn.execute(sql, params).fetchall()
        return [ItemOut(**item_dict(conn, r)) for r in rows]
    finally:
        conn.close()


@router.patch("/items/{item_id}", response_model=ItemOut)
def patch_item(item_id: int, body: ItemPatch):
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM occurrences WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(404, "item not found")
        status = body.status
        amended_qty = body.amended_qty
        amended_notes = body.amended_notes
        # If qty amended without status, mark amended
        if status is None and amended_qty is not None:
            status = "amended"
        fields = []
        vals: list = []
        if status is not None:
            fields.append("status = ?")
            vals.append(status)
        if amended_qty is not None:
            fields.append("amended_qty = ?")
            vals.append(amended_qty)
        if amended_notes is not None:
            fields.append("amended_notes = ?")
            vals.append(amended_notes)
        if not fields:
            raise HTTPException(400, "no changes")
        fields.append("reviewed_at = ?")
        vals.append(now_iso())
        vals.append(item_id)
        conn.execute(
            f"UPDATE occurrences SET {', '.join(fields)} WHERE id = ?",
            vals,
        )
        conn.commit()
        row = conn.execute("SELECT * FROM occurrences WHERE id = ?", (item_id,)).fetchone()
        return ItemOut(**item_dict(conn, row))
    finally:
        conn.close()


@router.post("/drawings/{drawing_id}/items/bulk")
def bulk_items(drawing_id: int, body: BulkAction):
    conn = connect()
    try:
        doc = conn.execute("SELECT id FROM documents WHERE id = ?", (drawing_id,)).fetchone()
        if not doc:
            raise HTTPException(404, "drawing not found")
        new_status = "approved" if body.action == "approve" else "excluded"
        sql = "UPDATE occurrences SET status = ?, reviewed_at = ? WHERE document_id = ?"
        params: list = [new_status, now_iso(), drawing_id]
        if body.only_pending:
            sql += " AND COALESCE(status,'pending') = 'pending'"
        cur = conn.execute(sql, params)
        conn.commit()
        return {"updated": cur.rowcount, "status": new_status}
    finally:
        conn.close()
