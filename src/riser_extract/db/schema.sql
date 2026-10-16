-- Riser GR-3 shared SQLite schema (DATA_DIR/getriser.sqlite)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    premise TEXT NOT NULL DEFAULT 'mep',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    drawing_number TEXT NOT NULL,
    floor_tab_name TEXT,
    source_pdf TEXT,
    content_hash TEXT,
    title_block_json TEXT,
    scale TEXT,
    revision TEXT,
    page_count INTEGER DEFAULT 1,
    extracted_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (project_id, drawing_number)
);

CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project_id);

CREATE TABLE IF NOT EXISTS catalog_items (
    item_id TEXT PRIMARY KEY,
    legacy_item_id TEXT,
    discipline TEXT,
    family TEXT,
    category TEXT,
    description TEXT,
    unit TEXT,
    scope_default TEXT DEFAULT 'in',
    catalog_sku TEXT,
    material TEXT,
    rating TEXT,
    notes TEXT,
    source TEXT DEFAULT 'seed'
);

CREATE INDEX IF NOT EXISTS idx_catalog_legacy ON catalog_items(legacy_item_id);

CREATE TABLE IF NOT EXISTS occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    item_id TEXT REFERENCES catalog_items(item_id),
    legacy_item_id TEXT,
    annotation TEXT,
    linked_to TEXT,
    qty REAL NOT NULL DEFAULT 1,
    unit TEXT NOT NULL DEFAULT 'no.',
    length_m REAL,
    size TEXT,
    measurement_type TEXT,
    scope TEXT DEFAULT 'in',
    pixel_bbox_json TEXT,
    real_world_json TEXT,
    centroid_json TEXT,
    symbol_class TEXT,
    confidence REAL,
    source TEXT,
    amber_flag INTEGER NOT NULL DEFAULT 0,
    occurrence_key TEXT NOT NULL,
    notes TEXT,
    UNIQUE (document_id, occurrence_key)
);

CREATE INDEX IF NOT EXISTS idx_occ_project_item ON occurrences(project_id, item_id);
CREATE INDEX IF NOT EXISTS idx_occ_document ON occurrences(document_id);

CREATE TABLE IF NOT EXISTS inventory_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL REFERENCES catalog_items(item_id),
    category TEXT,
    description TEXT,
    unit TEXT,
    qty_building REAL NOT NULL DEFAULT 0,
    scope TEXT,
    where_found TEXT,
    catalog_sku TEXT,
    catalog_status TEXT NOT NULL DEFAULT 'not_found',
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (project_id, item_id)
);

CREATE INDEX IF NOT EXISTS idx_inv_project ON inventory_lines(project_id);
