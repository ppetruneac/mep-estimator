"""Debug overlay PDF: text boxes, tag hits, path polylines, leader proposals."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz

from riser_extract.paths import PathSeg
from riser_extract.schema import ExtractionResult
from riser_extract.tags import TagHit


def write_overlay(
    src_pdf: str | Path,
    out_path: str | Path,
    *,
    tags: list[TagHit],
    paths: list[PathSeg],
    result: ExtractionResult,
    page_index: int = 0,
    max_paths: int = 400,
) -> Path:
    src = Path(src_pdf)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(src)
    page = doc[page_index]

    # Paths (sampled)
    for seg in paths[:max_paths]:
        if len(seg.points) < 2:
            continue
        color = seg.colour if seg.colour and len(seg.colour) >= 3 else (0, 0.6, 0.9)
        for (x0, y0), (x1, y1) in zip(seg.points, seg.points[1:]):
            page.draw_line(
                fitz.Point(x0, y0),
                fitz.Point(x1, y1),
                color=color[:3],
                width=0.6,
                overlay=True,
            )

    # Tag boxes
    for t in tags:
        page.draw_rect(
            fitz.Rect(t.x0, t.y0, t.x1, t.y1),
            color=(1, 0.4, 0),
            width=0.8,
            overlay=True,
        )
        page.insert_text(
            fitz.Point(t.x0, max(8, t.y0 - 2)),
            t.normalised[:40],
            fontsize=5,
            color=(0.8, 0.2, 0),
            overlay=True,
        )

    # Occurrence bboxes that are not tags
    for occ in result.occurrences:
        if not occ.pixel_bbox or len(occ.pixel_bbox) != 4:
            continue
        x0, y0, x1, y1 = occ.pixel_bbox
        page.draw_rect(
            fitz.Rect(x0, y0, x1, y1),
            color=(0.1, 0.5, 0.1),
            width=0.5,
            overlay=True,
        )

    # Title strip
    label = (
        f"{result.title_block.drawing_number or src.stem} | "
        f"{result.title_block.floor_tab_name} | {result.title_block.scale} | "
        f"tags={len(tags)} occ={len(result.occurrences)}"
    )
    page.insert_text(fitz.Point(24, 24), label, fontsize=8, color=(0, 0, 0), overlay=True)

    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out
