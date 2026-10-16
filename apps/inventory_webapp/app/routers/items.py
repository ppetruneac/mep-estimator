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
        # Category filter is applied in Python against excel_category (gold bands)
        extra, params = _filter_sql(
            status=status,
            measurement_type=measurement_type,
            scope=scope,
            item_id=item_id,
            category=None,
            q=q,
        )
        sql = f"""
            SELECT o.*
            FROM occurrences o
            LEFT JOIN catalog_items c ON c.item_id = o.item_id
            WHERE o.document_id = ?
            {extra}
            ORDER BY o.item_id, o.id
        """
        rows = conn.execute(sql, [doc["id"], *params]).fetchall()
        floor = doc["floor_tab_name"] if "floor_tab_name" in doc.keys() else None
        items = [ItemOut(**item_dict(conn, r, floor_tab_name=floor)) for r in rows]
        if category:
            items = [i for i in items if (i.category or "") == category]
        items.sort(key=lambda i: (i.category or "", i.item_id or "", i.id))
        return items
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
        # Facet chips use gold Excel section bands
        floor = doc["floor_tab_name"] if "floor_tab_name" in doc.keys() else None
        rows = conn.execute(
            "SELECT * FROM occurrences WHERE document_id = ?",
            (doc["id"],),
        ).fetchall()
        from collections import Counter

        cat_counts: Counter[str] = Counter()
        for r in rows:
            it = item_dict(conn, r, floor_tab_name=floor)
            cat_counts[it["category"] or "Unclassified"] += 1
        cats = [
            {"category": k, "count": v}
            for k, v in sorted(cat_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ]
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
        floor = None
        if row:
            d = conn.execute(
                "SELECT floor_tab_name FROM documents WHERE id = ?",
                (row["document_id"],),
            ).fetchone()
            floor = d["floor_tab_name"] if d else None
        return ItemOut(**item_dict(conn, row, floor_tab_name=floor))
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
        # Join catalog when category / search filters need it
        needs_join = bool(body.category or body.q)
        if needs_join:
            sql = """
                UPDATE occurrences
                SET status = ?, reviewed_at = ?
                WHERE id IN (
                  SELECT o.id
                  FROM occurrences o
                  LEFT JOIN catalog_items c ON c.item_id = o.item_id
                  WHERE o.document_id = ?
            """
            params: list = [new_status, now_iso(), doc["id"]]
        else:
            sql = "UPDATE occurrences SET status = ?, reviewed_at = ? WHERE document_id = ?"
            params = [new_status, now_iso(), doc["id"]]

        if body.only_pending:
            clause = (
                " AND COALESCE(o.status,'pending') = 'pending'"
                if needs_join
                else " AND COALESCE(status,'pending') = 'pending'"
            )
            sql += clause
        elif body.status:
            # Honour the status chip: only rewrite rows currently in that status
            if needs_join:
                sql += " AND COALESCE(o.status,'pending') = ?"
            else:
                sql += " AND COALESCE(status,'pending') = ?"
            params.append(body.status)
        else:
            # Flip any non-target status (pending ↔ excluded ↔ approved)
            if needs_join:
                sql += " AND COALESCE(o.status,'pending') != ?"
            else:
                sql += " AND COALESCE(status,'pending') != ?"
            params.append(new_status)

        if body.measurement_type:
            if needs_join:
                sql += " AND o.measurement_type = ?"
            else:
                sql += " AND measurement_type = ?"
            params.append(body.measurement_type)

        if body.category:
            if body.category == "Unclassified":
                sql += " AND (c.category IS NULL OR c.category = '')"
            else:
                sql += " AND c.category = ?"
                params.append(body.category)

        if body.q:
            like = f"%{body.q}%"
            sql += (
                " AND ("
                "o.annotation LIKE ? OR o.item_id LIKE ? OR o.notes LIKE ? OR "
                "o.linked_to LIKE ? OR c.category LIKE ? OR o.measurement_type LIKE ?"
                ")"
            )
            params.extend([like, like, like, like, like, like])

        if needs_join:
            sql += ")"

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
