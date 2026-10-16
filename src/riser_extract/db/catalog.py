"""Shared catalog seed + lookup."""

from __future__ import annotations

import sqlite3

from riser_extract.ids import CATALOGUE, ItemSpec


def _split_id(item_id: str) -> tuple[str, str]:
    parts = item_id.split("-", 2)
    discipline = parts[0] if parts else ""
    family = parts[1] if len(parts) > 1 else ""
    return discipline, family


def seed_catalog(conn: sqlite3.Connection, *, source: str = "seed") -> int:
    """Upsert all known catalogue rows. Returns number of item_ids touched."""
    n = 0
    for item_id, spec in CATALOGUE.items():
        upsert_catalog_item(conn, spec, source=source)
        n += 1
    conn.commit()
    return n


def upsert_catalog_item(
    conn: sqlite3.Connection,
    spec: ItemSpec,
    *,
    source: str = "seed",
    catalog_sku: str | None = None,
    material: str | None = None,
    rating: str | None = None,
    notes: str | None = None,
    description: str | None = None,
) -> None:
    discipline, family = _split_id(spec.item_id)
    sku = catalog_sku or f"SKU-{spec.item_id}"
    conn.execute(
        """
        INSERT INTO catalog_items (
            item_id, legacy_item_id, discipline, family, category, description,
            unit, scope_default, catalog_sku, material, rating, notes, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(item_id) DO UPDATE SET
            legacy_item_id = excluded.legacy_item_id,
            discipline = excluded.discipline,
            family = excluded.family,
            category = excluded.category,
            description = COALESCE(excluded.description, catalog_items.description),
            unit = excluded.unit,
            scope_default = excluded.scope_default,
            catalog_sku = COALESCE(excluded.catalog_sku, catalog_items.catalog_sku),
            material = COALESCE(excluded.material, catalog_items.material),
            rating = COALESCE(excluded.rating, catalog_items.rating),
            notes = COALESCE(excluded.notes, catalog_items.notes),
            source = excluded.source
        """,
        (
            spec.item_id,
            spec.legacy_item_id,
            discipline,
            family,
            spec.category,
            description or spec.category,
            spec.unit,
            spec.scope,
            sku,
            material,
            rating,
            notes,
            source,
        ),
    )


def ensure_item(conn: sqlite3.Connection, item_id: str | None) -> None:
    if not item_id:
        return
    spec = CATALOGUE.get(item_id)
    if spec:
        upsert_catalog_item(conn, spec)
        return
    # Unknown id — stub so FK succeeds
    discipline, family = _split_id(item_id)
    conn.execute(
        """
        INSERT INTO catalog_items (item_id, discipline, family, description, unit, source)
        VALUES (?, ?, ?, ?, 'no.', 'ingest')
        ON CONFLICT(item_id) DO NOTHING
        """,
        (item_id, discipline, family, item_id),
    )


def lookup(conn: sqlite3.Connection, item_id: str | None) -> sqlite3.Row | None:
    if not item_id:
        return None
    row = conn.execute(
        "SELECT * FROM catalog_items WHERE item_id = ?", (item_id,)
    ).fetchone()
    if row:
        return row
    return conn.execute(
        "SELECT * FROM catalog_items WHERE legacy_item_id = ?", (item_id,)
    ).fetchone()
