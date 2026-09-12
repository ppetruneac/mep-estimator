---
name: mep-estimator
description: Price an MEP inventory produced by drawings-reader. Build a Material Rates tab and a Labour tab by work category, extend the inventory Summary with material money, and join unit rates onto every drawing tab by item ID using formulas. Use when the user asks for a tender, unit rates, material cost, labour cost, priced inventory, or a building cost summary from HVAC or MEP take-off tabs.
metadata:
  type: workflow
  version: "1.0"
  domain: mep-commercial
  extends: drawings-reader
---

# MEP estimator

Price the book that `drawings-reader` already built. Do not invent a second inventory. Do not type unit rates onto floor tabs.

Inventory structure, item IDs, categories, Master / Summary and `where_found` live in `../drawings-reader/references/inventory-model.md`. Rate tables, labour units and formula patterns live in `references/pricing-model.md`. How to pick a rate when the spec is silent lives in `references/rate-sources.md`.

## When this skill starts

1. Confirm one workbook exists with one tab per drawing plus Master / Summary keyed by item ID.
2. If that book does not exist, run `drawings-reader` first. Do not price from OCR notes.
3. Confirm every priced line has an item ID and a category. If a line has no ID, stop and fix the inventory.

## Tabs this skill owns

| Tab | Role |
|---|---|
| Material Rates | Only place unit pounds live. One row per rate_key / item ID. Avg and best-in-class are columns, not two tabs. |
| Labour | Only place labour productivity and pounds-per-hour live. Rows are **work categories**, not floors. |
| Summary | Inventory Summary extended with material money looked up from Material Rates. Keep where_found. Group by category. |
| Price Summary | Building commercial view. Materials + labour by category and by drawing. Totals only. |

Drawing tabs stay owned by `drawings-reader`. This skill only adds formula columns on them.

## Working order

1. Read the specification pack and the drawing notes. Lock brand / material / diameter where the spec states them.
2. Build **Material Rates**. One row per item ID (or a stable rate_key that maps 1:1 to an ID). Two unit-rate columns: average market, best-in-class.
3. Build **Labour**. One row per work category. Inputs: unit of work, hours per unit, pounds per hour. Category total is a formula.
4. Extend **Summary**. Same item IDs as inventory. Add unit-rate lookups and material extension pounds. Do not paste numbers.
5. On every drawing tab add material columns only: unit rate avg, unit rate prem, material avg, material prem. All four are formulas against Material Rates joined by item ID.
6. Build **Price Summary**. Materials from Summary. Labour from the Labour tab (hours x rate by category, rolled to floors if hours exist). State what is excluded (prelims, crane, VAT, design).
7. Recalculate. Zero formula errors. Floor total SUM stops above the total row.

## Join rule (non-negotiable)

Never copy a unit rate from Material Rates onto a drawing tab or onto Summary.

```
unit_rate_avg  = IFERROR(VLOOKUP(item_id, MaterialRates, avg_col, FALSE), 0)
unit_rate_prem = IFERROR(VLOOKUP(item_id, MaterialRates, prem_col, FALSE), 0)
material_avg   = N(tender_qty) * N(unit_rate_avg)
material_prem  = N(tender_qty) * N(unit_rate_prem)
```

- Lookup key = item ID from drawings-reader (or the rate_key that equals that ID).
- Lookups reference **this row**. After row inserts or deletes, rewrite formulas.
- Wrap with IFERROR(...,0). Return 0, never blank text, so SUM does not throw VALUE errors.
- Named range MaterialRates covers the whole rate table. Edit rates only inside that sheet.

Drawing tabs do **not** carry labour pounds unless the user asks. Labour lives on the Labour tab and on Price Summary.

## Specification first

Order of evidence for a rate:

1. Printed on the drawing (size, brand, model).
2. Project specification clause that names the item.
3. Product family implied by a named system (example: a named VRF indoor implies that maker's controller, not a random thermostat).
4. Stated assumption — average market for this building use, plus a best-in-class alternative.

Write the evidence source on the Material Rates row. If the spec is silent, say assumed and name the comparable product. Do not invent a model number and present it as specified.

Off-premise items stay qty 0 and money 0 on this book (AHU on an H&C sheet, DHW on an H&C sheet). Do not price them here unless the user expands the premise.

## Labour is by work category

Do not store one blended hourly rate on every floor line.

Work categories (extend only when the inventory needs it):

| Work category | Typical unit of work |
|---|---|
| F-Gas / refrigerant install | per indoor, per outdoor, per joint |
| Pipework / tray / condensate | per metre |
| Insulation | per metre |
| Controls / containment electrics | per point |
| Commissioning | per system or per outdoor |

Each Labour row: category, unit, hours per unit, pounds per hour (editable), hours total (formula from inventory qty), labour money (hours x rate).

Hourly-rate cells are inputs. Everything else is a formula. Changing a rate must move Price Summary.

Productivity hours come from inventory quantities (FCU count, copper metres, lagging metres). Do not type a labour lump on Price Summary.

## Summary extension

Keep the inventory Summary columns from drawings-reader (category, item_id, description, unit, qty_building, where_found, scope).

Add:

| Column | Formula |
|---|---|
| unit rate avg | VLOOKUP(item_id, MaterialRates, …) |
| unit rate prem | VLOOKUP(item_id, MaterialRates, …) |
| Material avg | qty_building * unit rate avg |
| Material prem | qty_building * unit rate prem |

Group by category. Category subtotal is SUM of the item rows in that group, not a typed headline.

## Price Summary

One row per drawing tab plus a building total, and one block per work category.

| Block | Source |
|---|---|
| Materials by drawing | SUM of that drawing tab material columns |
| Materials by category | SUMIF Summary category |
| Labour by work category | Labour tab |
| Building total avg + labour | materials avg + labour |
| Building total prem + labour | materials prem + labour |

State on the face of the sheet: currency, date of rates, ex-VAT, what is excluded.

## Stop conditions

- No item ID on a line that needs money — fix inventory first.
- Spec and drawing disagree — keep both notes, price the specified product, flag the drawing.
- Rate not found — assumed row on Material Rates, never a typed rate on the floor.
- Circular SUM that includes the total row — rewrite the range.
- Cloud connector cannot append — write the full local xlsx and say the cloud book was not updated.
