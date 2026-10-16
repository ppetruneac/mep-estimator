# Agent notes — mep-estimator / Riser extract

## Layout

| Path | Role |
|---|---|
| `skills/drawings-reader/` | Method docs (keep). Inventory model still uses legacy `HC-*` IDs |
| `skills/mep-estimator/` | Pricing method docs (keep) |
| `src/riser_extract/` | Phase 1–4 extract, symbols, SQLite inventory, lengths. See [README](src/riser_extract/README.md) |
| `apps/inventory_webapp/` | GR-6 inventory review webapp (FastAPI + React) |
| `evals/` | Gold parse + performance reports vs Hubby inventory |
| `docs/riser/` | Product / technical docs |

## Setup

```bash
uv venv .venv
uv pip install -e ".[dev]"
export DATA_DIR=/Users/pico/workspace/data/getriser
```

Recommended for reproducibility (once lockfile is committed):

```bash
uv lock
uv sync --dev
```

| Env | Default |
|---|---|
| `DATA_DIR` | `/Users/pico/workspace/data/getriser` |
| `RISER_DB_PATH` | `$DATA_DIR/getriser.sqlite` |
| `RISER_TRAINING_DIR` | `$DATA_DIR/training-docs/HeatingandCooling/HubbyPremierInnLondon` |
| `RISER_UI_PORT` | `8870` |
| `RISER_API_PORT` | `8871` |

SQLite uses **WAL + busy_timeout (30s)** so multiple ingest/API processes can open the same DB; writers serialize safely.

## Commands

```bash
# Extract one PDF or a folder (JSON + optional overlay)
uv run riser-extract path/to.pdf -o out/
uv run riser-extract "$RISER_TRAINING_DIR" -o out/

# Phase 2 symbols
uv run riser-symbols extract "$RISER_TRAINING_DIR" -o evals/evidence/gr2

# Phase 3 inventory (SQLite upsert by project name)
uv run riser-inventory seed-catalog
uv run riser-inventory ingest --project HubbyPremierInnLondon
uv run riser-inventory export --project HubbyPremierInnLondon -o out/hubby/
uv run riser-inventory compare --project HubbyPremierInnLondon

# GR-6 webapp (Make)
make help
make seed-hubby
make up          # Docker UI :8870 API :8871
make dev-api     # host API
make dev-ui      # host Vite

# Unit tests
uv run pytest
make test-webapp

# Gold eval
uv run riser-eval --primary-only
```

Pre-commit / pre-PR gate: `uv run pytest`, and for inventory/webapp work also `make test-webapp` + Hubby compare after ingest.

## Item IDs

Live extraction uses trade prefixes: `MEC` / `ELEC` / `PLUM` / `VENT`.

Each occurrence also has `legacy_item_id` (`HC-*` / `VT-*` / `PH-*`) matching `skills/drawings-reader/references/inventory-model.md`.

## Do not

- Remove or hollow out `skills/`
- Emit CSV in Phase 1 (JSON only)
- Apply tender conversion into `length_m` without Phase 4 helpers
- Invent First Floor tags (no PDF; gold is interpolated)
