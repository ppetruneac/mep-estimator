# Evals — Riser Phase 1

Track extractor performance against the Hubby Premier Inn London gold inventory.

## Dataset

`datasets/hubby-premier-inn-london/`

| File | Role |
|---|---|
| `manifest.json` | Paths, primary floors, gate thresholds |
| `expected/floors.json` | Parsed from `25280-SEN Heating and Cooling Inventory - All Floors - last.xlsx` |

Training PDFs live outside the repo (default `RISER_TRAINING_DIR` or the path in the manifest).

## Refresh gold

```bash
uv run python evals/scripts/parse_ground_truth.py
```

## Run

```bash
uv run riser-eval                 # all floors with PDFs; gates on Basement + Second Floor
uv run riser-eval --primary-only  # only primary floors
```

Writes:

- `evals/reports/YYYY-MM-DD-hubby.json`
- `evals/reports/YYYY-MM-DD-hubby.md`
- `evals/reports/latest.md` (committed)

## What is scored

| Metric | Gate (primary) |
|---|---|
| Title-block drawing number | exact |
| Scale `1:50` | exact |
| Floor tab name | exact |
| FCU / HB tag recall | ≥ 0.95 |
| Basement FCU / HBC counts | 10 / 1 |
| Second Floor FCU / HBC counts | 31 / 2 |
| Basement F+R **plan_m** median relative error | ≤ 15% |
| Basement tray plan_m relative error | ≤ 20% |

Second Floor tray / HBC→room lengths are **reported only** (gold used average-to-core geometry, not a traced spine).

Not scored: lagging, clips, OFN, thermostats, condensate allowances, First Floor (no PDF).

## Item IDs

Live IDs use trade prefixes (`MEC` / `ELEC` / `PLUM` / `VENT`). Each occurrence also carries `legacy_item_id` matching `skills/drawings-reader` (`HC-*` / `VT-*` / `PH-*`).
