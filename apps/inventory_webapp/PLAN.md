# Inventory Review Webapp — Plan

**Linear:** [GR-6](https://linear.app/dentaway/issue/GR-6/webapp-for-inventory-review-and-summary-from-sqlite-excel-take-off)

**Goal:** A webapp that lets an estimator select a project, review per-drawing inventory (approve / exclude / amend), view source PDFs (with overlays when available), and see summaries by floor or by category. No rates, labour or costs in this slice.

This is likely to become the app users log into.

## Tech recommendation

Inspired by the observability stack in [DentAway/dental-jobs](https://github.com/DentAway/dental-jobs) (`jobs/observability/`):

| Layer | Choice | Why |
|---|---|---|
| Backend API | **FastAPI** (Python) | Reuses `riser_extract`, matches the rest of the monorepo style (FastAPI + uvicorn), easy to call from workers |
| Frontend | **React** (Vite) + Tremor / similar | Same pattern as the observability UI; good for tables, filters, summaries; can grow into a proper logged-in product |
| Database | **SQLite** for local/MVP → **Postgres** for multi-user | SQLite is fine for single-user review; Postgres when multiple estimators + auth |
| Auth | Google Workspace / Clerk / Auth.js later | Technical-execution.md already points at Google Workspace for the beachhead |
| PDF / overlays | Serve via API + PDF.js or react-pdf | Overlay PDFs from `riser_extract` can be layered |

**Streamlit** (shipped in this PR) is only a fast prototype to validate the data model and review flow. It is not suitable as the long-term logged-in product.

## Scope (this PR — prototype)

- SQLite project + drawings + inventory items (seeded from the Hubby Excel or `floors.json`)
- Streamlit UI for:
  - Project picker
  - Drawing / floor picker
  - Inventory table with status (approved / excluded / amended) and editable fields
  - Summary views: by floor, by category
  - Placeholder PDF path
- Persistence of review decisions in SQLite
- Out of scope here: costs, labour, Drive sync, full overlay rendering, auth, multi-user

## Data model (SQLite)

```sql
CREATE TABLE projects (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  code TEXT,
  notes TEXT
);

CREATE TABLE drawings (
  id INTEGER PRIMARY KEY,
  project_id INTEGER REFERENCES projects(id),
  floor_tab_name TEXT,
  drawing_number TEXT,
  title TEXT,
  scale TEXT,
  source_pdf TEXT,          -- path or Drive id later
  overlay_pdf TEXT
);

CREATE TABLE inventory_items (
  id INTEGER PRIMARY KEY,
  drawing_id INTEGER REFERENCES drawings(id),
  line TEXT,                -- A01, B01, H1 ...
  category TEXT,
  annotation TEXT,
  linked_to TEXT,
  count REAL,
  unit TEXT,
  size TEXT,
  tender_estimate REAL,
  measurement_type TEXT,    -- printed / scaled / geometry / vertical / specified-not-drawn / excluded
  scope TEXT,               -- in / interface / out
  notes TEXT,
  status TEXT DEFAULT 'pending',  -- pending / approved / excluded / amended
  amended_count REAL,
  amended_notes TEXT,
  reviewed_at TEXT
);
```

## User flow

1. Open app → select project (Hubby Premier Inn Putney is seeded).
2. Sidebar: list of drawings / floors.
3. Main: inventory table for selected drawing. Approve / Exclude / amend count & notes.
4. Summary: by floor or by category (sum of approved tender quantities).
5. PDF: embed or link when `source_pdf` is set; overlay PDF side-by-side when present.

## Next steps (toward the logged-in app)

1. Replace Streamlit with FastAPI + React (observability-style).
2. Add auth (Google Workspace first).
3. Move to Postgres.
4. Wire real PDF paths / Drive file ids and render `riser_extract` overlays.
5. Export reviewed inventory back to Excel.
6. Join with the skill inventory model (`HC-*` item IDs).

## Run the prototype

```bash
uv pip install -r apps/inventory_webapp/requirements.txt
python apps/inventory_webapp/seed.py
streamlit run apps/inventory_webapp/app.py
```
