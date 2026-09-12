# Riser — technical execution

*Companion to the [business plan](business-plan.md). Hosted version of `drawings-reader` + `mep-estimator`.*

How to build the product without throwing away Excel, and without letting Excel become the database.

## 1. Design constraint

The contractor must be able to download a workbook that looks like the one they already use: one tab per drawing, Summary by item ID, Material Rates, Labour, Price Summary. They must also be able to change a yellow rate and see floors move. If the web app cannot emit that file, it is not done.

Internally the source of truth is not the xlsx. It is a project graph. The xlsx is a projection.

## 2. Domain model

### 2.1 Core objects

| Object | Key fields |
|---|---|
| Organisation | rate books, labour books, templates, Drive connection |
| Project | premise (H&C / vent / PH / elec), currency, region, rate-book version |
| Document | drawing or spec, Drive file id, revision, title-block JSON, page size, scale |
| Item | item_id, category, unit, scope, measurement_type |
| Occurrence | item + document + qty + tender_qty + where on sheet + evidence |
| Rate | item_id, avg, prem, spec_source, assumed_product, dated |
| LabourNorm | work_category, unit, hours_per_unit, gbp_per_hour |
| Override | who, when, field, old, new, reason |
| Estimate | frozen totals snapshot + pointer at live formulas |

### 2.2 Item ID

Stable across floors: `{discipline}-{family}-{token}`. Example `HC-FCU-WALL`. Floor is not in the ID. Local line codes (`A01`) are display only.

### 2.3 Measurement type

`printed` | `scaled` | `geometry` | `vertical` | `specified-not-drawn` | `excluded`.

Required on every occurrence. UI shows amber when not printed.

### 2.4 Scope

in | interface | out. Title-block premise decides the default. Out still stored so Q&A can say the AHU is on the roof sheet and is not in this price.

## 3. User journeys

1. Connect a Drive folder. Pick the drawing set and spec PDFs.
2. Riser extracts title blocks and proposed inventory. Estimator reviews leaders on the raster.
3. Accept / split / reject lines. Tag gaps stay as allowances, not invented units.
4. Attach org rate book (or start from a template). Confirm assumed products.
5. Labour norms pull hours from accepted qty. Estimator edits hours/unit and pounds per hour.
6. Summary and Price Summary generate. Estimator adds prelims as separate lines.
7. Export xlsx / PDF. Write back to the Drive folder. Open a Gmail draft with the pack attached.
8. Q&A: where is condensate priced? Answers from inventory + measurement_type + where_found.

## 4. Architecture

### 4.1 Shape

- Web app (estimator UI) + worker (PDF extract, scale, formula rebuild) + API.
- Postgres for the graph. Object store for rasters and original PDFs.
- Google Drive and Gmail via OAuth, project-folder scope only.
- xlsx built server-side with the same rules as the estimator skill (named ranges, VLOOKUP/XLOOKUP by item_id, SUM that excludes the total row).
- Q&A: retrieval over title-block text, spec clauses, item notes, where_found — not a free model over raw pixels.

### 4.2 Why not Excel-in-the-browser as the database

Grid UIs are fine for review. They are a poor source of truth for joins. The live hotel book grew REF errors and circular totals the moment rows were deleted. The app must rewrite lookups after every structural edit, same as the skill rule.

### 4.3 Excel round-trip

| Direction | Rule |
|---|---|
| App to xlsx | Full book. Yellow inputs. Formulas on money. AutoFilter on the real header. |
| xlsx to app | Only yellow input cells and marked override columns re-import. Structural rows ignored. |
| Conflict | Last explicit override wins. Show a diff, do not silent-merge rates. |

## 5. Take-off pipeline

| Step | Implementation note |
|---|---|
| Ingest | Drive file id. Store original. pdfinfo for page size and rotation. |
| Text | pdfplumber words with coordinates. pdftotext -layout for notes. |
| Raster | 72 dpi on true plotted size so 1 cm maps to scale. |
| Title block | Project, number, rev, scale, paper, disclaimer. Filename loses. |
| Leaders | Propose target symbol from crop + colour heuristic. Human confirms. |
| Tags | Deduplicate. Sequence-gap = allow +1, do not invent. |
| Lengths | Scaled along spine if hatch exists; else geometry to nearest core; verticals from section or stated storey height. |
| Premise filter | Off-title plant written as exclusions. |

