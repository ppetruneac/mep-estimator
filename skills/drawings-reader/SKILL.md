---
name: drawings-reader
description: Read MEP design-intent drawings (PDF or CAD plots), extract title-block context, classify each annotation against the sheet premise, count equipment from symbols not labels, estimate pipe tray and refrigerant lengths, and write one inventory tab per drawing plus a master item register and a cross-tab summary by item ID. Use when the user shares a heating and cooling layout, VRV VRF HBC FCU drawing, or asks for a take-off, annotation count, scaled length, or inventory spreadsheet from a drawing.
metadata:
  type: workflow
  version: "1.3"
  domain: mep-hvac
---

# Drawings reader

Turn each MEP layout into one spreadsheet tab, then roll unique items into a master register. If more than one drawing is in the book, add a Summary tab keyed by inventory item ID. Do not invent a second workbook if the user already named one.

Heating, cooling, VRV, HBC, FCU, refrigerant, condensate and tray rules live in `references/ac-specifics.md`. Item IDs, master tab, cross-tab Summary, per-drawing vs building totals, and CSV/Excel write rules live in `references/inventory-model.md`.

Do not keep project-specific quantities, Drive file IDs, or job numbers in this skill. Those belong on the project workbook.

## Destination first

- If the user named one inventory spreadsheet, add a sheet. Do not create a parallel book.
- If several spreadsheets exist in the same folder, stop and consolidate to one.
- If no destination is named, ask before writing.
- If a cloud connector can read but cannot append a tab, write a complete local `.xlsx` and say the cloud file was not updated.

## Working order

1. Download the PDF. Read page size, rotation, creator (`pdfinfo`).
2. Extract title block and every word with coordinates (`pdfplumber` + `pdftotext -layout`).
3. Render at 72 dpi on the true plotted size so 1 cm on the sheet can be converted. Crop annotation zones. Do not inventory from OCR reading-order alone.
4. Capture title-block context (project, discipline, floor, number, rev, stage, scale, paper).
5. State the **sheet premise** from the title (heating and cooling, ventilation, public health, electrical). Every later item is in-scope, interface, or out-of-scope against that premise.
6. List every annotation string. For each leader, name the symbol and room it hits.
7. Count from tags and symbols, not from how many times the label is printed.
8. Measure only routes that are drawn, or that the specification of *this* discipline requires. Separate drawn length from inferred length.
9. Write one tab that matches the book template. Amber-flag inferred sizes and lengths. Assign a stable item ID.
10. Update the **Master** tab (union of IDs across drawings). Mark which metres are unique to that sheet and which would double-count a riser if summed.
11. When two or more drawing tabs exist, rebuild the **Summary** tab. One row per item ID. Include a **Where found** column listing every drawing tab that carries that ID.

Repeat 1-11 for every remaining drawing. Similar plates may share a template; still re-count tags on that sheet. Rebuild Summary after the last drawing, not only after the first.

## Cross-tab Summary (required once there is more than one drawing)

Do not leave the reader to add floor tabs by eye. Summary is the building view.

- Key = inventory item ID (`HC-FCU-WALL`, `HC-CU-IN`, …), not the local line code `A01`.
- One row per ID.
- Columns at minimum: item_id, description, unit, qty_building, **where_found**, scope.
- `where_found` is a readable list of tab names and drawing numbers where that ID appears with qty > 0. Example: `Basement (M-560X); Second Floor (M-5602); Third Floor (M-5603)`.
- Optional extra columns: qty per tab. Those do not replace `where_found`.
- Do not paste each floor headline block into Summary. That double-counts passing risers and plant laterals.
- After any floor qty change, refresh `where_found` and qty_building from the same IDs.

Full column list is in `references/inventory-model.md`.

## Title block (always capture)

- Project, client, architect, MEP consultant
- Drawing number and title. Title block wins over the PDF filename
- Floor / level
- Revision, issue, stage, date
- Scale and paper (`1:50 @ A1`)
- Disclaimer (`DO NOT SCALE`, design intent, contractor coordinates)

## Sheet premise (scope filter)

The title is the filter. A heating-and-cooling sheet may *show* AHUs, extract fans, smoke shafts, AOV, DHW plant, generators and acoustic screens because they sit on the same roof. Those are **visible, not priced** on an H&C take-off unless the user expands the premise.

| Premise on title | In inventory | Record as interface / exclusion |
|---|---|---|
| Heating and cooling / VRF / FCU | Indoor units, HBC/BC, refrigerant or F+R, condensate required by those units, refrigerant tray, electric terminals drawn as heat | AHU, kitchen/WC extract, smoke extract, AOV, DHW ASHP, calorifiers, generator, acoustic screen, drainage stacks |
| Ventilation | AHU, fans, ducts, attenuators, grilles, AOV where titled | Refrigerant pairs, FCU tags |
| Public health / DHW | Calorifiers, ASHP-DHW, HWS, BCWS | VRF outdoor modules |
| Electrical | Heaters only if this is the electrical sheet | Mechanical plant |

