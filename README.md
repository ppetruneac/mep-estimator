# mep-estimator

Estimator toolkit for mechanical, electrical and plumbing take-offs from Stage 3 / Stage 4 design-intent drawings.

This repository captures the method used on **Hub by Premier Inn Putney** (project 25280, Seneca Group / Curio Architects / Mosser Ltd) so the same process can be repeated floor by floor without inventing a new spreadsheet each time.

## What lives here

| Path | Purpose |
|---|---|
| `skills/drawings-reader/SKILL.md` | Agent skill. Load this when a user drops an MEP drawing and wants inventory, counts and pipe / tray estimates. |
| `skills/drawings-reader/references/ac-specifics.md` | Air-conditioning / heating-and-cooling specifics. Every rule that was used to turn a Seneca M-56xx sheet into a tab in the inventory workbook. |

## How to use the skill

1. User shares a drawing (PDF / Drive link) and points at **one** inventory spreadsheet.
2. Load `skills/drawings-reader/SKILL.md`.
3. Read `references/ac-specifics.md` before touching heating, cooling, VRV, HBC, FCU, refrigerant, condensate or tray.
4. Extract title-block context first, then annotations (trace each leader to the symbol), then counts, then lengths.
5. Append a new **sheet** (tab) to the existing workbook. Do not create a second Google Sheet.

## Current inventory workbook

One spreadsheet only, with a tab per floor:

- File: [25280-SEN Heating and Cooling Inventory](https://docs.google.com/spreadsheets/d/18I4tEO1nvDH4V83tHhEsKRLiKu1I4Jmbd1pUaZA0DJY/edit)
- Drive folder: [project drawings folder](https://drive.google.com/drive/folders/1neR-n1gdUHPirWpQ90je6Sw_Yq3mT5Ou)
- Tabs completed: `Basement`, `Ground Floor`
- Missing from the drawing set: no `25280-SEN-01` First Floor sheet. Do not invent that floor.

## Rules that already bit us

- One Google Spreadsheet. Sheets inside it. Never a new workbook per floor.
- Leaders are not extra equipment. Count tags and symbols the leader points at.
- Title block `1:50 @ A1` means 1 cm on the plotted A1 sheet = 0.5 m on site. A reduced print changes the scale.
- `DO NOT SCALE` still applies for setting-out. Scaled lengths are tender estimates only.
- If a pipe diameter is not printed, say so. Infer from product data and flag the row.

## Destination (required before the next write)

The take-off method in this repo is ready. The next floor still needs a **single destination** so results are not scattered again.

**Where should the next floor inventory be written?**

Reply with one of:

1. Google Sheet ID / URL (preferred: keep using `18I4tEO1nvDH4V83tHhEsKRLiKu1I4Jmbd1pUaZA0DJY` and add a tab).
2. A Drive folder ID if the workbook should live somewhere else.
3. A tab name convention if it is not `{Floor name}`.
4. Whether electrical / public-health take-offs get their own tabs in the same book, or stay AC-only for now.

Do not start Second Floor (`25280-SEN-02-DR-M-5602`) until that destination is confirmed.
