"""Annotated sheet export — boxes + class + confidence (MEPdetect-style audit)."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz

from riser_extract.schema import ExtractionResult

# Distinct colours per symbol class (RGB 0-1)
CLASS_COLOURS = {
    "fcu_wall": (0.05, 0.55, 0.95),
    "fcu_cass": (0.1, 0.7, 0.3),
    "hbc": (0.85, 0.35, 0.05),
    "panel_heater": (0.9, 0.1, 0.1),
    "door_curtain": (0.75, 0.05, 0.45),
    "ahu": (0.4, 0.2, 0.7),
    "ashp": (0.2, 0.5, 0.5),
    "tray_note": (0.95, 0.75, 0.1),
}


def write_annotated_png(
    src_pdf: str | Path,
    out_path: str | Path,
    *,
    result: ExtractionResult,
    page_index: int = 0,
    dpi: int = 110,
) -> Path:
    """Render page to PNG and burn in symbol boxes + labels."""
    src = Path(src_pdf)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(src)
    page = doc[page_index]
    # Draw on a copy via overlay annotations on a temp PDF then rasterize
    for sym in result.symbols:
        x0, y0, x1, y1 = sym.pixel_bbox
        colour = CLASS_COLOURS.get(sym.symbol_class, (0.2, 0.2, 0.2))
        width = 1.6 if not sym.amber_flag else 2.4
        page.draw_rect(
            fitz.Rect(x0, y0, x1, y1),
            color=colour,
            width=width,
            overlay=True,
        )
        label = f"{sym.symbol_class} {sym.confidence:.2f}"
        if sym.amber_flag:
            label = "AMBER " + label
        if sym.source:
            label += f" [{sym.source}]"
        page.insert_text(
            fitz.Point(x0, max(10, y0 - 2)),
            label[:48],
            fontsize=6,
            color=colour,
            overlay=True,
        )

    title = (
        f"{result.title_block.drawing_number} | {result.title_block.floor_tab_name} | "
        f"symbols={len(result.symbols)} amber="
        f"{sum(1 for s in result.symbols if s.amber_flag)}"
    )
    page.insert_text(fitz.Point(20, 18), title, fontsize=9, color=(0, 0, 0), overlay=True)

    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(str(out))
    doc.close()
    return out


def write_annotated_pdf(
    src_pdf: str | Path,
    out_path: str | Path,
    *,
    result: ExtractionResult,
    page_index: int = 0,
) -> Path:
    """Vector annotated PDF (same boxes as PNG)."""
    src = Path(src_pdf)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(src)
    page = doc[page_index]
    for sym in result.symbols:
        x0, y0, x1, y1 = sym.pixel_bbox
        colour = CLASS_COLOURS.get(sym.symbol_class, (0.2, 0.2, 0.2))
        page.draw_rect(fitz.Rect(x0, y0, x1, y1), color=colour, width=1.5, overlay=True)
        page.insert_text(
            fitz.Point(x0, max(10, y0 - 2)),
            f"{sym.symbol_class} {sym.confidence:.2f}",
            fontsize=6,
            color=colour,
            overlay=True,
        )
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out
