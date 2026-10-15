"""Open a plotted MEP PDF and expose page geometry, rotation, and CAD layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pymupdf as fitz


@dataclass
class PageInfo:
    path: Path
    page_index: int
    width_pt: float  # MediaBox width (unrotated)
    height_pt: float
    rotation: int
    display_width: float  # after rotation
    display_height: float
    layers: list[str] = field(default_factory=list)
    measure_m_per_cm: float | None = None
    m_per_pt: float | None = None
    producer: str | None = None
    creator: str | None = None


def _ocg_names(doc: fitz.Document) -> list[str]:
    names: list[str] = []
    try:
        ocgs = doc.get_ocgs() or {}
        for _xref, info in ocgs.items():
            name = (info or {}).get("name")
            if name:
                names.append(str(name))
    except Exception:
        pass
    return sorted(set(names))


def _measure_m_per_cm(page: fitz.Page) -> float | None:
    """Read PDF viewport Measure dictionary when present.

    Seneca AutoCAD plots store /C ≈ 0.5 meaning 1 cm on sheet = 0.5 m (1:50).
    """
    try:
        # PyMuPDF exposes viewports via page.get_drawings / raw dict inconsistently.
        # Fall back to parsing the page object string for /Measure ... /C <num>.
        xref = page.xref
        raw = page.parent.xref_object(xref)  # type: ignore[attr-defined]
    except Exception:
        raw = ""
    if not raw:
        try:
            raw = page.parent.xref_object(page.xref)
        except Exception:
            return None
    import re

    # AutoCAD Measure dicts put several /C values (often 1 for dimensionless
    # axes). The real-world X scale is the one near 0.5 for 1:50 (m per cm).
    # Values may be written as ".49949" without a leading zero.
    candidates = [float(x) for x in re.findall(r"/C\s+([0-9.]+)", raw)]
    usable = [c for c in candidates if 0.05 <= c <= 5.0]
    if not usable:
        return None
    # Prefer closest to 0.5 (1:50); fall back to closest to any N/100
    usable.sort(key=lambda c: abs(c - 0.5))
    return usable[0]


def open_page(pdf_path: str | Path, page_index: int = 0) -> tuple[fitz.Document, fitz.Page, PageInfo]:
    path = Path(pdf_path)
    doc = fitz.open(path)
    if page_index < 0 or page_index >= doc.page_count:
        doc.close()
        raise IndexError(f"page {page_index} out of range for {path} ({doc.page_count} pages)")
    page = doc[page_index]
    rot = int(page.rotation or 0)
    rect = page.mediabox  # unrotated
    w, h = float(rect.width), float(rect.height)
    # Displayed size after rotation (matches get_text / get_drawings frame)
    drect = page.rect
    measure = _measure_m_per_cm(page)
    m_per_pt = None
    if measure is not None:
        # 1 cm = 72/2.54 points ≈ 28.346 pt; measure is m per cm
        m_per_pt = measure / (72.0 / 2.54)
    meta = doc.metadata or {}
    info = PageInfo(
        path=path,
        page_index=page_index,
        width_pt=w,
        height_pt=h,
        rotation=rot,
        display_width=float(drect.width),
        display_height=float(drect.height),
        layers=_ocg_names(doc),
        measure_m_per_cm=measure,
        m_per_pt=m_per_pt,
        producer=meta.get("producer"),
        creator=meta.get("creator"),
    )
    return doc, page, info
