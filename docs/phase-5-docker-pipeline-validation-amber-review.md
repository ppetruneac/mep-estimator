# Phase 5: Docker Pipeline, Validation Harness & Amber-Flag Review

**Linear:** [GR-5](https://linear.app/dentaway/issue/GR-5/phase-5-docker-pipeline-validation-harness-and-amber-flag-review)

**Status:** Planning document (reevaluated against current repo)

**Depends on:** Phase 1 (`riser_extract`), evals harness, architecture in `docs/riser/technical-execution.md`, inventory review plan (GR-6).

## Goal

Package the current deterministic extractor and future workers as Docker services. Extend the existing validation harness. Implement amber-flag human-in-the-loop. Persist everything in the project graph database (SQLite for local/MVP → Postgres). Excel is a projection/export only. Do not emit CSV as a primary intermediate or deliverable.

## Why the reevaluation

The original GR-5 assumed CSV/Excel-centric flows, optional YOLO, and Drive XLSX as the main comparison target. The repo has moved to:

- Deterministic Phase 1 JSON extraction (`src/riser_extract/`).
- Postgres (or SQLite) as the source of truth for the project graph (see technical-execution.md and GR-6).
- Excel as a contractor handshake / projector (GR-3), not the database.
- Existing eval gate in `evals/` against Hubby gold (`floors.json` + original XLSX).

Phase 5 must fit this model.

## Expected Output

* One-command Docker Compose that:
  * Runs `riser_extract` on a drawing or folder.
  * Loads `ExtractionResult` into DB (drawings + occurrences).
  * Produces overlay PDF(s).
  * Flags amber items and stores them.
* Validation report (extends `evals/reports/`) with precision/recall, length errors, per-class accuracy. Runs in CI.
* Amber list queryable in the review UI (GR-6) or exported for human correction.
* Docker Compose + README.

## Architecture alignment

| Concern | Current / target |
|---|---|
| Intermediate | JSON (`ExtractionResult`) → DB tables |
| Source of truth | Project graph in Postgres / SQLite |
| Excel | Later projector (named ranges, formulas). Not Phase 5 intermediate. |
| CSV | Avoid. Not used in Phase 1; not the handshake. |
| Overlays | Already in `riser_extract` (`overlay.py`) |
| Validation | Extend `riser-eval` + `evals/` |
| Amber | measurement_type ≠ printed, weak evidence, missing scale, rule failures |

## How to get started

1. **Dockerize**
   - Dockerfile for the Python extractor worker (uv / hatchling based).
   - docker-compose.yml with:
     - extractor worker
     - Postgres (or volume-mounted SQLite for local)
     - optional future workers (length engine, etc.)
   - One-command: `docker compose up --build` or `docker compose run extract /path/to/pdf`.

2. **Validation harness**
   - Keep and extend `evals/scripts/` and `riser-eval`.
   - After extraction, load to a temporary DB and compare counts / lengths / item_ids to gold.
   - Produce Markdown + JSON report under `evals/reports/`.
   - CI job that runs the primary-floor gates.

3. **Persistence**
   - Map `ExtractionResult` → tables sketched in GR-6 (projects, drawings, inventory_items).
   - Store pixel_bbox, real_world_coords, measurement_type, scope, evidence.
   - Overlay path stored on the drawing row.

4. **Amber-flag workflow**
   - Rules (deterministic):
     - `measurement_type` in {scaled, geometry, vertical, specified-not-drawn}
     - missing or ambiguous scale
     - leader evidence weak / no nearby tag
     - classification rule failed or low match
   - Store `amber_flag: bool` + `amber_reason: str` on the occurrence.
   - Review surface is the inventory webapp (GR-6); corrections update the DB row and audit log.

5. **End-to-end**
   - Process a Hubby floor PDF.
   - Confirm DB inventory, overlay, amber list, and validation report.

## Acceptance criteria

* One-command Docker run processes a sample drawing and loads occurrences into the DB.
* Validation report generated automatically (extends existing evals).
* Overlay PDF produced and linked.
* Amber items clearly flagged and queryable.

## Open questions

- Exact Docker service boundaries (single worker vs split geometry / classify / persist).
- Whether local Compose uses SQLite or a Postgres container by default.
- How tightly Phase 5 couples to the GR-6 webapp data model vs a minimal loader.

## References

- `src/riser_extract/` — current Phase 1
- `evals/` — existing validation
- `docs/riser/technical-execution.md` — Postgres graph, Excel as projection
- GR-6 / inventory-webapp-plan.md — review UI and DB sketch
- MEPdetect — Docker patterns only (do not copy CSV flow)
