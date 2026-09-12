# Riser — business plan

**Brand:** Riser  
**Domain:** [getriser.co.uk](https://getriser.co.uk)  
**One line:** Upload the MEP set. Get a checked takeoff, a BoM, and a price — then ask the drawings questions.

Take-off, bill of materials, live rates and project estimates for UK MEP contractors — without ripping Excel out of their hands.

*Draft for founder review. Not a fundraising deck. September 2026. Spoken name: Riser. The domain is how people arrive. Do not spend on riser.app yet.*

## 1. What we already proved

Over a live hotel heating-and-cooling package we did the job contractors still do in Excel: read Stage 4 PDFs, follow every leader to a symbol, count terminals, estimate pipe and tray, keep ventilation plant off an H&C book, attach material and labour rates, and produce a building summary that does not double-count a riser.

That work is the product thesis. The pain that matters first is **takeoff → BoM → price**, not AI chat.

- A leader is not a pipe. Typical-detail labels are not extra units.
- Sheet title is the filter. An AHU on a cooling drawing is visible, not priced.
- Unit rates belong in one book. Floors look them up. They are not copied.
- Labour is hours × category rate, not a blended lump that lands at £49m.
- Missing floors can be interpolated only if you label them interpolated.
- Google Drive is where the files live. The estimator still wants an .xlsx they can download.
- Human review is the product, not a disclaimer. Every line must be auditable — a box on the sheet and a confidence score.

## 2. The problem

UK MEP contractors still lose bids (or win them and lose money) because takeoff is slow and leaky.

- Counting symbols and tracing pipe, duct and conduit across a full set takes hours to days.
- Schedules, notes and specs disagree with the plans; that only shows up after the bid is out.
- Quantities live in one tool, list prices in Luckins or a spreadsheet, labour in another person’s head.
- Revisions force a near-restart.
- Excel is still what they send. It should not be the only database.

## 3. The offer

Riser is an operating layer for SME MEP contractors and specialist estimators. It sits on top of the drawings and specs they already store in Google Drive.

1. Ingest drawings, schedules, specs and other bid docs.
2. Produce a **trade-by-trade takeoff** (counts, linear runs, equipment) with a box on the sheet and a confidence score.
3. **Explode** quantities into a BoM (fittings, hangers, waste, ancillaries) from the same item IDs.
4. **Price** from the contractor’s own rates and discounts. A UK library can sit behind that later — do not try to replace Ensign’s weekly book on day one. Export into them if needed.
5. Let the estimator **ask the set** (“what’s the spec on the VAVs on level 3?”) with a cite back to the sheet.
6. Email the pack back into the same Drive thread.

| Job to be done | What Riser does | What the contractor keeps |
|---|---|---|
| Take off a PDF set | Read title block, leaders, tags, scale. Propose counts and routes with confidence. | Accept / reject / override every line. |
| Bill of materials | Stable item IDs, categories, where-found, exploded ancillaries. | Their section names and codes. |
| Price tracking | One material book, one labour book. Dated. Avg vs premium. | Their discounts and charge-out. |
| Project estimate | Materials by drawing and category + labour by work type. | Prelims, risk, OH&P they add. |
| Project Q&A | Ask the drawings + spec + inventory in one place, cited. | The commercial decision. |
| Issue the bid | xlsx + PDF into Drive. Email the pack. | Their letterhead and covering mail. |

## 4. Why Excel stays in the product

UK MEP estimating still runs on workbooks. Ensign, EES, Trimble and Luckins-backed tools exist. Plenty of firms still will not move a live tender out of a sheet the QS can audit at 11pm. Fighting that is a go-to-market tax.

Riser treats Excel as an interface, not the system of record.

- System of record: project items with IDs, measurement type, scope, rates, hours.
- Excel is an export, an import, and a review surface. Users can still sort, filter and override.
- Customisation lives in data (rate book, labour norms, categories, templates), not in a private macro workbook.
- If a cell is a rate, it is an input. If a cell is money, it is a formula. The app enforces that even when the file is opened in Excel.

That is the lesson from the live book: circular SUMs, pasted rates, two Material Rates tabs, and a roof total that included itself. An app that only wraps Excel without a schema will recreate the same mess. An app that bans Excel will not be opened on Friday night.

V1 output must be an Excel takeoff they would actually send a supplier.

## 5. Who it is for

**Primary:** UK MEP / M&E subcontractors — estimators and QS on commercial and multi-residential jobs.

| Segment | Why they buy | Why they churn if we miss |
|---|---|---|
| SME mechanical / AC contractor (5–80 staff) | Bid more Stage 3–4 packages without a full QS bench. | If take-off is slower than a markup PDF + sheet. |
| Specialist estimator / freelance QS | Repeatable method across clients. Their rate book travels. | If they cannot take the xlsx to the client. |
| Small M&E consultancy doing design-intent counts | Same drawing set, inventory for the contractor. | If we price fabrication from intent drawings. |

**Not first:** architects, BIM coordinators, main-contractor planners. They can sit on the same BoM later. Naming and roadmap stay estimator-first so the homepage is not “AEC platform.”

Also not first: national contractors already on Ensign or Trimble with a Luckins pipe. Riser wins where the firm lives in Drive + Excel and loses days to leader-chasing and stale rates.

Sell to the person who stays late on bid night, not the IT manager.

## 6. Why this can win

Incumbents are deep on **price books and labour units** (Ensign, EES Data, Trimble Estimation MEP) or good at **one slice** (Countfire on electrical counts, MEPdetect on symbols). Generic takeoff (Bluebeam, PlanSwift) does not know a 20A socket from a soil stack.

The gap: **drawing-native takeoff + UK BoM/price in one pass**, with Q&A on the same set. Do not try to replace Ensign’s weekly price library on day one — export into them if needed. Speed of learning *their* symbols and *their* rate card is the defence when incumbents add AI counting.

| Player | They own | Gap Riser occupies |
|---|---|---|
| Ensign, EES Data | UK contractor estimating + weekly price / labour units | Speed of first-pass takeoff + Q&A on the set |
| Trimble Estimation MEP / Luckins | Catalogue and list prices | Contractor net rates when the spec has no model |
| Countfire | Electrical symbol counts | Multi-trade + BoM explosion |
| MEPdetect, DrawScale | Symbol AI | Price + assemblies, not just counts |
| Bluebeam, PlanSwift, STACK | Click lengths on a PDF | Trade meaning (tags, schedules, fittings, premise) |
| ChatGPT + Excel | Cheap and familiar | No audit trail, no IDs, rates get pasted, scope bleeds |

## 7. Product principles

1. Premise before price. Heating-and-cooling sheets do not silently become ventilation bills.
2. Count symbols, not labels. Show the box on the sheet.
3. Name the measurement: printed, scaled, geometry, vertical, specified-not-drawn, excluded.
4. One rate book. Join by item ID. Never paste unit rates onto a floor.
5. Labour is a work category with hours per unit, not a mystery total.
6. Where-found is a first-class field. Building totals must say which sheets contributed.
7. The contractor can override anything. Overrides are stored, not hidden in a cell.
8. Excel out, Drive in, email out. The bid still looks like their bid.
9. Human review ships with V1. If there is no review loop, do not ship counting.

## 8. Product (phased)

### V1 — bid in a week

- PDF set + schedule ingest
- Electrical / mechanical / plumbing symbol count with confidence and a box on the sheet
- Linear measure (pipe, duct, conduit, tray) with scale
- Sheet + spec Q&A with a cite
- Excel / CSV takeoff + simple BoM
- Revision overlay (“what changed”)

Electrical counts are the easiest proof. Pipe and duct is the higher-value proof. Start with one trade on a live set if needed.

### V2 — bid day

- Assemblies (example: socket = box + plate + earth + labour)
- Waste factors and purchase rounding
- Contractor rate card + supplier quote paste
- Labour units (even a thin JIB-style table)
- Quote PDF
- Luckins / Ensign-shaped exports — UK language, not US Trade Service

### V3 — after the win

- Inventory / buyout from the same BoM
- Variation vs issued set
- Optional seats for design and planning (quantities only)

## 9. Customisation without a private fork

Users will not accept a locked library. They also cannot be allowed to fork the schema.

| They can change | They cannot break |
|---|---|
| Category names and sort order | Item ID pattern and required fields |
| Rate book, discounts, avg vs premium | Join key from item to rate |
| Hours per unit and pounds per hour by trade | Hours must reference inventory qty |
| Export template (columns, letterhead) | Measurement-type vocabulary |
| Which disciplines are in-scope for a project | Off-premise items still recorded as exclusions |
| Assumed product when spec is silent | Assumed stays labelled assumed |
| Waste factors and assembly recipes | Required evidence on every priced line |

## 10. Pricing (indicative)

Willingness to pay is real: specialist tools cost thousands per year; AI takeoff newcomers charge from roughly £80 per job to a few hundred per month. Charge where hours come out of the bid. Do not launch on free AI chat.

Two shapes, both valid:

- Per-project fee for small firms (for example by trade-page count), **or**
- Seat subscription once the estimating team runs it every week.

| Plan | Who | Shape |
|---|---|---|
| Studio | Solo estimator | 1 user, few live projects, Drive export, email pack. Per-project option. |
| Workshop | SME contractor | 5 users, unlimited projects, rate-book versions, Q&A. |
| Works | Multi-site / framework | SSO, audit log, client portals, API, custom template, Ensign-shaped export. |

Add-ons: extra Drive workspaces, named rate-book hosting, on-prem rate file sync. Do not bundle Luckins-class data on day one — that is a partnership, not the MVP.

## 11. Go to market

- Beachhead: London and South East mechanical contractors bidding hotel / residential VRF packages. That is the job we already did.
- Ten estimators on live tender sets — measure hours saved and missed items caught.
- One trade first if needed (electrical counts for proof; pipe and duct for value).
- Wedge: send the Drive folder, get a first inventory tab back in 24 hours as a concierge MVP while the app is built.
- UK language: Luckins / Ensign-shaped exports, not US Trade Service.
- Proof: publish the method (drawings-reader + estimator skills) as the public standard. The app is the hosted version of a method they can inspect.
- Channel: QS networks, F-Gas / REFCOM circles, small M&E consultancies who already mark PDFs.
- Do not lead with AI. Lead with your rates, your floors, no double-counted riser.
- Do not spend on riser.app or a broad AEC story until three firms have priced a job in it.

## 12. Economics (order of magnitude)

A mid-size mechanical bid package still burns 2–5 estimator-days. If Riser saves one day per bid at a loaded £450–£650/day, Workshop at £200–£400/month is an easy conversation — provided the first take-off is trusted.

Gross margin should stay software-like. Concierge take-off in the first six months is a customer-acquisition cost, not the product. Cap it. Convert those jobs into labelled training data and templates.

## 13. Risks

| Risk | Mitigation |
|---|---|
| Wrong counts on a priced bid | Human accept step. Box on the sheet. Confidence score. Never silent invent on a tag gap. |
| No review UI | Do not ship counting. Review loop is V1. |
| Ensign / EES already in the account | Interoperate: export BoQ they can import. Do not pick a fight on week one. |
| Rate copyright / Luckins | Contractor-owned rates first. Partner or import later. |
| Incumbents add AI counting | Learn their symbols and their rate card faster than they learn the set. |
| Excel users refuse a web grid | Round-trip xlsx that re-imports overrides. |
| Hallucinated specs | Evidence order on every rate row. Assumed is labelled. |
| Drive / Gmail scopes scare IT | Least-privilege. Project folder only. Email as a draft, not silent send. |
| Domain vanity | getriser.co.uk is enough. Do not buy riser.app at this stage. |

## 14. Twelve-month plan

| Phase | Outcome |
|---|---|
| 0–3 months Foundation (V1 start) | Domain model live. PDF ingest + review UI. xlsx export matching the current book. Concierge on 5 packages. One estimator sitting next to you on a live commercial set. |
| 3–6 months Workshop (V1 finish) | Rate book + labour categories. Summary + Price Summary. Drive write-back. Email pack. Revision overlay. |
| 6–9 months Memory (V2) | Assemblies, waste, quote PDF. Project Q&A over drawings, spec and inventory. Versioned rates. Ensign-shaped export. |
| 9–12 months Works (V3 start) | Multi-user audit. Buyout from the same BoM. Template library. First paid Workshop cohort. Three firms have priced a job in it. |

## 15. Brand and domain

- Product name: **Riser**
- Public URL: **getriser.co.uk**
- Spoken name on site and in sales: Riser. The domain is how people arrive.
- Do not spend on `riser.app` at this stage.

## 16. Decision

Build Riser as the productised version of the method we already run: read the drawing properly, keep the inventory honest, explode a BoM, join rates by ID, let the contractor change the yellow cells.

Excel is the handshake. The schema is the company.

Estimators do not want another copilot. They want the set turned into a defensible, priced BoM by tomorrow morning, with every quantity still tied to a sheet.
