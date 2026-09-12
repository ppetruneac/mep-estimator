# Inventory model — IDs, master tab, CSV / Excel

Generic book structure for drawing take-offs. Do not put project quantities here.

## 1. Two layers

| Layer | What it holds | Rule |
|---|---|---|
| Per-drawing tab | Everything found on that sheet (in-scope priced + off-premise exclusions) | One tab per title-block floor / plant. Rows grouped by category |
| Master / Summary | Union of every item ID across the book | One row per ID, sorted by category then item_id. Building qty is the sum of unique contributions only. Required as soon as two drawing tabs exist |

A Rates tab (optional) holds unit rates. Floor money columns look up rates by `rate_key`. Do not type sterling on the floor if a rates tab exists.

`Master` is the register. `Summary` is the readable building view of the same IDs. They may be one sheet if the book is small. If they are two sheets, they share the same item_id list and the same category names.

## 2. Item ID and category

Stable, human-readable, unique in the book.

```
{discipline}-{family}-{token}
```

| ID | Category | Meaning |
|---|---|---|
| HC-FCU-WALL | Indoor terminals | Wall VRF / wall FCU |
| HC-FCU-CASS | Indoor terminals | Cassette FCU |
| HC-HBC | Controllers | Heat / branch controller |
| HC-ODU | Outdoor / plant | Outdoor VRV module |
| HC-CU-IN | Refrigerant / F+R pipe | Indoor pair (home-run) |
| HC-CU-RISER | Refrigerant / F+R pipe | This-storey drop / passing pair |
| HC-CU-ROOF | Refrigerant / F+R pipe | Plant-deck refrigerant lateral |
| HC-TRAY-400 | Tray / containment | 400 mm services tray |
| HC-TRAY-300 | Tray / containment | 300 mm services tray |
| HC-COND | Condensate | FCU condensate (specified, often not drawn) |
| HC-LAG-S | Lagging | Lagging small diameter |
| HC-LAG-L | Lagging | Lagging large diameter |
| HC-STAT | Controls / stats | Room controller per FCU |
| HC-ELEC-PNL | Electric heat | Electric panel heater |
| HC-ELEC-CUR | Electric heat | Over-door curtain |
| VT-AHU | Exclusions / interfaces | Air handling unit (ventilation) |
| PH-ASHP-DHW | Exclusions / interfaces | DHW plant (public health) |

Rules:

- Same physical thing keeps the same ID and the same category on every floor.
- Floor is a column on Master / Summary, not part of the ID.
- Category names are shared across floor tabs and Summary. Do not rename a category on Summary only.
- Off-premise items still get an ID so they can be filtered (`scope = out`). Put them under Exclusions / interfaces.
- Never reuse an ID for two materials (do not put lagging on `HC-CU-IN`).

Local row codes on a floor tab (`A01`, `B01`) are sheet line numbers. They may change when rows are inserted. The item ID does not.

## 3. Per-drawing tab columns

Keep this order unless the live book already differs — then match the live book.

1. Line (`A01` …)
2. Category
3. Item ID (Master ID)
4. Annotation / item (printed text)
5. What it refers to / linked to
6. Count
7. Unit
8. Size (printed / inferred)
9. Tender estimate
10. Est. unit
11. Measurement type (`printed` / `scaled` / `geometry` / `vertical` / `specified-not-drawn` / `excluded`)
12. Scope (`in` / `interface` / `out`)
13. Rate key
14. Notes

Header block (rows 1-6): project, source drawing number, rev, scale rule, premise, diameter caveat.

Layout:

- One coloured **section-band row** per category, then the items in that category.
- Sort inside a category by item_id.
- Turn on AutoFilter on the header row (not on a data row).
- Optional Excel outline / group per category so the sheet collapses.
- Headlines after all categories, at the bottom of the tab.
- Floor total SUM of money columns must stop on the last detail row. Including the total row is a circular reference.

Blue numbers = inputs. Amber fill = inferred size or length. Headlines are roll-ups of lines already above. Do not price a headline and the detail.

## 4. Master tab

Name the sheet `Master`.

