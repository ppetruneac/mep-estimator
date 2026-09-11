# AC specifics — drawing to inventory tab

Everything used to convert Seneca heating-and-cooling layouts into a spreadsheet tab on Hub by Premier Inn Putney (25280). Read this with `SKILL.md`.

Calibrated through Basement, Ground Floor, Second–Ninth Floor and Roof Plant (11 Sep 2026).

## 1. Project and drawing family

| Field | Value |
|---|---|
| Project | Hub by Premier Inn Putney |
| Client | Mosser Ltd |
| Architect | Curio Architects |
| MEP | Seneca Group Ltd |
| Discipline sheets | `25280-SEN-{level}-DR-M-56xx` Heating and Cooling Layout |
| Stage / rev seen | Stage 4, Rev P1 (bedroom sheets dated 10.12.25; basement dated 20.01.26) |
| Plot | AutoCAD LT 2026 → PDF, A1, often page rot 270° |
| Scale on title block | `1:50@A1` |

### Sheets in the Drive folder `1neR-n1gdUHPirWpQ90je6Sw_Yq3mT5Ou`

| Level | Drawing | File ID used |
|---|---|---|
| Basement | `25280-SEN-0X-DR-M-560X` | `1coSxItFOYYjvE2d8bpNpUfbZsII-e5Rw` |
| Ground Floor | `25280-SEN-00-DR-M-5600` (filename sometimes `0X` / `5600`) | `1HpjzrsLIQSkyrGiVs-KiDBNZDZajYIWD` |
| First Floor | **Not in the set.** Do not invent M-5601. |
| Second | `25280-SEN-02-DR-M-5602` | `1T7RqYHFhg4LE2HCY-3g4moRSfLYtnMvA` |
| Third | `25280-SEN-03-DR-M-5603` | `1mQ2XteJbEoSXb0lx9lQbuD-OvtZTPIQE` |
| Fourth | `25280-SEN-04-DR-M-5604` | `13sd2MjQwD3Xs3Yx1LbwpzRn_NG-ZHg6h` |
| Fifth | `25280-SEN-05-DR-M-5605` | `1ZNNh9EZ-FVYPgbSytCxknDoQXfGP4P6z` |
| Sixth | `25280-SEN-06-DR-M-5606` | `1Buj5m3kkCAaa0ItuI_yXI1TxvRxK3ohK` |
| Seventh | `25280-SEN-07-DR-M-5607` | `1ymYpKAy0tgALLEB-sulD1KlEdvDvaDl6` |
| Eighth | `25280-SEN-08-DR-M-5608` | `1QBGik_i2Ts4zE_ov5JdGVzs6ITLoEU8A` |
| Ninth | `25280-SEN-09-DR-M-5609` | `1J6WLcbKWijAMC30ZtvpG1CNCRnvYNNhT` |
| Roof plant | `25287-SEN-00-DR-M-5150` Stage 4A (different job number on the filename) | `1v_5IwCOFyF3Z7TvPKP-l53hEbjv9oHWm` |

Title block always wins over the PDF filename.

## 2. What to read first (context)

From the title block and notes, not from the plan:

- Floor name and drawing number
- Scale and paper
- Revision / date / stage (`PRELIMINARY DESIGN` / Stage 4)
- Standard notes — `DO NOT SCALE`; positions approximate for tender; contractor produces coordinated working drawings; Seneca is not responsible for setting-out or manufacturing dimensions
- North point, disclaimer

From the plan, as context not as HVAC items:

- Room names and areas (`7.3 m²`, `152.7 m²`, guest-room numbers)
- Tenant vs hotel demise (retail units, office lobby, hotel lobby, biodiverse roof)
- Architectural riser rooms (`Riser 1.6 m²`, `Riser Lobby 2.1 / 2.3 m²`) vs MEP green take-off boxes
- Notes such as `Cycle space provision subject to tenant fit-out`

These rooms tell you what an FCU or heater is serving. They are not extra equipment.

## 3. How text was extracted

