"""Shared query helpers."""

from __future__ import annotations

import json
import sqlite3

from app.excel_bands import excel_category
from app.labels import MEASUREMENT_TYPE_HELP, item_label


def effective_qty(row: sqlite3.Row | dict) -> float:
    d = dict(row)
    if d.get("amended_qty") is not None:
        return float(d["amended_qty"])
    if d.get("unit") == "m" and d.get("length_m") is not None:
        return float(d["length_m"])
    return float(d.get("qty") or 0)


def item_dict(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    floor_tab_name: str | None = None,
) -> dict:
    d = dict(row)
    d["amber_flag"] = bool(d.get("amber_flag"))
    d["status"] = d.get("status") or "pending"
    d["effective_qty"] = effective_qty(d)
    catalog_cat = None
    catalog_desc = None
    if d.get("item_id"):
        r = conn.execute(
            "SELECT category, description FROM catalog_items WHERE item_id = ?",
            (d["item_id"],),
        ).fetchone()
        if r:
            catalog_cat = r["category"]
            catalog_desc = r["description"]
    # Category = Excel take-off band (A–G…). Catalogue = item_id + SKU mapping.
    d["excel_category"] = excel_category(
        floor_tab_name=floor_tab_name,
        item_id=d.get("item_id"),
        annotation=d.get("annotation"),
        symbol_class=d.get("symbol_class"),
    )
    d["category"] = d["excel_category"]
    d["catalog_category"] = catalog_cat  # catalogue taxonomy family (internal / SKU join)
    d["item_label"] = item_label(d.get("item_id")) or catalog_desc
    mt = d.get("measurement_type")
    d["measurement_type_help"] = MEASUREMENT_TYPE_HELP.get(mt or "", None)
    for k in ("pixel_bbox_json", "real_world_json", "centroid_json", "occurrence_key"):
        d.pop(k, None)
    return d


def resolve_drawing(
    conn: sqlite3.Connection, project_uuid: str, drawing_key: str
) -> sqlite3.Row | None:
    """Resolve drawing by drawing_number within a project; fall back to numeric id."""
    proj = conn.execute(
        "SELECT id FROM projects WHERE uuid = ?", (project_uuid,)
    ).fetchone()
    if not proj:
        return None
    row = conn.execute(
        """
        SELECT d.*, p.uuid AS project_uuid
        FROM documents d
        JOIN projects p ON p.id = d.project_id
        WHERE d.project_id = ? AND d.drawing_number = ?
        """,
        (proj["id"], drawing_key),
    ).fetchone()
    if row:
        return row
    # uniqueness fallback: number-id
    if drawing_key.isdigit():
        return conn.execute(
            """
            SELECT d.*, p.uuid AS project_uuid
            FROM documents d
            JOIN projects p ON p.id = d.project_id
            WHERE d.project_id = ? AND d.id = ?
            """,
            (proj["id"], int(drawing_key)),
        ).fetchone()
    # if not unique by number alone, try suffix "-{id}"
    if "-" in drawing_key:
        base, _, maybe_id = drawing_key.rpartition("-")
        if maybe_id.isdigit():
            return conn.execute(
                """
                SELECT d.*, p.uuid AS project_uuid
                FROM documents d
                JOIN projects p ON p.id = d.project_id
                WHERE d.project_id = ? AND d.drawing_number = ? AND d.id = ?
                """,
                (proj["id"], base, int(maybe_id)),
            ).fetchone()
    return None


def parse_bbox(row: sqlite3.Row) -> list[float] | None:
    raw = row["pixel_bbox_json"] if "pixel_bbox_json" in row.keys() else None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
