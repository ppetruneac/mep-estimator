"""Rebuild project-level inventory_lines from occurrences."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from riser_extract.db.catalog import lookup
from riser_extract.ids import CATALOGUE


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def rebuild_inventory_lines(conn: sqlite3.Connection, project_id: int) -> int:
    """Aggregate occurrences → inventory_lines with catalog status + where_found."""
    conn.execute("BEGIN IMMEDIATE")
    conn.execute("DELETE FROM inventory_lines WHERE project_id = ?", (project_id,))

    # Per item_id totals
    rows = conn.execute(
        """
        SELECT
            o.item_id,
            o.unit,
            o.scope,
            SUM(
                CASE
                    WHEN o.unit = 'm' THEN COALESCE(o.length_m, o.qty, 0)
                    ELSE o.qty
                END
            ) AS qty_building
        FROM occurrences o
        WHERE o.project_id = ? AND o.item_id IS NOT NULL
        GROUP BY o.item_id, o.unit, o.scope
        """,
        (project_id,),
    ).fetchall()

    # where_found per item
    where_rows = conn.execute(
        """
        SELECT o.item_id, d.floor_tab_name, d.drawing_number,
               SUM(
                   CASE
                       WHEN o.unit = 'm' THEN COALESCE(o.length_m, o.qty, 0)
                       ELSE o.qty
                   END
               ) AS q
        FROM occurrences o
        JOIN documents d ON d.id = o.document_id
        WHERE o.project_id = ? AND o.item_id IS NOT NULL
        GROUP BY o.item_id, d.floor_tab_name, d.drawing_number
        HAVING q > 0
        ORDER BY d.floor_tab_name
        """,
        (project_id,),
    ).fetchall()
    where_map: dict[str, list[str]] = {}
    for r in where_rows:
        floor = r["floor_tab_name"] or "?"
        dwg = r["drawing_number"] or "?"
        where_map.setdefault(r["item_id"], []).append(f"{floor} ({dwg})")

    n = 0
    for r in rows:
        item_id = r["item_id"]
        cat = lookup(conn, item_id)
        spec = CATALOGUE.get(item_id)
        category = (cat["category"] if cat else None) or (spec.category if spec else None)
        description = (cat["description"] if cat else None) or (spec.category if spec else item_id)
        unit = r["unit"] or (cat["unit"] if cat else "no.")
        scope = r["scope"] or (cat["scope_default"] if cat else "in")
        qty = float(r["qty_building"] or 0)
        # Exclusions: keep row but zero building qty for priced rollups
        if scope == "out":
            qty_building = 0.0
        else:
            qty_building = qty
        sku = cat["catalog_sku"] if cat else None
        status = "matched" if cat and cat["catalog_sku"] else ("matched" if cat else "not_found")
        if cat:
            status = "matched"
        where_found = "; ".join(where_map.get(item_id, []))
        conn.execute(
            """
            INSERT INTO inventory_lines (
                project_id, item_id, category, description, unit, qty_building,
                scope, where_found, catalog_sku, catalog_status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                item_id,
                category,
                description,
                unit,
                qty_building,
                scope,
                where_found,
                sku,
                status,
                _now(),
            ),
        )
        n += 1

    conn.execute(
        "UPDATE projects SET updated_at = ? WHERE id = ?",
        (_now(), project_id),
    )
    conn.commit()
    return n
