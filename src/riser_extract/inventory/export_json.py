"""Export project inventory as JSON with nested occurrences."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from riser_extract.inventory.project_meta import backfill_project_parties


def export_json(conn: sqlite3.Connection, project_name: str, out_path: Path) -> Path:
    proj = conn.execute(
        "SELECT * FROM projects WHERE name = ?", (project_name,)
    ).fetchone()
    if not proj:
        raise ValueError(f"unknown project: {project_name}")
    pid = proj["id"]
    meta = backfill_project_parties(conn, pid)

    documents = []
    for d in conn.execute(
        "SELECT * FROM documents WHERE project_id = ? ORDER BY floor_tab_name",
        (pid,),
    ):
        occs = []
        for o in conn.execute(
            "SELECT * FROM occurrences WHERE document_id = ? ORDER BY id",
            (d["id"],),
        ):
            occs.append(
                {
                    "id": o["id"],
                    "item_id": o["item_id"],
                    "legacy_item_id": o["legacy_item_id"],
                    "annotation": o["annotation"],
                    "linked_to": o["linked_to"],
                    "qty": o["qty"],
                    "unit": o["unit"],
                    "length_m": o["length_m"],
                    "size": o["size"],
                    "measurement_type": o["measurement_type"],
                    "scope": o["scope"],
                    "pixel_bbox": json.loads(o["pixel_bbox_json"]) if o["pixel_bbox_json"] else None,
                    "real_world_coords": json.loads(o["real_world_json"]) if o["real_world_json"] else None,
                    "centroid_px": json.loads(o["centroid_json"]) if o["centroid_json"] else None,
                    "symbol_class": o["symbol_class"],
                    "confidence": o["confidence"],
                    "source": o["source"],
                    "amber_flag": bool(o["amber_flag"]),
                    "notes": o["notes"],
                }
            )
        # re-read after backfill
        tb_row = conn.execute(
            "SELECT title_block_json FROM documents WHERE id = ?", (d["id"],)
        ).fetchone()
        tb = json.loads(tb_row["title_block_json"]) if tb_row and tb_row["title_block_json"] else {}
        documents.append(
            {
                "drawing_number": d["drawing_number"],
                "floor_tab_name": d["floor_tab_name"],
                "source_pdf": d["source_pdf"],
                "scale": d["scale"],
                "revision": d["revision"],
                "title_block": tb,
                "occurrences": occs,
            }
        )

    items = []
    for line in conn.execute(
        """
        SELECT * FROM inventory_lines
        WHERE project_id = ?
        ORDER BY category, item_id
        """,
        (pid,),
    ):
        items.append(dict(line))

    payload = {
        "project": meta,
        "items": items,
        "documents": documents,
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path
