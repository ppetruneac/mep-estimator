"""Catalogue API — category (Excel band) + item_id / SKU mappings."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Query

from app.db import connect
from app.labels import item_label
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["catalogue"])


class CatalogueItem(BaseModel):
    item_id: str
    legacy_item_id: str | None = None
    category: str
    description: str | None = None
    item_label: str | None = None
    unit: str | None = None
    scope_default: str | None = None
    catalog_sku: str | None = None
    source: str | None = None


class CatalogueFacet(BaseModel):
    category: str
    count: int


class CatalogueResponse(BaseModel):
    items: list[CatalogueItem]
    categories: list[CatalogueFacet]


@router.get("/catalogue", response_model=CatalogueResponse)
def list_catalogue(
    category: str | None = None,
    q: str | None = Query(None, description="Search item_id, SKU, description"),
):
    conn = connect(readonly=True)
    try:
        rows = conn.execute(
            """
            SELECT item_id, legacy_item_id, category, description, unit,
                   scope_default, catalog_sku, source
            FROM catalog_items
            ORDER BY category, item_id
            """
        ).fetchall()
        items = []
        for r in rows:
            d = dict(r)
            d["item_label"] = item_label(d.get("item_id")) or d.get("description")
            items.append(CatalogueItem(**d))

        cat_counts = Counter(i.category or "Unclassified" for i in items)
        categories = [
            CatalogueFacet(category=k, count=v)
            for k, v in sorted(cat_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ]

        if category:
            items = [i for i in items if i.category == category]
        if q:
            ql = q.lower()
            items = [
                i
                for i in items
                if ql in (i.item_id or "").lower()
                or ql in (i.catalog_sku or "").lower()
                or ql in (i.description or "").lower()
                or ql in (i.item_label or "").lower()
                or ql in (i.legacy_item_id or "").lower()
                or ql in (i.category or "").lower()
            ]

        return CatalogueResponse(items=items, categories=categories)
    finally:
        conn.close()
