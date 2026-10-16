"""Project / document / occurrence upserts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from riser_extract.db.aggregate import rebuild_inventory_lines
from riser_extract.db.catalog import ensure_item
from riser_extract.pipeline import extract_drawing
from riser_extract.schema import ExtractionResult, Occurrence


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_projects_uuid_column(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()}
    if "uuid" not in cols:
        conn.execute("ALTER TABLE projects ADD COLUMN uuid TEXT")
    # Backfill any rows missing uuid
    for row in conn.execute(
        "SELECT id FROM projects WHERE uuid IS NULL OR uuid = ''"
    ).fetchall():
        conn.execute(
            "UPDATE projects SET uuid = ? WHERE id = ?",
            (str(uuid.uuid4()), row[0] if not hasattr(row, "keys") else row["id"]),
        )
    # Unique index (ignore if exists)
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_uuid ON projects(uuid)"
    )


def ensure_project(conn: sqlite3.Connection, name: str, *, premise: str = "mep") -> int:
    conn.execute("BEGIN IMMEDIATE")
    _ensure_projects_uuid_column(conn)
    row = conn.execute("SELECT id, uuid FROM projects WHERE name = ?", (name,)).fetchone()
    if row:
        pid = int(row["id"] if hasattr(row, "keys") else row[0])
        existing_uuid = row["uuid"] if hasattr(row, "keys") else row[1]
        if not existing_uuid:
            conn.execute(
                "UPDATE projects SET uuid = ?, updated_at = ?, premise = COALESCE(?, premise) WHERE id = ?",
                (str(uuid.uuid4()), _now(), premise, pid),
            )
        else:
            conn.execute(
                "UPDATE projects SET updated_at = ?, premise = COALESCE(?, premise) WHERE id = ?",
                (_now(), premise, pid),
            )
        conn.commit()
        return pid
    cur = conn.execute(
        "INSERT INTO projects (uuid, name, premise, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), name, premise, _now(), _now()),
    )
    conn.commit()
    return int(cur.lastrowid)


def occurrence_key(occ: Occurrence, seq: int) -> str:
    cx = cy = ""
    if occ.centroid_px and len(occ.centroid_px) >= 2:
        cx, cy = str(round(occ.centroid_px[0])), str(round(occ.centroid_px[1]))
    elif occ.pixel_bbox and len(occ.pixel_bbox) >= 4:
        cx = str(round(0.5 * (occ.pixel_bbox[0] + occ.pixel_bbox[2])))
        cy = str(round(0.5 * (occ.pixel_bbox[1] + occ.pixel_bbox[3])))
    parts = [
        occ.item_id or "_",
        (occ.annotation or "")[:80],
        str(occ.page),
        cx,
        cy,
        str(occ.measurement_type.value if hasattr(occ.measurement_type, "value") else occ.measurement_type),
        str(seq),
    ]
    return "|".join(parts)


def upsert_document(
    conn: sqlite3.Connection,
    *,
    project_id: int,
    result: ExtractionResult,
    pdf_path: Path,
    content_hash: str,
) -> int:
    tb = result.title_block
    drawing_number = tb.drawing_number or pdf_path.stem
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        """
        INSERT INTO documents (
            project_id, drawing_number, floor_tab_name, source_pdf, content_hash,
            title_block_json, scale, revision, page_count, extracted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        ON CONFLICT(project_id, drawing_number) DO UPDATE SET
            floor_tab_name = excluded.floor_tab_name,
            source_pdf = excluded.source_pdf,
            content_hash = excluded.content_hash,
            title_block_json = excluded.title_block_json,
            scale = excluded.scale,
            revision = excluded.revision,
            page_count = excluded.page_count,
            extracted_at = excluded.extracted_at
        """,
        (
            project_id,
            drawing_number,
            tb.floor_tab_name,
            str(pdf_path),
            content_hash,
            json.dumps(tb.model_dump()),
            tb.scale,
            tb.revision,
            _now(),
        ),
    )
    row = conn.execute(
        "SELECT id FROM documents WHERE project_id = ? AND drawing_number = ?",
        (project_id, drawing_number),
    ).fetchone()
    conn.commit()
    return int(row["id"])


def replace_occurrences(
    conn: sqlite3.Connection,
    *,
    project_id: int,
    document_id: int,
    result: ExtractionResult,
) -> int:
    """Delete prior rows for this drawing and insert the fresh extract set."""
    conn.execute("BEGIN IMMEDIATE")
    conn.execute("DELETE FROM occurrences WHERE document_id = ?", (document_id,))

    # Prefer symbol-enriched discrete equipment; also keep length/pipe occurrences
    rows_src: list[Occurrence] = list(result.occurrences)

    # Ensure catalog rows exist
    for occ in rows_src:
        ensure_item(conn, occ.item_id)

    n = 0
    for seq, occ in enumerate(rows_src):
        key = occurrence_key(occ, seq)
        bbox = json.dumps(occ.pixel_bbox) if occ.pixel_bbox else None
        rw = json.dumps(occ.real_world_coords) if occ.real_world_coords else None
        cent = json.dumps(occ.centroid_px) if occ.centroid_px else None
        mt = occ.measurement_type.value if hasattr(occ.measurement_type, "value") else occ.measurement_type
        sc = occ.scope.value if hasattr(occ.scope, "value") else occ.scope
        conn.execute(
            """
            INSERT INTO occurrences (
                project_id, document_id, item_id, legacy_item_id, annotation, linked_to,
                qty, unit, length_m, size, measurement_type, scope,
                pixel_bbox_json, real_world_json, centroid_json,
                symbol_class, confidence, source, amber_flag, occurrence_key, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                document_id,
                occ.item_id,
                occ.legacy_item_id,
                occ.annotation,
                occ.linked_to,
                float(occ.count),
                occ.unit,
                occ.length_m,
                occ.size,
                mt,
                sc,
                bbox,
                rw,
                cent,
                occ.symbol_class,
                occ.confidence,
                occ.source,
                1 if occ.amber_flag else 0,
                key,
                occ.notes,
            ),
        )
        n += 1
    conn.commit()
    return n


