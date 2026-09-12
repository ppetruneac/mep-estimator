# mep-estimator

Estimator toolkit for mechanical, electrical and plumbing take-offs from Stage 3 / Stage 4 design-intent drawings.

The method in this repo is also the seed for **Riser** ([getriser.co.uk](https://getriser.co.uk)): take-off, bill of materials, live rates, project estimates, project Q&A, Drive + email issue pack. Excel stays the handshake. The schema is the product.

## Product docs

| Path | Purpose |
|---|---|
| [docs/riser/business-plan.md](docs/riser/business-plan.md) | Offer, buyer, pricing shape, go-to-market |
| [docs/riser/technical-execution.md](docs/riser/technical-execution.md) | Domain model, pipeline, Excel round-trip, build slices |

## Skills

| Path | Purpose |
|---|---|
| `skills/drawings-reader/SKILL.md` | Read an MEP drawing into inventory, counts and pipe / tray estimates. |
| `skills/drawings-reader/references/` | AC take-off rules and inventory model (IDs, categories, Summary, where-found). |
| `skills/mep-estimator/SKILL.md` | Price that inventory. Material Rates + Labour by work category. Join by item ID. |
| `skills/mep-estimator/references/` | Pricing formulas and spec-first rate sources. |

## How to use the skills

1. User shares a drawing (PDF / Drive link) and points at **one** inventory spreadsheet.
2. Load `skills/drawings-reader/SKILL.md`.
3. Read `references/ac-specifics.md` and `references/inventory-model.md` before touching heating, cooling, VRV, HBC, FCU, refrigerant, condensate or tray.
4. Extract title-block context first, then annotations (trace each leader to the symbol), then counts, then lengths.
5. Append a new **sheet** (tab) to the existing workbook. Do not create a second spreadsheet.
6. To price, load `skills/mep-estimator/SKILL.md`. Rates live on Material Rates / Labour. Floors look them up. Do not paste unit rates.
7. If Drive cannot append or upload, write the complete local `.xlsx` and say so. Folder listing is the proof.

## Current inventory workbook (reference job)

One spreadsheet only, with a tab per drawing:

- Live Sheet (Basement + Ground Floor only): [25280-SEN Heating and Cooling Inventory](https://docs.google.com/spreadsheets/d/18I4tEO1nvDH4V83tHhEsKRLiKu1I4Jmbd1pUaZA0DJY/edit)
- Complete local book: `25280-SEN Heating and Cooling Inventory - All Floors.xlsx` in the project artifacts folder
- Drive folder: [project drawings folder](https://drive.google.com/drive/folders/1neR-n1gdUHPirWpQ90je6Sw_Yq3mT5Ou)
- Tabs taken off: Summary, Basement, Ground Floor, First–Ninth Floor, Roof Plant
- First Floor has no drawing. It is interpolated from 2F–5F and labelled as such.

## Rules that already bit us

- One spreadsheet. Sheets inside it. Never a new workbook per floor.
- Leaders are not extra equipment. Count tags and symbols the leader points at.
- Title block `1:50 @ A1` means 1 cm on the plotted A1 sheet = 0.5 m on site. A reduced print changes the scale.
- `DO NOT SCALE` still applies for setting-out. Scaled lengths are tender estimates only.
- If a pipe diameter is not printed, say so. Infer from product data and flag the row.
- Colour flood-fill under-counts thin CAD hatch. Use tag-to-core geometry.
- Bedroom floors print **400 mm** tray. Basement prints **300 mm**. Do not mix.
- Passing risers are a building-wide system count. Do not add the same stack three times.
- Tag gaps are allowances, not invented units.
- Title block wins over the PDF filename.
- HBC tag vs refrigerant-from-HBC-to-rooms — keep lengths, do not buy both materials.
- Floor money columns are formulas against Material Rates. Labour £/hour cells are the only labour inputs.

## Destination (required before the next write)

The take-off method in this repo is ready. Further writes still need a **single destination** so results are not scattered.

**Where should the next inventory write go?**

Reply with one of:

1. Google Sheet ID / URL.
2. A Drive folder ID if the complete All Floors workbook should live somewhere else.
3. A tab name convention if it is not `{Floor name}`.
4. Whether electrical / public-health take-offs get their own tabs in the same book, or stay AC-only for now.

Do not start a new project take-off until that destination is confirmed.
