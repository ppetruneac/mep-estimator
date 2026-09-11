# AC specifics — drawing to inventory tab

Everything used to convert Seneca heating-and-cooling layouts into a spreadsheet tab on Hub by Premier Inn Putney (25280). Read this with `SKILL.md`.

## 1. Project and drawing family

| Field | Value |
|---|---|
| Project | Hub by Premier Inn Putney |
| Client | Mosser Ltd |
| Architect | Curio Architects |
| MEP | Seneca Group Ltd |
| Discipline sheets | `25280-SEN-{level}-DR-M-56xx` Heating and Cooling Layout |
| Stage / rev seen | Stage 4, Rev P1 |
| Plot | AutoCAD LT 2026 → PDF, A1, often page rot 270° |
| Scale on title block | `1:50@A1` |

### Sheets in the Drive folder

| Level | Drawing |
|---|---|
| Basement | `25280-SEN-0X-DR-M-560X` |
| Ground Floor | `25280-SEN-00-DR-M-5600` (file name sometimes `0X` / `5600`) |
| First Floor | **Not in the set.** Do not invent M-5601. |
| Second–Ninth | `5602` … `5609` |
| Roof plant | separate M-5150 copy, different project number on the filename (`25287`) — treat as another drawing, not this floor series |

Title block always wins over the PDF filename.

## 2. What to read first (context)

From the title block and notes, not from the plan:

- Floor name and drawing number
- Scale and paper
- Revision / date / stage (`PRELIMINARY DESIGN` / Stage 4)
- Standard notes — `DO NOT SCALE`; positions approximate for tender; contractor produces coordinated working drawings; Seneca is not responsible for setting-out or manufacturing dimensions
- North point, disclaimer

From the plan, as context not as HVAC items:

- Room names and areas (`7.3 m²`, `152.7 m²`)
- Tenant vs hotel demise (retail units, office lobby, hotel lobby)
- Architectural riser rooms (`Riser 1.6 m²`) vs MEP green take-off boxes
- Notes such as `Cycle space provision subject to tenant fit-out`

These rooms tell you what an FCU or heater is serving. They are not extra equipment.

## 3. How text was extracted

1. Drive OCR / `google_drive_read_file` is lossy and jumbled on rotated A1 plots. Do not inventory from that pass alone.
2. `pdftotext -layout` gives reading order for title block and notes.
3. `pdfplumber.extract_words()` gives `x0`, `top`, `text`. Use this to place annotations on the sheet.
4. `pdftoppm -png -r 72` on the PDF as stored (after rotation handling) so the raster matches plotted millimetres.
5. Crop the zones where HVAC words sit. Confirm the leader lands on a red bar, green box, cyan spine or hatch — not on empty floor.

Colour language used on these Seneca plots:

- **Cyan / light blue spine** — ceiling pipe distribution (basement F+R / refrigerant in ceiling)
- **Green box / green hatch** — riser take-off or 300 mm tray
- **Red bar** — electric panel heater or over-door curtain
- **Black leader** — annotation only

## 4. Annotations — follow the leader

### Rule

Write three things for every HVAC string: the printed text, the symbol it touches, the room / wall.

### Basement (`M-560X`) — what was found

| Printed annotation | What it actually referred to | Count basis |
|---|---|---|
| `CEILING MOUNTED CASSETTE FCU'S` | Printed **twice**. (1) North of kitchen, leader down onto `FCU.B.01` cluster. (2) Bottom-right margin, leader onto `FCU.B.09` in Hotel Office. | Typical-detail call-out. Count came from tags `FCU.B.01`–`FCU.B.09` = **9 cassettes**, not from the two labels. |
| `WALL MOUNTED FCU IN COMMS ROOM` | Wall unit `FCU.B.10` in Main Comms 8.8 m² | 1 |
| `FCU.B.01` … `FCU.B.10` | Individual indoor units | 10 tagged terminals |
| `HBC CONTROLLER` / `HB:0B:01` | Hybrid / heat branch controller at east bar, next to `from above` riser | 1 controller |
| `REFRIGERANT PIPEWORK FROM ABOVE TO CEILING` | Vertical drop at east riser into the HBC. Outdoor units not on this sheet | 1 route, this floor only |
| `REFRIGERANT PIPEWORK IN CEILING` | Two leaders on the cyan ceiling spine (kitchen branch and restaurant branch) | Describes the same home-runs as FCU F+R. **0 extra metres** |
| `300 mm TRAY FOR RETAIL` | Hatched high-level tray, west retail wall → retail demise → dog-leg at team-room partition → staff-WC / servery spine → east retail VRV riser | 1 tray, 300 mm is the only services size printed on the sheet |
| `RISER ALLOCATED TO RETAIL – VRV SYSTEM` | Tenant shaft on the east stack | 1 riser, no tenant indoor units |
| `Risers at high level` | Two notes on kitchen / restaurant spine, rectangular services box | Coordination only, no extra HVAC vertical |
| `ELECTRIC PANEL HEATER` | Red wall bars. Seven separate leaders (staff WC / accessible WC-shower, corridor / cycle store, archive, luggage, cycle-store south wall). Extra red bar visible on Linen Intake | Tender **7**, allow **8** if schedule not issued |