def ingest_pdf(
    conn: sqlite3.Connection,
    *,
    project_name: str,
    pdf_path: Path,
    premise: str = "mep",
    force: bool = False,
) -> dict:
    pdf_path = pdf_path.resolve()
    project_id = ensure_project(conn, project_name, premise=premise)
    digest = _sha256(pdf_path)

    existing = conn.execute(
        """
        SELECT d.id, d.content_hash, d.drawing_number, d.floor_tab_name
        FROM documents d
        WHERE d.project_id = ? AND d.source_pdf = ?
        """,
        (project_id, str(pdf_path)),
    ).fetchone()

    if not force and existing and existing["content_hash"] == digest:
        n_occ = conn.execute(
            "SELECT COUNT(*) AS n FROM occurrences WHERE document_id = ?",
            (existing["id"],),
        ).fetchone()["n"]
        rebuild_inventory_lines(conn, project_id)
        return {
            "project": project_name,
            "project_id": project_id,
            "document_id": int(existing["id"]),
            "drawing_number": existing["drawing_number"],
            "floor_tab_name": existing["floor_tab_name"],
            "occurrences": n_occ,
            "skipped_unchanged": True,
            "n_symbols": None,
        }

    result = extract_drawing(pdf_path)
    drawing_number = result.title_block.drawing_number or pdf_path.stem
    document_id = upsert_document(
        conn,
        project_id=project_id,
        result=result,
        pdf_path=pdf_path,
        content_hash=digest,
    )
    n_occ = replace_occurrences(
        conn, project_id=project_id, document_id=document_id, result=result
    )
    rebuild_inventory_lines(conn, project_id)

    return {
        "project": project_name,
        "project_id": project_id,
        "document_id": document_id,
        "drawing_number": drawing_number,
        "floor_tab_name": result.title_block.floor_tab_name,
        "occurrences": n_occ,
        "skipped_unchanged": False,
        "n_symbols": len(result.symbols),
    }


def ingest_path(
    conn: sqlite3.Connection,
    *,
    project_name: str,
    path: Path,
    premise: str = "mep",
    force: bool = False,
) -> list[dict]:
    path = path.resolve()
    pdfs = [path] if path.is_file() else sorted(path.glob("*.pdf"))
    out = []
    for pdf in pdfs:
        out.append(
            ingest_pdf(
                conn,
                project_name=project_name,
                pdf_path=pdf,
                premise=premise,
                force=force,
            )
        )
    return out
