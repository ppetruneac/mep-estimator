# Phase 4: Length Calculations, Pipe/Tray Aggregation & Formulas

**Linear issue:** [GR-4](https://linear.app/dentaway/issue/GR-4/phase-4-length-calculations-pipetray-aggregation-and-formulas)  
**Status:** Planning document  
**Depends on:** Phase 1 (geometry & text extraction), inventory model (`skills/drawings-reader/references/inventory-model.md`), rules in `skills/drawings-reader/SKILL.md`

## Goal

Turn the deterministic geometry output of Phase 1 into reliable, auditable pipe and tray lengths that feed the inventory. Apply the existing waste factors and measurement-type rules from the drawings-reader skill. Keep every formula deterministic and unit-tested. Engineering formulas (Hazen-Williams, Darcy-Weisbach, etc.) are optional and catalog-driven.

## Source of truth

All rules below come from the existing skill documents. Do not invent new factors.

### Measurement types (from SKILL.md)

| Type | When | How |
|------|------|-----|
| `printed` | Size or length written on the sheet | Copy it. Do not scale it. |
| `scaled` | Coloured spine or hatch is visible | Measure along the route at the sheet scale. Not crow-flies. |
| `geometry` | Repetitive plate, hatch too thin to trace | Average plan from each terminal to the nearest known core. |
| `vertical` | Rise through this storey only | Storey height from section or stated assumption. Never full building height from one floor. |
| `specified-not-drawn` | Spec requires it (condensate, HBC drain) | Unit count × stated average run. Flag amber. |
| `excluded` | Visible but off-premise | Qty = 0. Point to the owning sheet. |

### Default tender conversion for a two-pipe indoor run (water F+R or refrigerant pair)

```
tender_m = (plan_route_m × 2 pipes × 1.15 coordination) + (1.5 m × 2 pipe tails)
```

- 1.15 = coordination waste on design-intent drawings where positions are approximate.
- 1.5 m/pipe = drop, valves and connection at the unit (3.0 m pair tails).

### Tray / containment

- One tray per printed size on that sheet, plus 15 % waste.
- Do not mix sizes (e.g. 300 mm basement with 400 mm bedroom).

### Risers and verticals

- Passing systems through a storey: price `systems × 2 pipes × storey_height` on that floor.
- Do not also price the full-height stack on the plant sheet.
- Mark unique vs interface metres in Master so Summary does not double-count.

### Scale rules

- `1:N @ paper`. 1 cm on the sheet = N/100 metres on site.
- Confirm page size in points. Reduced prints (A1 issued at A3) halve the graphic scale — never reuse metres from a reduced print.
- Pixel scale must be derived from the actual render DPI and the title-block scale.
- Storey-height verticals are not on plan; record the assumption on the tab.

## Architecture

```
Phase 1 geometry (polylines, layers, colours, text, scale)
        ↓
Length engine (filter → measure → classify → waste → aggregate)
        ↓
Inventory records (measurement_type, count/length, tender_m, notes)
        ↓
Optional catalog-driven formulas (pressure drop, etc.)
```

All intermediate results stay in structured JSON/CSV so they can be audited against the Drive inventory spreadsheets.

## Detailed plan

### 1. Length summation from geometry

**Input:** Phase 1 extraction records (vector paths with layer, colour, pixel length, real-world length after scale, nearby text).

**Steps:**

1. Filter candidate paths:
   - By layer name heuristics (pipe, tray, services, refrigerant, etc.).
   - By colour (where the skill notes coloured spines).
   - Exclude known leader/call-out lines (long lines from margin, no hatch).
2. Compute real-world length:
   - Use the scale factor from the title block (already extracted in Phase 1).
   - Handle polylines (sum segments) and simple arcs if present.
   - Store both pixel length and real-world metres.
3. Associate with context:
   - Nearest text tags / annotations from Phase 1.
   - Provisional item_id when the tag or layer allows it (e.g. HC-CU-IN, HC-TRAY-400).
4. Classify measurement_type:
   - `scaled` when a clear coloured spine/hatch was traced.
   - `geometry` when using average-run estimation.
   - `vertical` for storey-height assumptions.
   - `printed` when a length is written on the sheet.

**Output per segment:**

```json
{
  "drawing_number": "25280-SEN-00-DR-M-5600",
  "floor_tab_name": "Ground Floor",
  "layer": "PIPE-REF",
  "colour": "red",
  "pixel_length": 1240.5,
  "real_world_length_m": 12.4,
  "start_coord": [..],
  "end_coord": [..],
  "nearby_text": "FCU-03",
  "provisional_item_id": "HC-CU-IN",
  "measurement_type": "scaled"
}
```

### 2. Apply waste factors and tender conversion

Implement the exact formulas from SKILL.md as pure functions:

```python
def tender_length_two_pipe(plan_route_m: float,
                           coordination_factor: float = 1.15,
                           tail_m_per_pipe: float = 1.5) -> float:
    """Default tender conversion for a two-pipe indoor run."""
    return (plan_route_m * 2 * coordination_factor) + (tail_m_per_pipe * 2)

def tray_length_with_waste(plan_length_m: float, waste_factor: float = 0.15) -> float:
    return plan_length_m * (1 + waste_factor)
```

- Make factors configurable (but default to the skill values).
- Amber-flag any length that used a non-default factor or an assumption.
- Separate `drawn_length_m` from `tender_length_m` in the output.

### 3. Aggregation rules (unique vs interface)

Follow the inventory model exactly:

- Terminals, heaters, stats, lagging, clips → unique. Sum floors.
- This-storey passing riser → unique per storey. Summing floors is correct.
- Full-height riser written on a plant tab → interface. Do not add to the sum of passing rows.
- Roof laterals → unique to the plant tab.
- Exclusions → `qty_building = 0` but still list `where_found`.

Implementation:

- Group segments by `(item_id, floor_tab_name)`.
- Produce both per-floor quantities and a building-level view that respects unique/interface.
- Generate the `where_found` string in the required format:
  ```
  Basement (25280-SEN-0X-DR-M-560X); Ground Floor (25280-SEN-00-DR-M-5600)
  ```

### 4. Optional deterministic engineering formulas

Only when a catalog entry supplies the required parameters (diameter, roughness, flow).

Examples (pure Python, unit-tested):

- Hazen-Williams pressure drop (water).
- Darcy-Weisbach (general).
- Simple velocity / capacity checks.

These are **not** required for the first inventory. They attach as optional fields on the inventory line and are clearly marked as calculated, not extracted.

### 5. Integration with inventory schema

Map length results into the per-drawing tab columns defined in `inventory-model.md`:

| Inventory column | Source |
|------------------|--------|
| Item ID | provisional_item_id or catalog match |
| Count | number of discrete runs or terminals |
| Unit | `m` for linear items |
| Size | printed or catalog diameter |
| Measurement type | `scaled` / `geometry` / `vertical` / … |
| Notes | assumptions, waste factor used, amber flags |
| (Tender estimate) | tender_length_m |

Master / Summary aggregation uses the same unique/interface rules already documented.

### 6. Validation against Drive ground truth

1. Select 2–3 Heating & Cooling layout PDFs + their matching inventory XLSX from the Drive folder.
2. Run the length engine.
3. Compare computed tender lengths (and raw plan lengths) to the inventory numbers for the same item_ids.
4. Report:
   - Absolute and percentage error per major run.
   - Cases where measurement_type differed.
   - Amber-flag rate.
5. Agree on acceptable tolerances (suggested starting point: ±10 % on major runs for design-intent drawings, tighter on fully traced routes).

### 7. Outputs

- Per-drawing length report (CSV/JSON) with every segment.
- Aggregated inventory lines ready for the Excel book.
- Validation comparison report.
- Unit tests covering:
  - Scale conversion.
  - Waste factor formulas.
  - Unique vs interface aggregation.
  - Edge cases (reduced prints, vertical assumptions, exclusions).

## Implementation order

1. Pure length functions + unit tests (waste factors, scale).
2. Segment filter and real-world length calculator on Phase 1 output.
3. Aggregation respecting unique/interface rules.
4. Mapping into inventory schema.
5. Validation harness against Drive spreadsheets.
6. Optional engineering formulas (catalog-driven).
7. Documentation updates in `SKILL.md` if any rule is clarified.

## Acceptance criteria (from GR-4)

- Lengths match ground-truth within agreed tolerance on sample drawings.
- Formulas are unit-tested and deterministic.
- Calculated quantities attach cleanly to inventory lines.
- Detailed length report is produced and auditable.

## Open questions

- Exact storey-height source for verticals on the sample project (section drawing or stated assumption).
- Whether any of the Drive inventories already separate drawn length from tender length.
- Preferred tolerance band for the first validation.

## References

- `skills/drawings-reader/SKILL.md` — measurement types, waste factors, riser rules, scale.
- `skills/drawings-reader/references/inventory-model.md` — item_id format, Master/Summary aggregation, measurement_type.
- Phase 1 extraction schema (GR-1).
- Drive folder inventories (ground truth).
