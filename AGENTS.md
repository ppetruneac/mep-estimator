# Agent notes — mep-estimator / Riser extract

## Layout

| Path | Role |
|---|---|
| `skills/drawings-reader/` | Method docs (keep). Inventory model still uses legacy `HC-*` IDs |
| `skills/mep-estimator/` | Pricing method docs (keep) |
| `src/riser_extract/` | Phase 1 deterministic PDF extractor |
| `evals/` | Gold parse + performance reports vs Hubby inventory |
| `docs/riser/` | Product / technical docs |

## Setup

```bash
uv venv .venv
uv pip install -e ".[dev]"
```

Training PDFs + gold xlsx (not in git):

`/Users/pico/workspace/data/getriser/training-docs/HeatingandCooling/HubbyPremierInnLondon`

Override with `RISER_TRAINING_DIR`.

## Commands

```bash
# Extract one PDF or a folder (JSON + optional overlay)
uv run riser-extract path/to.pdf -o out/
uv run riser-extract "$RISER_TRAINING_DIR" -o out/

# Unit tests
uv run pytest

# Gold eval (primary floors gated)
uv run riser-eval --primary-only
uv run riser-eval
```

Pre-commit / pre-PR gate for extractor work: `uv run pytest` and `uv run riser-eval --primary-only`.

## Item IDs

Live extraction uses trade prefixes: `MEC` / `ELEC` / `PLUM` / `VENT`.

Each occurrence also has `legacy_item_id` (`HC-*` / `VT-*` / `PH-*`) matching `skills/drawings-reader/references/inventory-model.md`.

## Do not

- Remove or hollow out `skills/`
- Emit CSV in Phase 1 (JSON only)
- Apply tender conversion (×2 × 1.15 + tails) into `length_m` — that is Phase 4
- Invent First Floor tags (no PDF; gold is interpolated)
