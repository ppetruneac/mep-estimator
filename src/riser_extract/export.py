"""Write extraction results as JSON (Phase 1 — no CSV)."""

from __future__ import annotations

import json
from pathlib import Path

from riser_extract.schema import ExtractionResult


def drawing_slug(drawing_number: str | None, fallback: str) -> str:
    if not drawing_number:
        return fallback
    return drawing_number.replace("/", "-").replace(" ", "")


def write_json(result: ExtractionResult, out_dir: str | Path, slug: str) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{slug}.json"
    payload = {
        "title_block": result.title_block.model_dump(),
        "occurrences": [o.model_dump() for o in result.occurrences],
        "symbols": [s.model_dump() for s in result.symbols],
        "summary": result.summary(),
        "extractor_version": result.extractor_version,
        "backend": result.backend,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
