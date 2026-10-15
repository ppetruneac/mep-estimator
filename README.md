# mep-estimator

Estimator toolkit for mechanical, electrical and plumbing take-offs from Stage 3 / Stage 4 design-intent drawings.

The method in this repo is also the seed for **Riser** ([getriser.co.uk](https://getriser.co.uk)): take-off, bill of materials, live rates, project estimates, project Q&A, Drive + email issue pack. Excel stays the handshake. The schema is the product.

## Product docs

| Path | Purpose |
|---|---|
| [docs/riser/business-plan.md](docs/riser/business-plan.md) | Offer, buyer, pricing shape, go-to-market |
| [docs/riser/technical-execution.md](docs/riser/technical-execution.md) | Domain model, pipeline, Excel round-trip, build slices |
| [AGENTS.md](AGENTS.md) | Extractor setup, eval gate, ID conventions |

## Skills (method docs — kept)

| Path | Purpose |
|---|---|
| `skills/drawings-reader/SKILL.md` | Read an MEP drawing into inventory, counts and pipe / tray estimates |
| `skills/drawings-reader/references/` | AC take-off rules and inventory model (legacy `HC-*` IDs) |
| `skills/mep-estimator/SKILL.md` | Price that inventory. Material Rates + Labour by work category |
| `skills/mep-estimator/references/` | Pricing formulas and spec-first rate sources |

## Phase 1 extractor (`riser_extract`)

Deterministic geometry and text extraction from plotted MEP PDFs (no ML/YOLO).

```bash
uv venv .venv && uv pip install -e ".[dev]"

uv run riser-extract path/to/drawing.pdf -o out/
# writes out/inventory_json/{drawing-number}.json
# and out/overlays/{drawing-number}.pdf
```

Each occurrence carries:

- Trade `item_id` (`MEC-FCU-WALL`, `ELEC-PNL`, `PLUM-COND`, `VENT-AHU`, …)
- `legacy_item_id` matching the skill inventory model (`HC-FCU-WALL`, …)
- Coordinates (pixel bbox + metres), scale, layer, colour, measurement type

JSON only in Phase 1. Full Excel Master/Summary is GR-3.

### Evals

Gold: Hubby Premier Inn London inventory  
`…/HubbyPremierInnLondon/25280-SEN Heating and Cooling Inventory - All Floors - last.xlsx`

```bash
uv run python evals/scripts/parse_ground_truth.py
uv run riser-eval --primary-only   # Basement + Second Floor gates
```

See [evals/README.md](evals/README.md) and `evals/reports/latest.md`.

## How to use the skills

1. User shares a drawing (PDF / Drive link) and points at **one** inventory spreadsheet.
2. Load `skills/drawings-reader/SKILL.md`.
3. Read `references/ac-specifics.md` and `references/inventory-model.md` before touching heating, cooling, VRV, HBC, FCU, refrigerant, condensate or tray.
4. Extract title-block context first, then annotations (trace each leader to the symbol), then counts, then lengths.
5. Append a new **sheet** (tab) to the existing workbook. Do not create a second spreadsheet.
6. To price, load `skills/mep-estimator/SKILL.md`. Rates live on Material Rates / Labour. Floors look them up. Do not paste unit rates.

## Current inventory workbook (reference job)

One spreadsheet only, with a tab per drawing:

- Complete local book: `25280-SEN Heating and Cooling Inventory - All Floors - last.xlsx` under the training-docs folder
- Tabs taken off: Summary, Basement, Ground Floor, First–Ninth Floor, Roof Plant
- First Floor has no drawing. It is interpolated from 2F–5F and labelled as such.
