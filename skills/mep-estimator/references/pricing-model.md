# Pricing model — rates, labour units, formulas

Generic commercial overlay on a drawings-reader book. No project quantities here.

## 1. Material Rates tab

Name the sheet Material Rates. This is the only unit-rate book.

| Column | Content |
|---|---|
| item_id | Same ID as inventory |
| rate_key | Optional alias. If used, it must map 1:1 to item_id |
| category | Same category name as Summary |
| description | Short commercial name |
| unit | no. / m / kit / lot / kg |
| spec_source | clause / drawing note / assumed |
| product_assumption | Named comparable when spec is silent |
| avg_gbp | Average market unit rate (input, yellow) |
| prem_gbp | Best-in-class unit rate (input, yellow) |
| notes | Diameter family, exclusions |

Rules:

- Avg and best-in-class are two columns. Never two Material Rates tabs.
- Yellow on avg_gbp and prem_gbp only. All other money on the book is a formula.
- Named range MaterialRates covers the rate table. Document which column index is avg and which is prem.
- One row per item ID. Do not put a floor-specific rate against a building ID.
- Off-premise IDs may sit on the table with rates filled so a later premise change is easy, but Summary extensions stay 0 while qty is 0.

## 2. Drawing-tab material columns

Append on the right of the inventory columns. Match the live book if it already has a pattern.

| Column | Formula pattern |
|---|---|
| unit rate avg | IFERROR(VLOOKUP(item_id_cell, MaterialRates, avg_index, FALSE),0) |
| unit rate prem | IFERROR(VLOOKUP(item_id_cell, MaterialRates, prem_index, FALSE),0) |
| Material avg | N(tender_qty_cell)*N(unit_avg_cell) |
| Material prem | N(tender_qty_cell)*N(unit_prem_cell) |

- item_id_cell and tender_qty_cell are on this row.
- Section-band rows and headline rows: 0, not a lookup to a blank key.
- Exclusion rows (scope = out): lookup may run, extension stays 0 because qty is 0.
- Floor total material = SUM of the extension column from first item row to the row above the total.

Labour money does not belong on these columns unless the user asks for a combined line.

## 3. Labour tab

Name the sheet Labour.

### 3.1 Rate inputs (yellow)

| Work category | Unit of work | Hours per unit (input) | pounds per hour (input) |
|---|---|---|---|
| F-Gas / refrigerant install | indoor / outdoor / joint | from method | charge-out |
| Pipework / tray / condensate | m | from method | charge-out |
| Insulation | m | from method | charge-out |
| Controls / first-fix electrics | point | from method | charge-out |
| Commissioning | system or outdoor | from method | charge-out |

Charge-out is what the client is billed, not take-home pay. State region and date on row 1.

Optional on-cost percent (yellow). If used, labour = productive hours x rate x (1+on-cost). Default the on-cost in a single cell so one edit moves the book.

### 3.2 Hours from inventory

Hours are formulas on inventory quantities, not typed lumps.

| Work category | Hours driver |
|---|---|
| F-Gas install | qty(HC-FCU-*) x h_per_indoor + qty(HC-ODU) x h_per_outdoor |
| Pipework / tray | qty_m(HC-CU-* + HC-TRAY-* + HC-COND) x h_per_m |
| Insulation | qty_m(HC-LAG-*) x h_per_m |
| Controls electrics | qty(HC-STAT) x h_per_point |
| Commissioning | qty(HC-ODU or systems) x h_per_system |

Put hours-per-unit in yellow cells next to the hourly rate so both are editable.

### 3.3 Floor split (optional)

If Price Summary needs labour by drawing:

hours_floor = hours_building * (floor_qty / building_qty) for that driver.

Do not invent a second set of hourly rates per floor.

## 4. Summary extension

Inventory Summary already has category, item_id, qty_building, where_found.

Add four formula columns as in section 2, looking up item_id.

Category subtotal rows use SUMIF on the category column. Do not type the subtotal.

## 5. Price Summary

Name the sheet Price Summary.

Block A — materials by drawing (each row a formula to that sheet material total).

Block B — materials by category (SUMIF on Summary).

Block C — labour by work category (formulas to Labour).

Block D — building totals: materials avg, materials prem, labour, avg+labour, prem+labour.

Face notes: currency, rate date, ex-VAT, excluded prelims / crane / VAT / design / builderswork.

## 6. Formula hygiene

- No REF / N/A / VALUE / DIV0 / NAME errors.
- IFERROR on every lookup. N() on every qty x rate.
- Named rates for labour hourly cells so a later floor hours column can stay formula-only.
- After deleting inventory rows, rewrite drawing-tab lookups.
- Total SUM ranges stop on the last item row.

## 7. Checks before publishing

- Every in-scope item ID on Summary has a Material Rates row.
- Changing one yellow rate cell moves Summary and Price Summary.
- Drawing-tab unit-rate cells are formulas, not numbers.
- Off-premise IDs contribute zero money.
- where_found still matches qty > 0 after pricing.
- Recalculate the workbook and record zero formula errors.