Do not ship colour flood-fill as the length engine. It under-counts thin hatch. That was already learned.

## 6. Pricing engine

Port the mep-estimator rules.

- Material Rates: one row per item_id. avg and prem columns. spec_source required.
- Drawing tabs: unit rate and extension are formulas against the MaterialRates named range.
- Labour: work categories with hours_per_unit × inventory driver × pounds per hour.
- Summary: qty_building, where_found, material money via lookup. Group by category.
- Price Summary: materials by drawing, materials by category, labour by category, building totals. Ex-VAT. Prelims listed excluded until the user adds them.

Evidence order for a blank spec: drawing print → project spec clause → product family of the named system → assumed average + best-in-class. Assumed is a field, not a footnote someone deletes.

## 7. Project Q&A

This is not a general chatbot. It answers against the project corpus.

| Question type | Grounding |
|---|---|
| What did we count on third floor? | Occurrences where document = 3F |
| Is condensate drawn? | measurement_type = specified-not-drawn |
| Why is the AHU unpriced? | scope = out, premise = H&C |
| Where is the large refrigerant pair used? | item notes + rate row |
| What changes if storey height is 3.6 m? | Recompute vertical occurrences only, show delta |

Refuse to invent a count in Q&A. If the raster was not reviewed, say so.

## 8. Google Drive and email

- OAuth: Drive file access limited to the folder the user picks. Gmail send as a user-visible draft first.
- Write-back path: Riser Estimate.xlsx and Riser Estimate.pdf into that folder. Never create a second spreadsheet for the next floor.
- If Drive write is denied, the user still gets a local download. That failure mode already happened on the live job.
- Email pack: PDF summary + xlsx + short body listing premise, exclusions, rate date.

## 9. Customisation layer

| Hook | Storage |
|---|---|
| Category catalogue | Org table. Default H&C set shipped. |
| Rate book versions | Immutable version + editable draft. Estimates pin a version. |
| Labour norms | Org defaults, project override. |
| Export template | Column order, letterhead image, disclaimer. |
| Premise pack | Which item families default to in/out per drawing title. |

Do not let users delete required fields. Do let them hide columns.

## 10. Suggested stack

| Layer | Pragmatic default |
|---|---|
| API / app | TypeScript, Postgres, object store |
| Workers | Python already used for pdfplumber / openpyxl — keep it |
| Auth | Google Workspace sign-in for the beachhead |
| xlsx | Same generator the estimator skill uses, versioned |
| Q&A | Constrained retrieval + citations to document + item_id |
| Hosting | EU region. Project data residency stated in the contract |

## 11. Build slices

| Slice | Done when |
|---|---|
| S0 Schema + xlsx projector | We can emit the current hotel book from seed data with live formulas. |
| S1 Drive ingest + review UI | Estimator accepts basement + one bedroom floor from PDFs. |
| S2 Rate book join | Change one yellow cell, floors and Summary move. Zero formula errors. |
| S3 Labour categories | Hours follow FCU count and copper metres. Hourly rate editable. |
| S4 Issue pack | xlsx + PDF land in the Drive folder. Gmail draft opens. |
| S5 Q&A | Five question types in section 7 answered with citations. |
| S6 Round-trip | Override a qty in Excel, re-import, audit log shows the change. |

## 12. Quality bar

- No priced line without item_id, category, measurement_type, scope.
- No unit rate stored on an occurrence.
- Recalc of a generated xlsx returns zero formula errors.
- Tag-gap policy: allow, do not invent.
- Human accept before a pack is marked issued.
- Every Q&A answer cites an object id.

## 13. What not to build in v1

- A Luckins-scale catalogue.
- Full BIM / IFC take-off.
- Payroll or timesheets.
- Automatic send of emails without a draft step.
- Silent interpolation of missing floors.

## 14. Open decisions

1. UK-only first, or expose currency/region on day one.
2. Whether Workshop includes a hosted starter rate book or empty yellow cells only.
3. Whether the public method (GitHub skills) stays public as marketing, or becomes licensed content.