1. Drive OCR / `google_drive_read_file` is lossy and jumbled on rotated A1 plots. Do not inventory from that pass alone.
2. `pdftotext -layout` gives reading order for title block and notes.
3. `pdfplumber.extract_words()` gives `x0`, `top`, `text`. Use this to place annotations and to list every `FCU.xx.yy` / `HB:` tag.
4. `pdftoppm -png -r 72` on the PDF as stored (after rotation handling) so the raster matches plotted millimetres.
5. Crop the zones where HVAC words sit (west FCU, east FCU, tray, lobby, cores). Confirm the leader lands on a red bar, green box, cyan spine or hatch — not on empty floor.
6. Deduplicate tags. A tag printed twice next to one symbol is still one unit.
7. Colour BFS on cyan/green pixels returned too few pixels on these plots (thin hatch, anti-alias). Abandoned for length. Lengths on bedroom floors used tag-to-core geometry plus the two-core plate learned on Ground Floor.

Colour language used on these Seneca plots:

- **Cyan / light blue spine** — ceiling pipe distribution (basement F+R / refrigerant in ceiling)
- **Green box / green hatch** — riser take-off or tray
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

The two cores on this sheet are the plate used later for 2F–9F average plan runs when a pixel trace is not available.

### Bedroom floors (`M-5602` … `M-5609`) — what was found

Same annotation family on every bedroom sheet. Counts change with the plate.

| Printed annotation | What it actually referred to | Count basis |
|---|---|---|
| `WALL MOUNTED INTERNAL VRF UNITS` | Typical-detail, printed more than once along the corridor | Count from `FCU.{ff}.{nn}` tags, one per guest room |
| `FCU.02.01` … `FCU.09.09` | Individual wall VRF | Sequence per floor. Look for holes (see §13) |
| `HBC CONTROLLER` / `HB:{ff}:01` / `HB:{ff}:02` | Branch controllers at the riser cores | 2 on 2F–7F, 1 on 8F and 9F |
| `REFRIGERANT FROM HBC TO ROOMS` | Corridor home-runs from the HBC to the wall units | Same family as basement F+R. Two pipes per unit. **0 extra metres** beyond the home-run take-off |
| `REFRIGERANT FROM OUTDOOR UNIT TO HBC` / `SYSTEM NO 1 refrigeration from above` | Local drop from the floor riser into the HBC boxes **this storey only** | 12 m tender per HBC box (connection, not the multi-storey stack) |
| `REFRIGERANT PIPEWORK ON 400MM WIDE TRAY IN CEILING` | Printed several times along the corridor | **One tray**, 400 mm — only services size printed on 2F–9F |
| `7NO systems` / system notes on 8F and 9F | Building-wide hotel-room outdoor systems | Source of the **7-system** passing-riser rule |

No electric panel heaters on the bedroom floors that were read.

### Roof (`M-5150`) — what was found

| Printed annotation | What it actually referred to | Count basis |
|---|---|---|
| Hotel-room outdoor plant / `HOTEL ROOMS REFRIGERANT PIPEWORK TO BELOW` | Seven hotel-room VRF/HVRF systems leaving the roof into the hotel riser | **7 systems** — matches 8F/9F notes |
| `BOH & F&B REFRIGERANT PIPEWORK TO BELOW` | BOH/F&B outdoor unit into the riser | 1 route |
| `RISER RETAIL/OFFICES REFRIGERANT PIPEWORK TO BELOW` | Printed twice, same tenant riser as Ground Floor | 1 riser, two leaders |
| `AHU:01` / `AHU:02` / `AHU:03` | Roof AHUs (rooms, BOH/F&B, packed). AHU:01 may be double-stacked | 3 |
| ASHP + `2500 L` calorifiers | DHW plant | 1 ASHP + 2 × 2500 L (capacity **is** printed) |
| Duct leaders with `400 × 400`, `FB & TLL` etc. | Roof-deck duct laterals only | Use the printed size; do not invent shaft length |
| `BCWS TO ASHP SYSTEM` / `HWS F&R T/B BASEMENT & PLANTROOM` | Roof-deck water laterals | This deck only |

Do not copy bedroom FCU/HBC rows onto the roof tab.

## 5. Inventory items (what goes on the tab)

Always include, even when count is zero:

