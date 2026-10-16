# Agent notes — mep-estimator / Riser extract

## Layout

| Path | Role |
|---|---|
| `skills/drawings-reader/` | Method docs (keep). Inventory model still uses legacy `HC-*` IDs |
| `skills/mep-estimator/` | Pricing method docs (keep) |
| `src/riser_extract/` | Phase 1–3 extract, symbols, SQLite inventory |
| `evals/` | Gold parse + performance reports vs Hubby inventory |
| `docs/riser/` | Product / technical docs |

## Setup

```bash
uv venv .venv
uv pip install -e ".[dev]"
export DATA_DIR=/Users/pico/workspace/data/getriser
```

| Env | Default |
|---|---|
| `DATA_DIR` | `/Users/pico/workspace/data/getriser` |
| `RISER_DB_PATH` | `$DATA_DIR/getriser.sqlite` |
| `RISER_TRAINING_DIR` | `$DATA_DIR/training-docs/HeatingandCooling/HubbyPremierInnLondon` |

SQLite uses **WAL + busy_timeout (30s)** so multiple ingest processes can open the same DB; writers serialize safely.

## Commands

```bash
# Extract one PDF or a folder (JSON + optional overlay)
uv run riser-extract path/to.pdf -o out/
uv run riser-extract "$RISER_TRAINING_DIR" -o out/

# Phase 2 symbols: annotated PNG/PDF + JSON
uv run riser-symbols extract "$RISER_TRAINING_DIR" -o evals/evidence/gr2

# Phase 3 inventory (SQLite upsert by project name)
uv run riser-inventory seed-catalog
uv run riser-inventory ingest --project HubbyPremierInnLondon
uv run riser-inventory ingest --project HubbyPremierInnLondon   # second run upserts / skips unchanged
uv run riser-inventory export --project HubbyPremierInnLondon -o out/hubby/
uv run riser-inventory compare --project HubbyPremierInnLondon

# Unit tests
uv run pytest

# Gold eval (primary floors gated; includes Phase 2 symbol counts)
uv run riser-eval --primary-only
uv run riser-eval
```

Pre-commit / pre-PR gate: `uv run pytest`, and for inventory work also `uv run riser-inventory compare --project HubbyPremierInnLondon` after ingest.

## Item IDs

Live extraction uses trade prefixes: `MEC` / `ELEC` / `PLUM` / `VENT`.

Each occurrence also has `legacy_item_id` (`HC-*` / `VT-*` / `PH-*`) matching `skills/drawings-reader/references/inventory-model.md`.

## Do not

- Remove or hollow out `skills/`
- Emit CSV in Phase 1 (JSON only)
- Apply tender conversion (×2 × 1.15 + tails) into `length_m` — that is Phase 4
- Invent First Floor tags (no PDF; gold is interpolated)
