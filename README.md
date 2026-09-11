# mep-estimator

Estimator toolkit for mechanical, electrical and plumbing take-offs from Stage 3 / Stage 4 design-intent drawings.

This repository captures the method used on **Hub by Premier Inn Putney** (project 25280, Seneca Group / Curio Architects / Mosser Ltd) so the same process can be repeated without inventing a new spreadsheet each time.

## What lives here

| Path | Purpose |
|---|---|
| `skills/drawings-reader/SKILL.md` | Agent skill v1.1. Load this when a user drops an MEP drawing and wants inventory, counts and pipe / tray estimates. |
| `skills/drawings-reader/references/ac-specifics.md` | Air-conditioning / heating-and-cooling specifics. Every rule used to turn a Seneca M-56xx or roof M-5150 sheet into a tab. |
| `inventory/` | CSV export of each tab for File → Import into the single Google Sheet. |

## How to use the skill

1. User shares a drawing (PDF / Drive link) and points at **one** inventory spreadsheet.
2. Load `skills/drawings-reader/SKILL.md`.
3. Read `references/ac-specifics.md` before touching heating, cooling, VRV, HBC, FCU, refrigerant, condensate or tray.
4. Extract title-block context first, then annotations (trace each leader to the symbol), then counts, then lengths.
5. Append a new **sheet** (tab) to the existing workbook. Do not create a second Google Sheet.
6. If Drive cannot append or upload, write the complete local `.xlsx` and say so. Folder listing is the proof.

## Current inventory workbook

One spreadsheet only, with a tab per drawing:

- Live Sheet (Basement + Ground Floor only): [25280-SEN Heating and Cooling Inventory](https://docs.google.com/spreadsheets/d/18I4tEO1nvDH4V83tHhEsKRLiKu1I4Jmbd1pUaZA0DJY/edit)
- Complete local book (12 tabs): `25280-SEN Heating and Cooling Inventory - All Floors.xlsx` in the project artifacts folder
- Drive folder: [project drawings folder](https://drive.google.com/drive/folders/1neR-n1gdUHPirWpQ90je6Sw_Yq3mT5Ou)
- Tabs taken off: Summary, Basement, Ground Floor, Second–Ninth Floor, Roof Plant
- Missing from the drawing set: no `25280-SEN-01` First Floor sheet. Do not invent that floor.

## Rules that already bit us

- One Google Spreadsheet. Sheets inside it. Never a new workbook per floor.
- Leaders are not extra equipment. Count tags and symbols the leader points at.
- Title block `1:50 @ A1` means 1 cm on the plotted A1 sheet = 0.5 m on site. A reduced print changes the scale.
- `DO NOT SCALE` still applies for setting-out. Scaled lengths are tender estimates only.
- If a pipe diameter is not printed, say so. Infer from product data and flag the row.
- Colour flood-fill under-counts thin CAD hatch. Use tag-to-core geometry.
- Bedroom floors print **400 mm** tray. Basement prints **300 mm**. Do not mix.
- 8F/9F notes give **7** hotel-room systems. Price passing risers from that number. Do not add the same stack three times.
- Tag gaps (`FCU.06.16`, `FCU.07.21`) are allowances, not invented units.
- Roof filename `25287-SEN-00-DR-M-5150` is still this building.
- HBC tag vs `REFRIGERANT FROM HBC TO ROOMS` — keep lengths, do not buy both materials.

## Destination (required before the next write)

The take-off method in this repo is ready. Further writes still need a **single destination** so results are not scattered.

**Where should the next inventory write go?**

Reply with one of:

1. Google Sheet ID / URL (preferred: keep using `18I4tEO1nvDH4V83tHhEsKRLiKu1I4Jmbd1pUaZA0DJY` and add / replace tabs).
2. A Drive folder ID if the complete All Floors workbook should live somewhere else.
3. A tab name convention if it is not `{Floor name}`.
4. Whether electrical / public-health take-offs get their own tabs in the same book, or stay AC-only for now.

Do not start a new project take-off until that destination is confirmed.
