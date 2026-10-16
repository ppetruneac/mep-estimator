# riser_extract — Phase 1 deterministic MEP extractor

Deterministic geometry and text extraction from plotted Stage 3 / Stage 4 MEP PDFs.

No ML / YOLO. Pure PDF parsing (PyMuPDF + pdfplumber) + rule-based classification.

This package is the seed of the **Riser** take-off engine. It produces JSON inventory that later stages (pricing, Excel handshake, Q&A) consume.

## Installation

From the repository root:

```bash
uv venv .venv
uv pip install -e ".[dev]"
```

Or, once a lockfile exists:

```bash
uv sync --dev
```

## CLI

```bash
uv run riser-extract path/to/drawing.pdf -o out/
uv run riser-extract path/to/folder/ -o out/          # all *.pdf
uv run riser-extract drawing.pdf -o out/ --no-overlay
```

Outputs:

- `out/inventory_json/{drawing-number}.json` — full extraction
- `out/overlays/{drawing-number}.pdf` — visual overlay (leaders, bboxes, scale)

Eval gate:

```bash
uv run riser-eval --primary-only
uv run pytest
```

## Output schema (high level)

Each JSON contains:

- `title_block` — drawing number, title, scale, floor, discipline, etc.
- `occurrences[]` — every counted or measured item
  - `item_id` — trade-prefixed (`MEC-FCU-WALL`, `ELEC-PNL`, `PLUM-COND`, `VENT-AHU`, …)
  - `legacy_item_id` — matching the skills inventory model (`HC-FCU-WALL`, …)
  - `qty` / `length_m` / `plan_m`
  - `bbox` (pixel + metres), layer, colour, measurement type
  - evidence (leader text, nearby tags, etc.)
- `summary` — counts, scale, backend used

JSON only in Phase 1. Full Excel Master / Summary is a later slice.

## Package layout

| Module | Responsibility |
|---|---|
| `cli.py` | `riser-extract` entry point |
| `eval_cli.py` | `riser-eval` gold comparison |
| `pipeline.py` | Orchestrates page → text → leaders → classify → scale → export |
| `schema.py` | Pydantic models (`ExtractionResult`, `Occurrence`, `TitleBlock`) |
| `page.py` / `text.py` | PDF page loading and word extraction |
| `leaders.py` | Leader-line tracing from annotation to symbol |
| `tags.py` | Tag parsing and association |
| `classify.py` | Rule-based item classification |
| `scale.py` | Scale detection and metre conversion |
| `paths.py` | Path / length measurement |
| `overlay.py` | Overlay PDF generation |
| `ids.py` | Item ID and legacy ID mapping |
| `export.py` | JSON writer |

## Item IDs

Live extraction uses trade prefixes: `MEC` / `ELEC` / `PLUM` / `VENT`.

Every occurrence also carries `legacy_item_id` (`HC-*` / `VT-*` / `PH-*`) so it remains compatible with `skills/drawings-reader/references/inventory-model.md`.

## Relationship to the rest of the repo

- Method and inventory model: `skills/drawings-reader/`
- Pricing method: `skills/mep-estimator/`
- Gold evals: `evals/`
- Product docs: `docs/riser/`
- Agent notes: root `AGENTS.md`

See also the root [README](../../README.md) and [AGENTS.md](../../AGENTS.md).