- Indoor units (cassette / wall / ducted) with tag and room
- Controllers (HBC / BC / REFNET) with tag
- Electric heaters and door curtains
- Drawn pipe (F+R or refrigerant) per route and as a sub-total
- Drawn tray
- Drawn risers (hotel vs tenant)
- Pipe the specification requires but the sheet omitted (condensate, HBC drain, filling loop)
- Passing systems through this storey (bedroom floors)
- Explicit exclusions (tenant indoor units, outdoor plant, riser above this floor)

Do not inventory bins, cycle spaces or retractable gates as HVAC. Record them once under exclusions if the user said keep all drawing text.

## 6. System reading (Putney)

Two signals on the basement sheet:

1. Tag `HBC CONTROLLER HB:0B:01` → Mitsubishi City Multi **Hybrid VRF**. Refrigerant outdoor → HBC. **Water** flow and return HBC → indoor units.
2. Printed `REFRIGERANT PIPEWORK IN CEILING` → could be read as refrigerant VRV all the way to FCUs.

Upper-floor sheets print `WALL MOUNTED INTERNAL VRF` and `REFRIGERANT FROM HBC TO ROOMS` more strongly than the basement water reading.

Action used: keep the **same pair lengths**; flag the material. Do not buy both water copper and refrigerant copper for the same run. Confirm against the Seneca specification before order.

Mitsubishi HBC points used when the drawing was silent:

- Indoor water ports typically **22 mm OD**
- Indoor capacity above ~5.6 kW may need larger field pipe (step toward 28 mm OD / 20 mm+ ID)
- Max HBC-to-indoor run in the product literature ~**60 m** (basement longest plan run was FCU.B.10 at 21 m — inside limit)
- Water design pressure at HBC 0.6 MPa; field pipe min 1.0 MPa
- HBC needs drain / overflow, isolation, air vents, drain cock, filling loop, strainer, PRV, expansion vessel (usually field-supply)

Kitchen `FCU.B.01` / `FCU.B.03` in 43.3 m² kitchen — load may exceed 5.6 kW. Amber flag for upsize.

Indoor VRF pair on bedroom wall units (if the spec is refrigerant, not Hybrid water) inferred **ø6.4 / ø9.5 mm** pending the indoor schedule.

Refrigerant pair into the HBC (outdoor not on the floor sheet) inferred **ø15.88 mm** liquid/HP and **ø19.05–22.2 mm** gas/LP for an 8–12 HP outdoor. Not printed.

Ground floor has no FCUs — 22 mm water does not apply there.

## 7. Scale and how lengths were measured

### Conversion

- Title block `1:50 @ A1`
- 1 cm on the A1 plot = **0.50 m** on site
- 1 m on site = 2 cm on the A1 plot
- Raster at 72 dpi → 0.3528 mm/px → at 1:50 → **0.01764 m/px**

Basement page after render used for measuring: 2384 × 1684 px (A1 landscape at 72 dpi).

### Formula

```
tender_m = plan_m * 2 * 1.15 + 1.5 * 2
```

- `2` = flow and return (or liquid and gas if the spec is refrigerant)
- `1.15` = 15% coordination on a Stage 4 intent drawing that says positions are approximate
- `1.5 m` per pipe = drop, isolation and connection at the FCU (3.0 m pair tails)

### Basement F+R (each FCU to HBC along the cyan spine, not crow-flies)

| Unit | Plan route | Tender F+R |
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

**Basement refrigerant (this floor only)** — `FROM ABOVE TO CEILING`: ~3 m horizontal HBC to shaft + ~4 m basement rise = 7 m route × 2 pipes = **14 m**. Do not price the multi-storey riser from the basement sheet.

**Basement 300 mm tray** — followed the hatch: 9.0 + 14.5 + 4.5 + 1.0 = 29.0 m plan + 15% = 33.5 m → tender **34 m**. One tray only.

**Basement condensate (not drawn, still required)** — 10 indoor units × 6 m average to nearest drain = **60 m**. 32 mm PVC cassettes / 20–22 mm wall FCU, fall 1:100.

**Ground floor refrigerant** — no cyan spine. Two riser nodes only. Per riser: 4.0 m assumed GF storey height × 2 pipes = 8 m, plus 3.0 m × 2 pipes for isolation / future tenant tee = 6 m → **14 m** each → **28 m** both risers. 4.0 m storey height is an assumption.

Do not add a horizontal main between west and east cores. Do not re-count the basement 14 m drop.

