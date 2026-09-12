# AC specifics — generic methods

How to read a heating-and-cooling / VRF / FCU drawing into inventory. No project quantities here. Project numbers live on the workbook.

Read with `SKILL.md` and `inventory-model.md`.

## 1. Context before the plan

From the title block and notes, not from furniture:

- Floor name and drawing number (title block wins over filename)
- Scale and paper
- Revision / date / stage
- `DO NOT SCALE` and design-intent notes
- Sheet premise (heating and cooling vs ventilation vs PH)

From the plan, as **context** not as HVAC items:

- Room names and areas
- Tenant vs landlord demise
- Architectural riser rooms vs MEP take-off boxes
- Fit-out caveats

Rooms tell you what a terminal serves. They are not extra equipment.

## 2. Extraction order that works on plotted PDFs

1. Cloud OCR on a rotated A1 plot is lossy. Do not inventory from that pass.
2. `pdftotext -layout` for title block and notes.
3. `pdfplumber.extract_words()` for `x0`, `top`, `text`. Place tags and list every `FCU.*` / `HB:` / plant name.
4. `pdftoppm -png -r 72` so the raster matches plotted millimetres.
5. Crop the zones where HVAC words sit. Confirm the leader lands on a symbol (bar, box, spine, hatch) — not empty floor.
6. Deduplicate tags. A tag printed twice next to one symbol is one unit.
7. If colour flood-fill on the hatch returns too few pixels (thin linework, anti-alias), abandon pixel length. Use tag-to-core geometry instead and say so.

Typical colour language on many MEP plots (confirm per legend; do not assume):

- Cyan / light-blue spine — ceiling pipe distribution
- Green box / green hatch — riser take-off or tray
- Red bar — electric heater or over-door curtain
- Black leader — annotation only

## 3. Follow the leader

For every HVAC string write three things: printed text, symbol it touches, room / wall.

| Pattern | Treat as | Count from |
|---|---|---|
| Typical-detail call-out printed twice | Label, not equipment | Tags or symbols |
| `FCU.{level}.{nn}` | One indoor unit | Distinct tags |
| `HB:` / `HBC CONTROLLER` / `BC BOX` | One controller | Distinct tags |
| Refrigerant-in-ceiling note on the same spine as home-runs | Description of the home-run already taken | 0 extra metres |
| Refrigerant from outdoor / from above into an HBC | This-storey drop only | Route x 2 pipes, this floor |
| Tray note with a printed width | One tray of that width | Hatch length + 15%, once |
| `R/A & T/B` at a riser box | Rise-above / to-below unless notes say return-air | 1 riser node, not a horizontal main |
| Margin-to-margin leader across rooms | Call-out | No pipe metres |
| Electric heater / door curtain + red bar | Electric terminal | Distinct bars, not label repeats |
| AHU / extract fan / AOV / ASHP-DHW / generator on an H&C sheet | Off-premise unless user expands scope | Exclusion row, priced 0 |

## 4. What belongs on an H&C tab

Always list, even when count is zero:

- Indoor units (cassette / wall / ducted / split) with tag and room
- Controllers (HBC / BC / REFNET)
- Electric heaters and door curtains **if drawn as heat**
- Drawn pipe (F+R or refrigerant) per route and as a sub-total
- Drawn tray
- Drawn risers (landlord vs tenant)
- Pipe the H&C specification requires but the sheet omitted (condensate from FCUs, HBC drain)
- Passing systems through this storey
- Explicit exclusions (tenant indoors, outdoor plant priced on the plant sheet, ventilation plant)

Do not inventory bins, cycle spaces, retractable gates or room names as HVAC.

### Off-drawing allowances (generic, amber)

Only add these if the user asks for a complete tender, and mark them not-on-drawing:

- Specified lagging on **copper refrigerant / F+R only**, not on plastic condensate. Waste +10% on booked copper metres, split by diameter family.
- Tray hangers at stated centres (typical 1.2 m), couplers, drop-rods, pipe clips at 1.0-1.2 m, stub clips leaving the tray (typical 4 per FCU).
- Consumables / expendable materials (OFN, Ag rods, flux, cutter blades, insulation adhesive and tapes). Not "expandable".
- One room controller per FCU unless the plant sheet has no indoors (roof / electric-only lobby = 0).

Do not store project quantities for those allowances inside this skill.

## 5. System reading

Two signals often sit on the same sheet:

1. `HBC` / Hybrid tag — refrigerant outdoor to HBC, water HBC to indoors.
2. Printed refrigerant-from-HBC-to-rooms — VRF pair all the way.

Action: keep the **same pair lengths**; flag the material. Do not buy both water copper and refrigerant copper for the same run. Confirm against the project specification before order.

When the drawing is silent, infer only from the named product family and mark inferred:

- Indoor VRF pair often 6.4 / 9.5 mm pending the indoor schedule
- Outdoor / riser pair often 15.88 / 19.05-22.2 mm pending HP
- Hybrid indoor water ports often 22 mm OD; step up if load is high
- Condensate 20-22 mm wall / 32 mm cassette, fall 1:100, **not** to the refrigerant tray

## 6. Measurement types (use the name on the Notes cell)

### Printed

Copy. Duct 400 x 400, tray 400 mm, vessel litres. Never scale a printed size.

### Scaled plan

Convert first:

- `1:N @` the plotted paper
- 1 cm on that paper = N/100 m on site
- 72 dpi raster about 0.3528 mm/px

Walk the coloured spine or hatch. Do not cut corners through rooms.

### Geometry estimate

When hatch cannot be traced, use average plan to the nearest riser/HBC learned from a floor that *was* measured. State geometry estimate, the average plan (m), and the formula.

### This-storey vertical

`storey_height_m x 2 pipes` (and only the systems that actually pass). Source of storey height: section, or a written assumption.

### Specified-not-drawn

Example condensate: `unit_count x average_run_m` to the corridor drain stack. Say it is not on this sheet and must be confirmed on drainage.

### Tender conversion (two-pipe terminals)

```
tender_m = plan_m x 2 x 1.15 + 1.5 x 2
```

| Term | Meaning |
|---|---|
| `plan_m` | Scaled or geometry route, one way, HBC/riser to unit |
| `2` | Flow and return, or liquid and gas |
| `1.15` | 15% coordination on intent drawings |
| `1.5` | Drop + isolation + connection per pipe |

Tray: `plan_m x 1.15`, one tray per printed width.

Passing riser on an occupied storey: `building_system_count x 2 x storey_height_m`. Building system count comes from a note on the drawings (often the top floor or roof), not from inventing one stack per floor.

Plant deck: laterals on the deck only. Do not add the multi-storey rise again.

## 7. Diameters

| If | Then |
|---|---|
| Printed | Use printed. |
| Not printed | Infer from product, write inferred, amber. |
| Two readings exist (water vs refrigerant) | One material column, one flag. Never both. |

## 8. What not to take (generic)

- Outdoor units on a floor sheet when a plant sheet exists
- Full-height riser from a basement or ground-floor sheet
- The same stack priced as per-floor passing and as a third full-height total
- Tenant indoor units inside a demise marked tenant
- A second tray that is not hatched
- Leader lines used as pipe centre-lines
- Furniture, bins, cycle stands
- A floor tab for a drawing that does not exist, unless the user orders an interpolation and you label it interpolated
- Bedroom FCU rows copied onto a plant tab
- Ventilation / DHW / life-safety plant on an H&C-priced section

## 9. Checks before publishing a tab

- Every in-scope HVAC string on the PDF appears at least once
- Off-premise strings appear once under exclusions
- Leader text count is not equipment count unless tags agree
- Tag sequence has no silent hole — or the hole is called out
- Sub-totals match the sum of routes
- Verticals are this storey only
- Tray width matches that sheet
- Master tab updated with the same item IDs
- No formula returns REF / N/A / VALUE / DIV0
- Floor total SUM stops on the row above the total (no circular ref)