### Ground Floor (`M-5600`) — what was found

No `FCU.G.xx` tags. No HBC. Hotel terminals are electric only.

| Printed annotation | What it actually referred to | Count basis |
|---|---|---|
| `ELECTRIC OVER DOOR DOOR CURTAIN` | Vertical red bar on the **west wall** of Hotel Lobby and Reception 7.3 m² — door onto Deliveries Through Route | 1 air curtain |
| `ELECTRIC PANEL HEATER` | Horizontal red bar on the **south wall** of the same 7.3 m² lobby | 1 panel, different wall from the curtain |
| `RISER RETAIL/OFFICE REFRIGERANT PIPEWORK R/A & T/B` (left margin) | Green box inside **Riser Lobby 2.1 m²**, east of Stair 2 / office core. Leader crosses Office Cycle Store as text only | 1 west riser |
| `RISER RETAIL/OFFICE REFRIGERANT PIPEWORK R/A & T/B` (right margin) | Green box on the **east face** of the two 1.6 m² courtyard risers, at Retail Unit 1 149.5 m² | 1 east riser |

`R/A & T/B` read as **rise-above and to-below** — the same 2-pipe refrigerant pair continuing to basement and to floors above. Not a GF distribution main. Not return-air ductwork.

The long horizontal lines from left and right margins are **call-outs**. They were not taken as pipe across retail / office.

## 5. Inventory items (what goes on the tab)

Always include, even when count is zero:

- Indoor units (cassette / wall / ducted) with tag and room
- Controllers (HBC / BC / REFNET) with tag
- Electric heaters and door curtains
- Drawn pipe (F+R or refrigerant) per route and as a sub-total
- Drawn tray
- Drawn risers (hotel vs tenant)
- Pipe the specification requires but the sheet omitted (condensate, HBC drain, filling loop)
- Explicit exclusions (tenant indoor units, outdoor plant, riser above this floor)

Do not inventory bins, cycle spaces or retractable gates as HVAC. Record them once under exclusions if the user said keep all drawing text.

## 6. System reading (Putney)

Two signals on the basement sheet:

1. Tag `HBC CONTROLLER HB:0B:01` → Mitsubishi City Multi **Hybrid VRF**. Refrigerant outdoor → HBC. **Water** flow and return HBC → indoor units.
2. Printed `REFRIGERANT PIPEWORK IN CEILING` → could be read as refrigerant VRV all the way to FCUs.

Action used: treat distribution to FCUs as **water F+R** because of the HBC tag; keep the same **lengths** if the specification later says refrigerant; do not buy both materials. Flag the row.

Mitsubishi HBC points used when the drawing was silent:

- Indoor water ports typically **22 mm OD**
- Indoor capacity above ~5.6 kW may need larger field pipe (step toward 28 mm OD / 20 mm+ ID)
- Max HBC-to-indoor run in the product literature ~**60 m** (basement longest plan run was FCU.B.10 at 21 m — inside limit)
- Water design pressure at HBC 0.6 MPa; field pipe min 1.0 MPa
- HBC needs drain / overflow, isolation, air vents, drain cock, filling loop, strainer, PRV, expansion vessel (usually field-supply)

Kitchen `FCU.B.01` / `FCU.B.03` in 43.3 m² kitchen — load may exceed 5.6 kW. Amber flag for upsize.

Refrigerant pair into the HBC (outdoor not on sheet) inferred **ø15.88 mm** liquid/HP and **ø19.05–22.2 mm** gas/LP for an 8–12 HP outdoor. Not printed.

Ground floor has no FCUs — 22 mm water does not apply there.

## 7. Scale and how lengths were measured

### Conversion

- Title block `1:50 @ A1`
- 1 cm on the A1 plot = **0.50 m** on site
- 1 m on site = 2 cm on the A1 plot
- Raster at 72 dpi → 0.3528 mm/px → at 1:50 → **0.01764 m/px**

Basement page after render used for measuring: 2384 × 1684 px (A1 landscape at 72 dpi).

### What was measured vs assumed

**Basement F+R (each FCU to HBC along the cyan spine, not crow-flies)**