**Ground floor electric items** — no pipe, no condensate.

### Bedroom floors — geometry estimate (pixel trace not reliable)

Average plan from the wall unit to the nearest of the two cores, then the standard formula.

| Floor | Wall VRF | HBC | Avg plan used | HBC→room tender | 400 mm tray plan+15% | ODU→HBC this storey | Passing 7 systems |
|---|---|---|---|---|---|---|---|
| 2F–5F each | 31 | 2 | ~12 m | **875 m** | **60 m** | 24 m (2 boxes) | 56 m |
| 6F | 26 (allow 27) | 2 | slightly shorter plate | **676 m** | **46 m** | 24 m | 56 m |
| 7F | 24 (allow 25) | 2 | shorter plate | **596 m** | **41 m** | 24 m | 56 m |
| 8F | 15 | 1 | shorter plate | **342 m** | **32 m** | 12 m | 56 m |
| 9F | 9 | 1 | 8.0 m avg | **196 m** | **18 m** | 12 m | 14 m (System 7 only on this plate) |

Passing metreage: `7 systems × 2 pipes × 4.0 m storey = 56 m` on 2F–8F. Ninth floor note is the source of the 7-system building count; do not also multiply 56 m by 7 on the roof.

Bedroom condensate (not drawn): **5 m × unit count** (shorter rooms than basement). 20–22 mm, fall 1:100.

### Roof laterals only

| Route | Basis | Tender |
|---|---|---|
| Hotel-room refrigerant on the roof deck | 7 systems to the riser, laterals only | **161 m** |
| BOH/F&B refrigerant to below | 12 m plan × 2 × 1.15 | **28 m** |
| Retail/office refrigerant to below | 10 m plan × 2 × 1.15 | **23 m** |
| Printed duct laterals B01–B08 | printed sizes | **54 m** |
| BCWS to ASHP | roof deck | **15 m** |
| HWS F+R T/B | 15 m plan × 2 × 1.15 + tails | **40 m** |

If you need a single full-height hotel riser take-off instead of the per-floor passing rows: `7 systems × 2 pipes × rise`. Do not add that figure on top of S07 + roof 161 m.

## 8. Diameters

| Service | On drawing | Used for tender |
|---|---|---|
| 300 mm tray (basement) | Printed | 300 mm |
| 400 mm tray (2F–9F) | Printed | 400 mm |
| Roof ducts | Some sizes printed (`400 × 400`, FB & TLL) | Use printed |
| 2500 L calorifiers | Printed | 2500 L |
| FCU F+R (basement, if Hybrid water) | Not printed | 22 mm OD copper pair, inferred from HBC ports |
| Kitchen FCU F+R if > 5.6 kW | Not printed | Flag 28 mm OD |
| Bedroom indoor VRF pair | Not printed | ø6.4 / ø9.5 mm pending schedule |
| Refrigerant to HBC / through riser | Not printed | ø15.88 / ø19.05–22.2 inferred |
| Condensate | Not drawn | 32 mm cassettes / 20–22 mm wall |

If it is not printed, the size column must say inferred.

## 9. Allowances that are not on the sheet but were taken

- 15% coordination on every scaled plan length
- 1.5 m tails per pipe at each FCU
- Condensate to all indoor units
- HBC drain 8 m, HBC water ancillaries 6 m + 1 set of valves / strainer / PRV / filling loop (skip water ancillaries if the spec is refrigerant VRF)
- Electric heater duty 1.0–2.0 kW when no schedule
- Door curtain 1.0–1.5 m wide, 3–6 kW when no schedule
- +1 FCU allowance on 6F and 7F where tag `FCU.06.16` / `FCU.07.21` may exist
- 4.0 m storey height until the architect section is locked

## 10. What was deliberately not taken

- Outdoor / condensing units on floor sheets (price on Roof Plant)
- Refrigerant riser through upper floors from the basement or GF sheet
- The same 7-system stack priced three ways (per-floor passing + roof laterals + a third full-height total)
- Tenant VRV indoor units and tenant pipe inside retail / office
- A second tray that is not hatched
- Leader lines used as pipe centre-lines
- Hotel bin-store containers as HVAC
- First Floor tab with no M-5601 drawing
- Bedroom FCU rows copied onto the roof tab

## 11. Spreadsheet conventions used

