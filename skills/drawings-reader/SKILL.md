---
name: drawings-reader
description: Read MEP design-intent drawings (PDF/CAD plots), extract title-block context, trace every annotation leader to its symbol, count equipment, and estimate pipe, tray and refrigerant lengths onto one inventory spreadsheet tab per floor. Use when the user shares a heating and cooling layout, VRV/VRF/HBC/FCU drawing, Drive PDF of an M-56xx sheet, or asks for a take-off, inventory, annotation count or scaled pipe/tray estimate from a drawing.
metadata:
  type: workflow
  version: "1.0"
  domain: mep-hvac
---

# Drawings reader

Turn one MEP layout into one spreadsheet tab. Do not create a new workbook.

For heating, cooling, VRV, HBC, FCU, refrigerant, condensate and tray rules, read `references/ac-specifics.md` before estimating.

## Destination first

If the user has already named one inventory spreadsheet, write into that file as a new sheet. If more than one spreadsheet exists in the folder, stop and consolidate. If no destination is named, ask (see repo README).

## Working order

1. Download the PDF. Read `pdfinfo` (page size, rotation, creator).
2. Extract title block and every word with coordinates (`pdfplumber` + `pdftotext -layout`).
3. Render the sheet at 72 dpi on the true page size so 1 plotted cm can be converted. Crop annotation zones. Do not trust OCR order alone.
4. Build context from title block — project, client, discipline, floor, drawing number, revision, stage, date, scale, paper size.
5. List every HVAC annotation string. For each leader, name the symbol it touches (room + wall/ceiling + colour).
6. Count from tags and symbols, not from how many times the leader text is printed.
7. Estimate only routes that are drawn or that the specification requires (condensate, HBC drain). Separate drawn length from inferred length.
8. Write one tab that matches the existing column template. Amber-flag inferred sizes and lengths.

## Title block (always capture)

- Project, client, architect, MEP consultant
- Drawing number and title
- Floor / level
- Revision, issue, stage, date, drawn/checked
- Scale and paper (`1:50@A1`)
- Disclaimer (`DO NOT SCALE`, design intent, contractor coordinates)

## Scale

- `1:N @ paper` on an A1 plot — 1 cm on that A1 sheet = N/100 metres on site. At 1:50, 1 cm = 0.5 m.
- Confirm page size in points. A1 landscape after a 270° rotation still plots as 841 × 594 mm.
- If the PDF is printed at A3 the graphic scale halves. Never reuse metres from a reduced print.
- Pixel scale at 72 dpi ≈ 0.3528 mm/px. At 1:50 that is ≈ 0.01764 m/px on site.
- Storey-height verticals are not on plan. Use architect section or a stated assumption (record it).

## Annotations

- A leader is a pointer. The inventory item is the equipment or route at the arrowhead.
- Typical-detail call-outs (`CEILING MOUNTED CASSETTE FCU'S`) that appear twice do not mean two extra units.
- Long lines from the sheet margin across rooms are usually call-outs, not pipe runs. Prove a coloured spine or hatch exists before taking length off a leader line.
- Same text in two places = two locations, still count symbols not labels.

## Counts

Prefer tagged IDs (`FCU.B.01` … `FCU.B.10`, `HB:0B:01`). If there are no tags, count distinct coloured symbols the leaders hit. State the method on the tab.

## Lengths

For each indoor unit on a water or refrigerant pair:

`tender_m = (plan_route_m × 2 pipes × 1.15 coordination) + (1.5 m × 2 pipe tails)`

- Plan route follows the drawn spine to the riser / HBC, not a straight line through walls.
- 15% is coordination waste on a Stage 4 intent drawing.
- 1.5 m/pipe is drop, valves and connection at the unit.
- Vertical riser through this floor only unless the sheet shows more.
- Tray — follow the hatched / noted route only, plus 15%. Do not invent a second tray.

## Spreadsheet tab template

Match the existing book. Columns, in order:

1. Item
2. Annotation / item
3. What it refers to / linked to (on the drawing)
4. Count
5. Unit
6. Size (on drawing / inferred)
7. Tender estimate
8. Est. unit
9. Notes

Header block rows 1–6 — project, source drawing, scale basis, diameter caveat, tender definition.

Section bands — indoor units, F+R / refrigerant, tray and risers, electric heating, associated pipe not drawn, exclusions, headlines, caveats.

Blue numbers = inputs. Amber fill = inferred size or length. Do not put unit rates in unless asked.

## One book

- Tab name = floor on the title block (`Basement`, `Ground Floor`, `Second Floor`).
- Never upload a second Google Sheet for the next floor.
- Drawings that do not exist (no M-5601 in the Putney set) are not tabs.

## Stop conditions

- Cannot see the symbol a leader hits — crop and look again before guessing.
- Pipe Ø not printed — infer only from named product (e.g. HBC ports) and flag.
- System type ambiguous (Hybrid water vs refrigerant VRV) — keep lengths, change material note, do not buy both.