| Column | Content |
|---|---|
| category | Same name as the floor-tab section |
| item_id | ID from section 2 |
| family | FCU / HBC / ODU / CU / TRAY / COND / LAG / STAT / ELEC / EXCL |
| description | Short commercial name |
| unit | no. / m / kit / lot |
| scope | in / out |
| premise | heating-cooling / ventilation / PH / electrical |
| rate_key | Lookup into Rates |
| qty_{tab} | One column per drawing tab |
| qty_building | Formula: sum of unique columns only |
| where_found | Tab name + drawing number for every tab where qty > 0 |
| unique_or_shared | unique (sum freely) or interface (do not sum with the paired tab) |
| source_drawings | Drawing numbers that contributed |
| measurement_type | Dominant type |
| notes | Double-count warning |

Sort Master by category, then item_id. AutoFilter on. Optional outline groups per category.

`where_found` format (required, human readable):

```
Basement (25280-SEN-0X-DR-M-560X); Ground Floor (25280-SEN-00-DR-M-5600); Roof Plant (25287-SEN-00-DR-M-5150)
```

- List only tabs where the tender qty for that ID is greater than zero.
- Use the sheet tab name first, drawing number in brackets.
- Semicolon-separated. Do not write "all floors" unless every drawing tab actually has qty > 0.
- Rebuild this string after each new drawing tab, not by hand memory.

Building qty rules:

- Terminals, heaters, stats, lagging, clips — unique. Sum floors.
- This-storey passing riser — unique per storey. Summing floors is correct (each storey is another rise).
- Full-height riser written on a plant tab — interface. Do not add it to the sum of passing rows.
- Roof laterals — unique to the plant tab. Do not add floor home-runs into them.
- Exclusions — qty_building = 0 on this book. Still list `where_found` so the reader can see the item was noticed.

When a drawing is missing and the user orders an interpolated tab, mark `where_found` as `First Floor (interpolated from Second-Fifth)` and keep the same IDs and category.

## 5. Writing CSV / Excel

### During extraction

Write a working CSV per drawing first (easy to diff):

```
inventory_csv/{drawing-number}.csv
```

Same columns as section 3, including `category`. UTF-8. No merged cells. Amber / scope as plain text.

Then assemble the workbook:

- One sheet per drawing, named from the title block (`Basement`, `Second Floor`, `Roof Plant`).
- `Master` and `Summary` plus optional `Rates`, `Labour`.
- Floor money = qty x VLOOKUP(rate_key). Labour = hours x named hourly rate.
- Every lookup wrapped in IFERROR(...,0). Lookups reference **this row**. After deleting rows, rewrite formulas.
- Named ranges for rates so floors do not hard-code sterling.
- AutoFilter on the real header row. Group rows by category (Excel Data > Group, or a section-band row).

### Cloud vs local

1. Prefer one named spreadsheet.
2. If the connector cannot append a tab, write the full local `.xlsx` and say so.
3. Never upload a second cloud file just for the next floor.

### Checks after write

- Recalculate. Zero REF / N/A / VALUE / DIV0 / NAME errors.
- Master qty_{tab} matches that tab tender column for the same ID.
- Category of an ID is identical on the floor tab, Master and Summary.
- Summary / Price sheets point at the real total cell, not the row below it.
- Every Master / Summary row has a non-empty `where_found` if qty_building > 0, or if scope = out.

## 6. Summary tab (cross-drawing)

Required as soon as the book has more than one drawing tab.

Headlines at the **bottom** of each drawing tab stay as a commercial digest of that sheet only.

Building Summary is keyed by item ID and **grouped by category**:

| Column | Required |
|---|---|
| category | yes |
| item_id | yes |
| description | yes |
| unit | yes |
| qty_building | yes |
| where_found | yes |
| scope | yes |
| qty per drawing tab | optional |

Rules:

- Sort category, then item_id. Same category names as the floor tabs.
- One row per item ID. Never one row per floor line.
- Optional category subtotal row (count / metres only, not a second priced headline).
- `where_found` must name every tab that holds that ID with qty > 0.
- AutoFilter on. Optional outline / group per category so Summary collapses the same way as a floor tab.
- Do not paste floor headline blocks into Summary. That triple-counts passing risers and plant laterals.
- Rebuild Summary after the last drawing is written, and again after any qty edit.
