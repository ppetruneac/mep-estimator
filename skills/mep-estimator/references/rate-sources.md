# Rate sources — spec first, then an assumed product

How to fill Material Rates when the drawing is silent. No merchant prices stored here. Prices go on the workbook and must be dated.

## 1. Evidence order

1. Title block, legend and printed size on the drawing.
2. Project specification that names the system, material or accessory.
3. Product family implied by a named system on the drawing (a named VRF indoor implies that maker's branch controller and remote, not a generic thermostat).
4. Assumed average-market product for this building use, plus a best-in-class alternative.

Write the rung used in spec_source on Material Rates. Assumed is a valid source. Pretending an assumption is specified is not.

## 2. What the spec usually locks

| Topic | What to lift |
|---|---|
| Indoor / outdoor plant | Maker, system family (VRF / Hybrid / chiller / split), refrigerant |
| Pipe | Material standard, jointing, purge |
| Insulation | Class / thickness / vapour barrier. Copper only unless the spec says otherwise |
| Controls | Maker remote vs bedhead / BMS card |
| Leak detection | Named detector family if the refrigerant charge needs it |
| Tray | Width if printed on the drawing; material only if specified |

If the spec says as-scheduled and there is no schedule, treat model as assumed and keep the family.

## 3. Assumptions when the spec is silent

Match the building use (hotel bedrooms, offices, retail, plant room), not a catalogue favourite.

| Item family | Average-market stance | Best-in-class stance |
|---|---|---|
| Bedroom wall terminal | Mid-range VRF indoor in the specified family | Same family, higher duty / lower noise series |
| Cassette / ducted | Mid-range indoor in the specified family | Higher series, better filtration if the room use needs it |
| Outdoor module | Specified family, duty inferred from indoor count | Same family, heat recovery if the drawing already shows it |
| Branch controller | Maker HBC / BC that fits the indoor count | Same, spare port capacity |
| Copper pair | Specified standard, diameter from product ports | Same standard, larger wall thickness only if spec asks |
| Lagging | Closed-cell elastomeric to the specified class | Same class, thicker wall if the spec table allows |
| Condensate | Plastic to drain, not copper | Same. Do not upgrade condensate to copper without a spec |
| Room control | Maker wired remote | Specified hotel bedhead / key-card interface |
| Door curtain / panel heater | Commercial electric unit, duty inferred from room | Higher-duty / quieter unit |
| Expendables | Trade pack sized to joint count | Same items, do not invent branded kits |

Two columns on Material Rates already express average vs best-in-class. Do not add a third option tab.

## 4. Labour rate stance

Use published or quoted client charge-out for the project region and date, not take-home pay.

Split by work category (F-Gas, pipe/tray, insulation, controls electrics, commissioning). Do not apply an F-Gas rate to lagging metres.

If no quote is on file, state the region, the date, and that the figure is an industry-average charge-out. Keep hourly rates in yellow cells.

## 5. What not to price on this book

- Items off the sheet premise (AHU on an H&C take-off, DHW on an H&C take-off) unless the user expands scope.
- Preliminaries, crane, roof access, welfare, VAT, design hours — list as excluded on Price Summary.
- Double-counted interfaces (full-height riser plus per-storey passing plus roof laterals). Price each interface once.

## 6. Refresh

Rates age. If the user asks for a reprice, edit Material Rates and Labour inputs only. Drawing tabs and Summary must move by formula. Do not walk the floors pasting new unit rates.
