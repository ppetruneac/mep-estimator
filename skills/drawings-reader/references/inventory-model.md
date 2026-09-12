# Inventory model — IDs, master tab, CSV / Excel

Generic book structure for drawing take-offs. Do not put project quantities here.

## 1. Two layers

| Layer | What it holds | Rule |
|---|---|---|
| Per-drawing tab | Everything found on that sheet (in-scope priced + off-premise exclusions) | One tab per title-block floor / plant |
| Master tab | Union of every priced item ID across the book | One row per ID. Building qty is the sum of unique contributions only |

A third Rates tab (optional) holds unit rates. Floor money columns look up rates by `rate_key`. Do not type sterling on the floor if a rates tab exists.

## 2. Item ID

Stable, human-readable, unique in the book.

```
{discipline}-{family}-{token}
```

Examples (patterns, not project stock):

| ID | Meaning |
|---|---|
| HC-FCU-WALL | Wall VRF / wall FCU |
| HC-FCU-CASS | Cassette FCU |
| HC-HBC | Heat / branch controller |
| HC-ODU | Outdoor VRV module |
| HC-CU-IN | Indoor refrigerant or F+R pair (home-run) |
| HC-CU-RISER | This-storey drop / passing pair |
| HC-CU-ROOF | Plant-deck refrigerant lateral |
| HC-TRAY-400 | 400 mm services tray |
| HC-TRAY-300 | 300 mm services tray |
| HC-COND | FCU condensate (specified, often not drawn) |
| HC-LAG-S | Lagging small diameter |
| HC-LAG-L | Lagging large diameter |
| HC-STAT | Room controller per FCU |
| HC-ELEC-PNL | Electric panel heater |
| HC-ELEC-CUR | Over-door curtain |
| VT-AHU | Air handling unit (ventilation — off H&C premise) |
| PH-ASHP-DHW | DHW plant (public health — off H&C premise) |

Rules:

- Same physical thing keeps the same ID on every floor (`HC-FCU-WALL` on 2F and 5F).
- Floor is a column on Master, not part of the ID.
- Off-premise items still get an ID so they can be filtered (`in_scope = FALSE`).
- Never reuse an ID for two materials (do not put lagging on `HC-CU-IN`).

Local row codes on a floor tab (`A01`, `B01`) are sheet line numbers. They may change when rows are inserted. The Master ID does not.

## 3. Per-drawing tab columns

Keep this order unless the live book already differs — then match the live book.

1. Line (`A01` …)
2. Item ID (Master ID)
3. Annotation / item (printed text)
4. What it refers to / linked to
5. Count
6. Unit
7. Size (printed / inferred)
8. Tender estimate
9. Est. unit
10. Measurement type (`printed` / `scaled` / `geometry` / `vertical` / `specified-not-drawn` / `excluded`)
11. Scope (`in` / `interface` / `out`)
12. Rate key
13. Notes

Header block (rows 1-6): project, source drawing number, rev, scale rule, premise, diameter caveat.

Section bands: terminals, pipe, tray, specified-not-drawn, exclusions, headlines.

- Blue numbers = inputs.
- Amber fill = inferred size or length.
- Headlines are roll-ups of lines already above. Do not price a headline and the detail.

Floor total SUM of money columns must stop on the last detail row. Including the total row is a circular reference.

## 4. Master tab

Name the sheet `Master`.

| Column | Content |
|---|---|
| item_id | ID from section 2 |
| family | FCU / HBC / ODU / CU / TRAY / COND / LAG / STAT / ELEC / EXCL |
| description | Short commercial name |
| unit | no. / m / kit / lot |
| scope | in / out |
| premise | heating-cooling / ventilation / PH / electrical |
| rate_key | Lookup into Rates |
| qty_{tab} | One column per drawing tab |
| qty_building | Formula: sum of unique columns only |
| unique_or_shared | unique (sum freely) or interface (do not sum with the paired tab) |
| source_drawings | Drawing numbers that contributed |
| measurement_type | Dominant type |
| notes | Double-count warning |

Building qty rules:

- Terminals, heaters, stats, lagging, clips — unique. Sum floors.
- This-storey passing riser — unique per storey. Summing floors is correct (each storey is another rise).
- Full-height riser written on a plant tab — interface. Do not add it to the sum of passing rows.
- Roof laterals — unique to the plant tab. Do not add floor home-runs into them.
- Exclusions — qty_building = 0 on this book.

When a drawing is missing and the user orders an interpolated tab, mark `source_drawings` as interpolated from the source plates and keep the same IDs.

## 5. Writing CSV / Excel

### During extraction

Write a working CSV per drawing first (easy to diff):

```
inventory_csv/{drawing-number}.csv
```

Same columns as section 3. UTF-8. No merged cells. Amber / scope as plain text.

Then assemble the workbook:

- One sheet per drawing, named from the title block (`Basement`, `Second Floor`, `Roof Plant`).
- `Master` plus optional `Rates`, `Labour`, `Summary`.
- Floor money = qty x VLOOKUP(rate_key). Labour = hours x named hourly rate.
- Every lookup wrapped in IFERROR(...,0). Lookups reference **this row**. After deleting rows, rewrite formulas — leftover J14 on row 12 is how N/A and trace-arrows appear.
- Named ranges for rates so floors do not hard-code sterling.

### Cloud vs local

1. Prefer one named spreadsheet.
2. If the connector cannot append a tab, write the full local `.xlsx` and say so.
3. Never upload a second cloud file just for the next floor.

### Checks after write

- Recalculate. Zero REF / N/A / VALUE / DIV0 / NAME errors.
- Master qty_{tab} matches that tab tender column for the same ID.
- Summary / Price sheets point at the real total cell, not the row below it.

## 6. Summary / headlines

Headlines at the **bottom** of each drawing tab are a commercial digest of that sheet only.

Building Summary lists each ID once with qty_building from Master. It is not a paste of every floor headline (that would triple-count passing risers and roof laterals).
