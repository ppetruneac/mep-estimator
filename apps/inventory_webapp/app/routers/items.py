from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.db import connect, now_iso
from app.labels import MEASUREMENT_TYPE_HELP
from app.models import BulkAction, CategoryFacet, DrawingFacets, ItemOut, ItemPatch
from app.services import item_dict, resolve_drawing

router = APIRouter(prefix="/api", tags=["items"])


def _filter_sql(
    *,
    status: str | None,
    measurement_type: str | None,
    scope: str | None,
    item_id: str | None,
    category: str | None,
    q: str | None,
) -> tuple[str, list]:
    sql = ""
    params: list = []
    if status:
        sql += " AND COALESCE(o.status,'pending') = ?"
        params.append(status)
    if measurement_type:
        sql += " AND o.measurement_type = ?"
        params.append(measurement_type)
    if scope:
        sql += " AND o.scope = ?"
        params.append(scope)
    if item_id:
        sql += " AND o.item_id = ?"
        params.append(item_id)
    if category:
        if category == "Unclassified":
            sql += " AND (c.category IS NULL OR c.category = '')"
        else:
            sql += " AND c.category = ?"
            params.append(category)
    if q:
        like = f"%{q}%"
        sql += (
            " AND ("
            "o.annotation LIKE ? OR o.item_id LIKE ? OR o.notes LIKE ? OR "
            "o.linked_to LIKE ? OR c.category LIKE ? OR o.measurement_type LIKE ?"
            ")"
        )
        params.extend([like, like, like, like, like, like])
    return sql, params


@router.get(
    "/projects/{project_uuid}/drawings/{drawing_key}/items",
    response_model=list[ItemOut],
)
def list_items_by_key(
    project_uuid: str,
    drawing_key: str,
    status: str | None = None,
    measurement_type: str | None = None,
    scope: str | None = None,
    item_id: str | None = None,
    category: str | None = None,
    q: str | None = Query(None, description="Full-text search"),
):
    conn = connect(readonly=True)
    try:
        doc = resolve_drawing(conn, project_uuid, drawing_key)
        if not doc:
            raise HTTPException(404, "drawing not found")
        extra, params = _filter_sql(
            status=status,
            measurement_type=measurement_type,
            scope=scope,
            item_id=item_id,
            category=category,
            q=q,
        )
        sql = f"""
            SELECT o.*
            FROM occurrences o
            LEFT JOIN catalog_items c ON c.item_id = o.item_id
            WHERE o.document_id = ?
            {extra}
            ORDER BY COALESCE(c.category, 'Unclassified'), o.item_id, o.id
        """
        rows = conn.execute(sql, [doc["id"], *params]).fetchall()
        return [ItemOut(**item_dict(conn, r)) for r in rows]
    finally:
        conn.close()


@router.get(
    "/projects/{project_uuid}/drawings/{drawing_key}/facets",
    response_model=DrawingFacets,
)
def drawing_facets(project_uuid: str, drawing_key: str):
    """Category / status / type chips with counts (observability-style)."""
    conn = connect(readonly=True)
    try:
        doc = resolve_drawing(conn, project_uuid, drawing_key)
        if not doc:
            raise HTTPException(404, "drawing not found")
        cats = conn.execute(
            """
            SELECT COALESCE(c.category, 'Unclassified') AS category, COUNT(*) AS count
            FROM occurrences o
            LEFT JOIN catalog_items c ON c.item_id = o.item_id
            WHERE o.document_id = ?
            GROUP BY 1
            ORDER BY count DESC, category
            """,
            (doc["id"],),
        ).fetchall()
        statuses = conn.execute(
            """
            SELECT COALESCE(status, 'pending') AS key, COUNT(*) AS count
            FROM occurrences WHERE document_id = ?
            GROUP BY 1 ORDER BY count DESC
            """,
            (doc["id"],),
        ).fetchall()
        types = conn.execute(
            """
            SELECT COALESCE(measurement_type, '(none)') AS key, COUNT(*) AS count
            FROM occurrences WHERE document_id = ?
            GROUP BY 1 ORDER BY count DESC
            """,
            (doc["id"],),
        ).fetchall()
        return DrawingFacets(
            categories=[CategoryFacet(category=r["category"], count=r["count"]) for r in cats],
            statuses=[
                {"key": r["key"], "count": r["count"], "help": None} for r in statuses
            ],
            measurement_types=[
                {
                    "key": r["key"],
                    "count": r["count"],
                    "help": MEASUREMENT_TYPE_HELP.get(r["key"]),
                }
                for r in types
            ],
        )
    finally:
        conn.close()


# Legacy numeric routes kept for PDF helpers / older clients
@router.get("/drawings/{drawing_id}/items", response_model=list[ItemOut])
def list_items_legacy(
    drawing_id: int,
    status: str | None = None,
    measurement_type: str | None = None,
    scope: str | None = None,
    item_id: str | None = None,
    category: str | None = None,
    q: str | None = None,
):
    conn = connect(readonly=True)
    try:
        doc = conn.execute(
            "SELECT d.*, p.uuid AS project_uuid FROM documents d JOIN projects p ON p.id=d.project_id WHERE d.id=?",
            (drawing_id,),
        ).fetchone()
        if not doc:
            raise HTTPException(404, "drawing not found")
        return list_items_by_key(
            doc["project_uuid"],
            doc["drawing_number"],
            status=status,
            measurement_type=measurement_type,
            scope=scope,
            item_id=item_id,
            category=category,
            q=q,
        )
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


@router.post("/projects/{project_uuid}/drawings/{drawing_key}/items/bulk")
def bulk_items_by_key(project_uuid: str, drawing_key: str, body: BulkAction):
    conn = connect()
    try:
        doc = resolve_drawing(conn, project_uuid, drawing_key)
        if not doc:
            raise HTTPException(404, "drawing not found")
        new_status = "approved" if body.action == "approve" else "excluded"
        sql = "UPDATE occurrences SET status = ?, reviewed_at = ? WHERE document_id = ?"
        params: list = [new_status, now_iso(), doc["id"]]
        if body.only_pending:
            sql += " AND COALESCE(status,'pending') = 'pending'"
        cur = conn.execute(sql, params)
        conn.commit()
        return {"updated": cur.rowcount, "status": new_status}
    finally:
        conn.close()


@router.post("/drawings/{drawing_id}/items/bulk")
def bulk_items_legacy(drawing_id: int, body: BulkAction):
    conn = connect()
    try:
        doc = conn.execute(
            "SELECT d.*, p.uuid AS project_uuid FROM documents d JOIN projects p ON p.id=d.project_id WHERE d.id=?",
            (drawing_id,),
        ).fetchone()
        if not doc:
            raise HTTPException(404, "drawing not found")
        return bulk_items_by_key(doc["project_uuid"], doc["drawing_number"], body)
    finally:
        conn.close()
