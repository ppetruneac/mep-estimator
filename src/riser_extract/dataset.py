"""Build a YOLO-format annotation dataset from rule proposals (weak labels).

Inventories guide *what* and *how many*; boxes come from Phase 2 rules.
Humans can correct amber boxes later (active learning).
"""

from __future__ import annotations

import json
from pathlib import Path

import pymupdf as fitz

from riser_extract.pipeline import extract_drawing
from riser_extract.symbols import (
    CLASS_AHU,
    CLASS_ASHP,
    CLASS_CURTAIN,
    CLASS_FCU_CASS,
    CLASS_FCU_WALL,
    CLASS_HBC,
    CLASS_PANEL,
    CLASS_TRAY,
)

# Stable class index for YOLO data.yaml
YOLO_CLASSES = [
    CLASS_FCU_WALL,
    CLASS_FCU_CASS,
    CLASS_HBC,
    CLASS_PANEL,
    CLASS_CURTAIN,
    CLASS_AHU,
    CLASS_ASHP,
    CLASS_TRAY,
]
CLASS_TO_IDX = {c: i for i, c in enumerate(YOLO_CLASSES)}


def _yolo_line(cls_idx: int, bbox: list[float], page_w: float, page_h: float) -> str:
    x0, y0, x1, y1 = bbox
    cx = ((x0 + x1) / 2) / page_w
    cy = ((y0 + y1) / 2) / page_h
    w = (x1 - x0) / page_w
    h = (y1 - y0) / page_h
    # clamp
    cx, cy, w, h = [max(0.0, min(1.0, v)) for v in (cx, cy, w, h)]
    return f"{cls_idx} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"


def export_yolo_dataset(
    pdfs: list[Path],
    out_dir: str | Path,
    *,
    dpi: int = 110,
    skip_amber: bool = False,
) -> Path:
    """Render each PDF page + write YOLO labels next to images."""
    out = Path(out_dir)
    images = out / "images"
    labels = out / "labels"
    images.mkdir(parents=True, exist_ok=True)
    labels.mkdir(parents=True, exist_ok=True)

    meta = []
    for pdf in pdfs:
        result = extract_drawing(pdf)
        slug = (result.title_block.drawing_number or pdf.stem).replace(" ", "")
        floor = result.title_block.floor_tab_name or "unknown"
        stem = f"{slug}_{floor.replace(' ', '_')}"

        doc = fitz.open(pdf)
        page = doc[0]
        page_w, page_h = float(page.rect.width), float(page.rect.height)
        zoom = dpi / 72.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        img_path = images / f"{stem}.png"
        pix.save(str(img_path))
        doc.close()

        lines = []
        kept = 0
        for sym in result.symbols:
            if skip_amber and sym.amber_flag:
                continue
            idx = CLASS_TO_IDX.get(sym.symbol_class)
            if idx is None:
                continue
            lines.append(_yolo_line(idx, sym.pixel_bbox, page_w, page_h))
            kept += 1
        lab_path = labels / f"{stem}.txt"
        lab_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

        meta.append(
            {
                "pdf": str(pdf),
                "image": str(img_path.relative_to(out)),
                "label": str(lab_path.relative_to(out)),
                "floor": floor,
                "drawing_number": result.title_block.drawing_number,
                "n_symbols": len(result.symbols),
                "n_labels": kept,
                "symbol_summary": result.summary().get("symbols", {}),
            }
        )

    data_yaml = {
        "path": str(out.resolve()),
        "train": "images",
        "val": "images",
        "names": {i: n for i, n in enumerate(YOLO_CLASSES)},
    }
    # Ultralytics wants a real yaml file
    yaml_path = out / "data.yaml"
    yaml_lines = [
        f"path: {out.resolve()}",
        "train: images",
        "val: images",
        "names:",
    ]
    for i, n in enumerate(YOLO_CLASSES):
        yaml_lines.append(f"  {i}: {n}")
    yaml_path.write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")

    (out / "manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (out / "classes.json").write_text(
        json.dumps({"classes": YOLO_CLASSES, "data_yaml": data_yaml}, indent=2),
        encoding="utf-8",
    )
    return out