| Unit | Plan route | Tender F+R (plan × 2 × 1.15 + 3.0 m tails) |
|---|---|---|
| FCU.B.01 kitchen | 18.0 m | 44.4 m |
| FCU.B.02 team room | 18.0 m | 44.4 m |
| FCU.B.03 kitchen/servery | 14.0 m | 35.2 m |
| FCU.B.04 restaurant W | 11.0 m | 28.3 m |
| FCU.B.05 restaurant C | 7.5 m | 20.3 m |
| FCU.B.06 restaurant E | 4.5 m | 13.4 m |
| FCU.B.07 restaurant SE | 3.0 m | 9.9 m |
| FCU.B.08 lobby edge | 5.5 m | 15.7 m |
| FCU.B.09 hotel office | 7.0 m | 19.1 m |
| FCU.B.10 comms wall | 21.0 m | 51.3 m |
| **Hotel F+R sub-total** | | **282 m** |

Formula applied:

```
tender_m = plan_m * 2 * 1.15 + 1.5 * 2
```

- `2` = flow and return (or liquid and gas if the spec is refrigerant)
- `1.15` = 15% coordination on a Stage 4 intent drawing that says positions are approximate
- `1.5 m` per pipe = drop, isolation and connection at the FCU

**Basement refrigerant (this floor only)**

- `FROM ABOVE TO CEILING`: ~3 m horizontal HBC to shaft + ~4 m basement rise = 7 m route × 2 pipes = **14 m**
- Do not price the multi-storey riser from the basement sheet

**Basement 300 mm tray**

Followed the hatch: 9.0 + 14.5 + 4.5 + 1.0 = 29.0 m plan + 15% = 33.5 m → tender **34 m**. One tray only.

**Basement condensate (not drawn, still required)**

10 indoor units × 6 m average to nearest drain = **60 m**. 32 mm PVC cassettes / 20–22 mm wall FCU, fall 1:100. Confirm on the drainage drawing.

**Ground floor refrigerant**

No cyan spine. Two riser nodes only.

Per riser: 4.0 m assumed GF storey height × 2 pipes = 8 m, plus 3.0 m × 2 pipes for isolation / future tenant tee = 6 m → **14 m** each → **28 m** both risers.

4.0 m storey height is an assumption. Lock it against the architect section before order. Do not add a horizontal main between west and east cores. Do not re-count the basement 14 m drop.

**Ground floor electric items** — no pipe, no condensate.

## 8. Diameters

| Service | On drawing | Used for tender |
|---|---|---|
| 300 mm tray | Printed | 300 mm |
| FCU F+R | Not printed | 22 mm OD copper pair, inferred from HBC ports |
| Kitchen FCU F+R if > 5.6 kW | Not printed | Flag 28 mm OD |
| Refrigerant to HBC / through GF riser | Not printed | ø15.88 / ø19.05–22.2 inferred |
| Condensate | Not drawn | 32 mm / 20–22 mm |

If it is not printed, the size column must say inferred.

## 9. Allowances that are not on the sheet but were taken

- 15% coordination on every scaled plan length
- 1.5 m tails per pipe at each FCU
- Condensate to all indoor units
- HBC drain 8 m, HBC water ancillaries 6 m + 1 set of valves / strainer / PRV / filling loop
- Electric heater duty 1.0–2.0 kW when no schedule
- Door curtain 1.0–1.5 m wide, 3–6 kW when no schedule

## 10. What was deliberately not taken

- Outdoor / condensing units (other drawings)
- Refrigerant riser through upper floors from the basement or GF sheet
- Tenant VRV indoor units and tenant pipe inside retail / office
- A second tray that is not hatched
- Leader lines used as pipe centre-lines
- Hotel bin-store containers as HVAC
- First Floor tab with no M-5601 drawing

## 11. Spreadsheet conventions used

Workbook name: `25280-SEN Heating and Cooling Inventory`  
One file. Tabs: `Basement`, `Ground Floor`, then `{Floor name}` for each later M-56xx sheet.

Columns: Item | Annotation / item | What it refers to | Count | Unit | Size (on drawing / inferred) | Tender estimate | Est. unit | Notes

Header states source drawing number, rev, scale rule, diameter caveat.

Headlines block repeats the commercial totals.

Caveats block repeats system ambiguity, do-not-fabricate, and the date of take-off.

Blue text = quantities. Amber fill = inferred.

No sterling rates unless the user asks. Tender estimate is quantity after allowances.

## 12. Checks before publishing a tab

- Every HVAC string on the PDF appears at least once on the tab
- Leader text count ≠ equipment count unless tags agree
- Sub-totals match the sum of routes
- Verticals are this storey only
- Exclusions listed so the next floor does not double-count the riser
- Tab lands in the single workbook, not a new Google Sheet
