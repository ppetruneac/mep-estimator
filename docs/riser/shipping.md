# What’s shipping — Riser extract (GR-1 + GR-2 + GR-3)

Hosted method package: `riser_extract` in this repo. Skills under `skills/` stay as the human method docs.

## In this stack

| Ticket | PR | Ships |
|---|---|---|
| [GR-1](https://linear.app/dentaway/issue/GR-1/phase-1-deterministic-geometry-and-text-extraction-core) | [#1](https://github.com/ppetruneac/mep-estimator/pull/1) | Deterministic PDF geometry + text extraction → JSON |
| [GR-2](https://linear.app/dentaway/issue/GR-2/phase-2-symbol-identification-rules-first-yolo-optional) | [#2](https://github.com/ppetruneac/mep-estimator/pull/2) (stacked on #1) | Rules-first symbol ID, annotated sheets, eval gates, optional YOLO residual |
| [GR-3](https://linear.app/dentaway/issue/GR-3/phase-3-stable-inventory-model-shared-catalog-lookup) | stacked | SQLite inventory + catalog lookup + Excel/JSON export |

## Data directory

```bash
export DATA_DIR=/Users/pico/workspace/data/getriser
# DB file: $DATA_DIR/getriser.sqlite  (WAL mode; busy_timeout for concurrent writers)
```

See `.env.example`. The SQLite file is **outside git**.

## Install

```bash
uv venv .venv && uv pip install -e ".[dev]"
# optional residual detector:
uv pip install -e ".[yolo]"
```

## CLIs

| Command | What it does |
|---|---|
| `riser-extract <pdf\|dir> -o out/` | Phase 1+2: JSON per drawing + overlay PDF + annotated PNG |
| `riser-eval [--primary-only]` | Gold eval vs Hubby inventory (title/scale/tags/lengths + symbol counts) |
| `riser-symbols extract …` | Same extract path, evidence-oriented output layout |
| `riser-symbols dataset …` | Export YOLO weak-label dataset from rule proposals |
| `riser-symbols train …` | Optional YOLO11 fine-tune (Apple MPS when available) |
| `riser-symbols decision-log …` | Write rules-vs-YOLO decision artifact |
| `riser-inventory seed-catalog` | Upsert shared `catalog_items` |
| `riser-inventory ingest --project HubbyPremierInnLondon [dir]` | Extract + upsert into `getriser.sqlite` |
| `riser-inventory export --project … -o out/` | `inventory.json` + gold-shaped `inventory.xlsx` |
| `riser-inventory compare --project …` | Primary count gates vs Hubby gold |

## Phase 1 — geometry & text (JSON)

Per drawing: `inventory_json/{drawing-number}.json`

- Title block: drawing number, floor tab name, scale (`1:50`), rotation, Measure dict, CAD layers
- Occurrences: tags, provisional trade `item_id` (`MEC` / `ELEC` / `PLUM` / `VENT`) + `legacy_item_id` (`HC-*` / `VT-*` / `PH-*`)
- Path lengths in **plan metres** (no tender ×2 ×1.15 + tails — that is GR-4)
- Coordinates: `pixel_bbox` (displayed page) + `real_world_coords` (metres)
- No CSV in this phase

## Phase 2 — symbol identification

Each JSON also has `symbols[]`:

| Field | Meaning |
|---|---|
| `symbol_class` | `fcu_wall`, `fcu_cass`, `hbc`, `panel_heater`, `door_curtain`, `ahu`, `ashp`, `tray_note` |
| `confidence` | 0–1 |
| `source` | `rule` (production path) or `yolo` (optional residual) |
| `pixel_bbox` / `centroid_px` | Box on the sheet |
| `amber_flag` | Low-confidence / needs human review |
| `item_id` / `legacy_item_id` | Join keys toward inventory |

Annotated audit sheets: boxes + class + confidence burned onto PNG (`annotated/`).

### Rules vs YOLO

- **Rules solve** starter classes on the Hubby Seneca H&C set (tag proximity + layer + colour + compact geometry).
- **YOLO is optional residual** for untagged roof-plant classes (`odu_module`, `damper`, `valve`, …).
- Decision log: [`evals/reports/gr2-decision-log.md`](../../evals/reports/gr2-decision-log.md)
- Weak-label dataset labels: `evals/datasets/hubby-premier-inn-london/yolo/`
- Example weights (short MPS train): `evals/models/symbol_yolo/best.pt`

## Phase 3 — stable inventory (SQLite)

```bash
export DATA_DIR=/Users/pico/workspace/data/getriser
uv run riser-inventory ingest --project HubbyPremierInnLondon
uv run riser-inventory export --project HubbyPremierInnLondon -o out/hubby/
uv run riser-inventory compare --project HubbyPremierInnLondon
```

- DB: `$DATA_DIR/getriser.sqlite` (one shared file; rows scoped by **project name**)
- Premise default: **`mep`**
- Concurrent safe: **WAL** journal + **30s busy_timeout** (multiple processes may open the DB; writers serialize)
- Upsert: same project + same drawing refreshes that sheet’s occurrences (content_hash skip when unchanged)
- Catalog: shared `catalog_items` seeded from trade IDs (`MEC-*` / `ELEC-*` / …)
- Export: JSON (items + nested occurrences with coordinates) + Excel (floor tabs + Master + Summary)

## Gold eval (Hubby)

Source of truth workbook:

`…/HubbyPremierInnLondon/25280-SEN Heating and Cooling Inventory - All Floors - last.xlsx`

Primary gates (Basement + Second Floor):

| Check | Gate |
|---|---|
| Drawing number + scale `1:50` + floor tab | exact |
| FCU / HB tag recall | ≥ 0.95 |
| Basement FCU / HBC / panel symbol counts | 10 / 1 / 7 |
| Second Floor FCU / HBC symbol counts | 31 / 2 |
| Basement F+R plan_m median relative error | ≤ 15% |
| Basement tray plan_m relative error | ≤ 20% |

Latest report: [`evals/reports/latest.md`](../../evals/reports/latest.md)  
Evidence PNGs: [`evals/evidence/gr2/annotated/`](../../evals/evidence/gr2/annotated/)

## Not shipping yet

| Later ticket | Deferred |
|---|---|
| GR-4 | Tender conversion (×2 ×1.15 + tails), waste, formulas as quantity of record |
| GR-5 | Docker one-command pipeline + amber review UI |

Skills (`skills/drawings-reader`, `skills/mep-estimator`) are **not** removed; they remain the method reference. Live extractor IDs use trade prefixes with `legacy_item_id` for skill join.
