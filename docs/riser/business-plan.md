# Riser — business plan

Take-off, bill of materials, live rates and project estimates for UK MEP contractors — without ripping Excel out of their hands.

*Working title for [getriser.co.uk](https://getriser.co.uk). Draft for founder review. Not a fundraising deck. September 2026.*

## 1. What we already proved

Over a live hotel heating-and-cooling package we did the job contractors still do in Excel: read Stage 4 PDFs, follow every leader to a symbol, count terminals, estimate pipe and tray, keep ventilation plant off an H&C book, attach material and labour rates, and produce a building summary that does not double-count a riser.

That work is the product thesis. The pain is not another estimating database. The pain is: drawings arrive as PDFs in Drive, the take-off lives in a spreadsheet the QS can edit, rates get pasted and go stale, scope from the wrong discipline leaks into the price, and nobody can ask the project a straight question six weeks later.

- A leader is not a pipe. Typical-detail labels are not extra units.
- Sheet title is the filter. An AHU on a cooling drawing is visible, not priced.
- Unit rates belong in one book. Floors look them up. They are not copied.
- Labour is hours × category rate, not a blended lump that lands at £49m.
- Missing floors can be interpolated only if you label them interpolated.
- Google Drive is where the files live. The estimator still wants an .xlsx they can download.

## 2. The offer

Riser is an operating layer for SME MEP contractors and specialist estimators. It sits on top of the drawings and specs they already store in Google Drive, produces a structured inventory, prices it from their rate book, and answers questions against that project — then emails the estimate back into the same Drive thread.

| Job to be done | What Riser does | What the contractor keeps |
|---|---|---|
| Take off a PDF set | Read title block, leaders, tags, scale. Propose counts and routes. | Accept / reject / override every line. |
| Bill of materials | Stable item IDs, categories, where-found across floors. | Their section names and codes. |
| Price tracking | One material book, one labour book. Dated. Avg vs premium. | Their discounts and charge-out. |
| Project estimate | Materials by drawing and category + labour by work type. | Prelims, risk, OH&P they add. |
| Project Q&A | Ask the drawings + spec + inventory in one place. | The commercial decision. |
| Issue the bid | xlsx + PDF into Drive. Email the pack. | Their letterhead and covering mail. |

## 3. Why Excel stays in the product

UK MEP estimating still runs on workbooks. Ensign, Trimble and Luckins-backed tools exist. Plenty of firms still will not move a live tender out of a sheet the QS can audit at 11pm. Fighting that is a go-to-market tax.

Riser treats Excel as an interface, not the system of record.

- System of record: project items with IDs, measurement type, scope, rates, hours.
- Excel is an export, an import, and a review surface. Users can still sort, filter and override.
- Customisation lives in data (rate book, labour norms, categories, templates), not in a private macro workbook.
- If a cell is a rate, it is an input. If a cell is money, it is a formula. The app enforces that even when the file is opened in Excel.

That is the lesson from the live book: circular SUMs, pasted rates, two Material Rates tabs, and a roof total that included itself. An app that only wraps Excel without a schema will recreate the same mess. An app that bans Excel will not be opened on Friday night.

## 4. Who it is for

| Segment | Why they buy | Why they churn if we miss |
|---|---|---|
| SME mechanical / AC contractor (5–80 staff) | Bid more Stage 3–4 packages without a full QS bench. | If take-off is slower than a markup PDF + sheet. |
| Specialist estimator / freelance QS | Repeatable method across clients. Their rate book travels. | If they cannot take the xlsx to the client. |
| Small M&E consultancy doing design-intent counts | Same drawing set, inventory for the contractor. | If we price fabrication from intent drawings. |

Not first: national contractors already on Ensign or Trimble with a Luckins pipe. Riser wins where the firm lives in Drive + Excel and loses days to leader-chasing and stale rates.

## 5. Market and competition

UK MEP estimating is a known category. Ensign positions take-off plus a 350k-item library. Trimble Estimation MEP / Luckins sells a managed catalogue. STACK and Groundplan sell generic plan measure. McCormick is US-weighted.

Riser does not start by trying to own the national price list. It starts where those tools are weak for the SME AC / fabricator: design-intent PDF reading with discipline scope, a contractor-owned rate book that actually drives the floors, and a project memory you can query.

| Player | They own | Gap Riser occupies |
|---|---|---|
| Ensign | UK contractor estimating + take-off UI | Messy Stage 4 PDF reading + project Q&A + Drive-native issue. |
| Trimble / Luckins | Catalogue and list prices | Contractor net rates and assumptions when the spec has no model. |
| STACK / plan measure | Click lengths on a PDF | MEP premise, HBC vs VRF, passing-riser logic. |
| ChatGPT + Excel | Cheap and familiar | No audit trail, no IDs, rates get pasted, scope bleeds. |

## 6. Product principles

1. Premise before price. Heating-and-cooling sheets do not silently become ventilation bills.
2. Count symbols, not labels.
3. Name the measurement: printed, scaled, geometry, vertical, specified-not-drawn, excluded.
4. One rate book. Join by item ID. Never paste unit rates onto a floor.
5. Labour is a work category with hours per unit, not a mystery total.
6. Where-found is a first-class field. Building totals must say which sheets contributed.
7. The contractor can override anything. Overrides are stored, not hidden in a cell.
8. Excel out, Drive in, email out. The bid still looks like their bid.

## 7. Customisation without a private fork

Users will not accept a locked library. They also cannot be allowed to fork the schema.

| They can change | They cannot break |
|---|---|
| Category names and sort order | Item ID pattern and required fields |
| Rate book, discounts, avg vs premium | Join key from item to rate |
| Hours per unit and pounds per hour by trade | Hours must reference inventory qty |
| Export template (columns, letterhead) | Measurement-type vocabulary |
| Which disciplines are in-scope for a project | Off-premise items still recorded as exclusions |
| Assumed product when spec is silent | Assumed stays labelled assumed |

## 8. Pricing (indicative)

Sell seats plus projects. Catalogue access is optional later, not the wedge.

| Plan | Who | Shape |
|---|---|---|
| Studio | Solo estimator | 1 user, 3 live projects, Drive export, email pack. |
| Workshop | SME contractor | 5 users, unlimited projects, rate-book versions, Q&A. |
| Works | Multi-site / framework | SSO, audit log, client portals, API, custom template. |

Add-ons: extra Drive workspaces, named rate-book hosting, on-prem rate file sync. Do not bundle Luckins-class data on day one — that is a partnership, not the MVP.

## 9. Go to market

- Beachhead: London and South East mechanical contractors bidding hotel / residential VRF packages. That is the job we already did.
- Wedge: send the Drive folder, get a first inventory tab back in 24 hours as a concierge MVP while the app is built.
- Proof: publish the method (drawings-reader + estimator skills) as the public standard. The app is the hosted version of a method they can inspect.
- Channel: QS networks, F-Gas / REFCOM circles, small M&E consultancies who already mark PDFs.
- Do not lead with AI. Lead with your rates, your floors, no double-counted riser.

## 10. Economics (order of magnitude)

A mid-size mechanical bid package still burns 2–5 estimator-days. If Riser saves one day per bid at a loaded £450–£650/day, Workshop at £200–£400/month is an easy conversation — provided the first take-off is trusted.

Gross margin should stay software-like. Concierge take-off in the first six months is a customer-acquisition cost, not the product. Cap it. Convert those jobs into labelled training data and templates.

## 11. Risks

| Risk | Mitigation |
|---|---|
| Wrong counts on a priced bid | Human accept step. Amber flags. Never silent invent on a tag gap. |
| Ensign already in the account | Interoperate: export BoQ they can import. Do not pick a fight on week one. |
| Rate copyright / Luckins | Contractor-owned rates first. Partner later. |
| Excel users refuse a web grid | Round-trip xlsx that re-imports overrides. |
| Hallucinated specs | Evidence order on every rate row. Assumed is labelled. |
| Drive / Gmail scopes scare IT | Least-privilege. Project folder only. Email as a draft, not silent send. |

## 12. Twelve-month plan

| Phase | Outcome |
|---|---|
| 0–3 months Foundation | Domain model live. PDF ingest + review UI. xlsx export matching the current book. Concierge on 5 packages. |
| 3–6 months Workshop | Rate book + labour categories. Summary + Price Summary. Drive write-back. Email pack. |
| 6–9 months Memory | Project Q&A over drawings, spec and inventory. Versioned rates. Where-found across revisions. |
| 9–12 months Works | Multi-user audit. Template library (VRF hotel, office fit-out, plant). First paid Workshop cohort. |

## 13. Decision

Build Riser as the productised version of the method we already run: read the drawing properly, keep the inventory honest, join rates by ID, let the contractor change the yellow cells. Excel is the handshake. The schema is the company.