Write every out-of-scope annotation once under **Exclusions / interfaces** with qty priced = 0 so the next reader does not think it was missed.

## Scale

- `1:N @ paper` on that paper size. 1 cm on the plotted sheet = N/100 metres on site. At 1:50, 1 cm = 0.5 m.
- Confirm page size in points. A1 landscape after a 270 degree rotation still plots as 841 x 594 mm.
- A reduced print (A1 drawing issued at A3) halves the graphic scale. Never reuse metres from a reduced print.
- Pixel scale at 72 dpi is about 0.3528 mm/px. At 1:50 that is about 0.01764 m/site-m per pixel.
- Storey-height verticals are not on plan. Use an architect section or a stated assumption. Record the assumption on the tab.

## How to extract

- Cloud OCR on a rotated A1 plot is jumbled. Use it to find the file, not to count.
- `pdfplumber.extract_words()` with `x0, top` places tags and leaders. Deduplicate identical tag strings at one symbol.
- `pdftoppm -png -r 72`, then crop west/east/tray/lobby/plant zones and look at the image. Confirm the leader lands on a coloured symbol.
- Colour flood-fill under-counts thin hatch. When hatch is thin, measure from tag coordinates along the corridor spine instead of trusting pixel counts.
- If a full-sheet raster is not available, say the plan length is geometry-estimated, not pixel-measured.

## Annotations

- A leader is a pointer. The inventory item is the equipment or route at the arrowhead.
- Typical-detail call-outs printed twice (`CEILING MOUNTED CASSETTE FCU'S`) are not two extra units.
- Long lines from the sheet margin across rooms are usually call-outs, not pipe runs. Prove a coloured spine or hatch exists before taking length off a leader line.
- Same text in two places = two locations; still count symbols, not labels.
- Discipline shorthand on one set is not universal. Read `R/A & T/B` against the sheet notes before treating it as return-air ductwork.

## Counts

Prefer tagged IDs (`FCU.02.01`, `HB:02:01`). If there are no tags, count distinct coloured symbols the leaders hit. State the method on the tab.

After listing tags, look for gaps in the sequence. Allow +1 in Notes; do not invent the unit until the plot is cropped and the gap is confirmed empty or present.

## Lengths (measurement types. name which one you used)

| Type | When | How |
|---|---|---|
| Printed | Size or length is written on the sheet | Copy it. Do not scale it. |
| Scaled plan | Coloured spine or hatch is visible | Measure along the route at the sheet scale. Not crow-flies through walls. |
| Geometry estimate | Repetitive plate, hatch too thin to trace | Average plan from each terminal to the nearest known core, using a plate learned on a floor that *was* traced. |
| Vertical assumption | Rise through this storey only | Storey height from section, or a stated m/storey. Never the full building height from one floor sheet. |
| Specified-not-drawn | Spec requires it (condensate, HBC drain) | Unit count x stated average run. Flag amber. Confirm on the correct discipline drawing. |
| Excluded | Visible but off-premise | Qty 0 on this book. Point to the sheet that owns it. |

Default tender conversion for a two-pipe indoor run (water F+R or refrigerant pair):

```
tender_m = (plan_route_m x 2 pipes x 1.15 coordination) + (1.5 m x 2 pipe tails)
```

- 15% is coordination waste on a design-intent drawing that says positions are approximate.
- 1.5 m/pipe is drop, valves and connection at the unit (3.0 m pair tails).
- One tray per printed size on that sheet, plus 15%. Do not mix a 300 mm basement tray with a 400 mm bedroom tray.
- Passing systems through a storey are a building-wide count stated on the drawings. Price `systems x 2 pipes x storey_height` on that floor. Do not also price the full-height stack on the plant sheet.
- Plant tab prices deck laterals and plant only. Floor tabs price floor distribution. Name the interface so the two are not added twice.

## System type

An HBC tag can mean Hybrid (refrigerant to HBC, water HBC to rooms). Printed `REFRIGERANT FROM HBC TO ROOMS` can mean VRF all the way. Keep the lengths. Change the material note. Do not buy water and refrigerant for the same run.

## Stop conditions

- Cannot see the symbol a leader hits. Crop and look again before guessing.
- Pipe diameter not printed. Infer only from named product and flag inferred.
- System type ambiguous. Keep lengths, change material note, do not buy both.
- Tag sequence has a hole. Allow, do not invent.
- Storey height not on the HVAC sheet. State the assumption and stop short of fabrication quantities.
- Item is on the sheet but off the title premise. Exclusion row, not a priced line.

## Destination placeholder

If no inventory file has been named yet, ask where to write (one spreadsheet, one Master tab, one Summary tab, one sheet per drawing).