Workbook name: `25280-SEN Heating and Cooling Inventory` (complete local copy `25280-SEN Heating and Cooling Inventory - All Floors.xlsx`)

One file. Tabs: `Summary`, `Basement`, `Ground Floor`, `Second Floor` … `Ninth Floor`, `Roof Plant`.

Live Google Sheet `18I4tEO1nvDH4V83tHhEsKRLiKu1I4Jmbd1pUaZA0DJY` received Basement + Ground Floor only. The Drive connector available to the agent could search/read/list/trash. It could not append a tab or upload a file. If that is still true, write the local `.xlsx` and say the Sheet was not updated.

Columns: Item | Annotation / item | What it refers to | Count | Unit | Size (on drawing / inferred) | Tender estimate | Est. unit | Notes

Header states source drawing number, rev, scale rule, diameter caveat.

Headlines block repeats the commercial totals.

Caveats block repeats system ambiguity, do-not-fabricate, tag gaps, storey-height assumption, and the date of take-off.

Blue text = quantities. Amber fill = inferred.

No sterling rates unless the user asks. Tender estimate is quantity after allowances.

## 12. Checks before publishing a tab

- Every HVAC string on the PDF appears at least once on the tab
- Leader text count ≠ equipment count unless tags agree
- Tag sequence has no silent hole — or the hole is called out (`allow +1`)
- Sub-totals match the sum of routes
- Verticals are this storey only
- Exclusions listed so the next floor does not double-count the riser
- Tray size matches what that sheet printed (300 mm vs 400 mm)
- Roof tab does not repeat bedroom FCU counts
- Summary tab flags which metres must not be added together
- Tab lands in the single workbook, not a new Google Sheet

## 13. Bedroom-floor counts locked on this set

| Floor | FCU tags read | Allow | HBC |
|---|---|---|---|
| 2F | 31 | 31 | 2 |
| 3F | 31 | 31 | 2 |
| 4F | 31 | 31 | 2 |
| 5F | 31 | 31 | 2 |
| 6F | 26 | 27 if `FCU.06.16` exists | 2 |
| 7F | 24 | 25 if `FCU.07.21` exists | 2 |
| 8F | 15 | 15 | 1 |
| 9F | 9 | 9 | 1 |
| **2F–9F** | **198** | **200** | **14** |

Building-wide hotel indoor controllers: 14 (2F–9F) + basement `HB:0B:01` = **15**.

Building-wide hotel-room outdoor systems: **7** (9F note + roof).

## 14. Building totals that must not be double-counted

| Code | Item | Tender | Note |
|---|---|---|---|
| S03 | Bedroom wall VRF 2F–9F | 198 no. | Allow +2 |
| S04 | HBC 2F–9F | 14 no. | +1 basement |
| S05 | HBC→room pair 2F–9F | ~5310–5424 m | Dominant pipe quantity |
| S06 | 400 mm tray 2F–9F | ~377–382 m | Plus basement 300 mm tray 34 m |
| S07 | Passing systems 2F–9F if summed | 406 m | = 7 systems × 2 pipes × ~32 m rise. Do not add roof 161 m as a third copy of the same stack |
| S08 | Hotel-room outdoor systems | 7 no. | Roof |
| S09 | AHUs | 3 no. | Roof |
| S10 | DHW plant | 1 ASHP + 2 × 2500 L | Roof |
| S11 | Bedroom condensate 2F–9F | 990 m | 5 m × 198 |

## 15. Validation lessons from this job

1. Typical-detail leaders are not units. User asked where `CEILING MOUNTED CASSETTE FCU'S` was found — twice, both call-outs.
2. Filename `0X` / `560X` is not the floor. Title block is.
3. Missing First Floor is a missing drawing, not a missing tab to invent.
4. Three Google Spreadsheets in one folder is an error state. Consolidate to one book.
5. Colour-trace lengths looked precise and were wrong. Geometry + formula beat BFS on thin CAD hatch.
6. 8F/9F system notes are the only printed building-wide system count. Use them for passing risers on every bedroom floor.
7. Roof drawing number `25287` is still this building. Do not drop it because the prefix changed.
8. If Drive write is blocked, say the file is local. Listing the folder is the proof, not the project `artifacts/` path.
