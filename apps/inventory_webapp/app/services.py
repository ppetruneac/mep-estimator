"""Shared query helpers."""

from __future__ import annotations

import json
import sqlite3


def effective_qty(row: sqlite3.Row | dict) -> float:
    d = dict(row)
    if d.get("amended_qty") is not None:
        return float(d["amended_qty"])
    if d.get("unit") == "m" and d.get("length_m") is not None:
        return float(d["length_m"])
    return float(d.get("qty") or 0)


def item_dict(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    d = dict(row)
    d["amber_flag"] = bool(d.get("amber_flag"))
    d["status"] = d.get("status") or "pending"
    d["effective_qty"] = effective_qty(d)
    cat = None
    if d.get("item_id"):
        r = conn.execute(
            "SELECT category FROM catalog_items WHERE item_id = ?",
            (d["item_id"],),
        ).fetchone()
        cat = r["category"] if r else None
    d["category"] = cat
    # drop heavy unused
    for k in ("pixel_bbox_json", "real_world_json", "centroid_json", "occurrence_key"):
        d.pop(k, None)
    return d


def parse_bbox(row: sqlite3.Row) -> list[float] | None:
    raw = row["pixel_bbox_json"] if "pixel_bbox_json" in row.keys() else None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
