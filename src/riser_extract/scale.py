"""Scale and title-block parsing from text + PDF Measure dict."""

from __future__ import annotations

import re
from dataclasses import dataclass

from riser_extract.page import PageInfo

SCALE_RE = re.compile(
    r"(?P<ratio>1\s*:\s*(?P<n>\d{1,4}))\s*(?:@\s*(?P<paper>A[0-4]))?",
    re.IGNORECASE,
)
DRAWING_NO_RE = re.compile(
    r"\b(\d{4,5}-[A-Z]{2,4}(?:-\d{1,2}|-0X)?-DR-[A-Z]-\d{3,5}[A-Z]?)\b",
    re.IGNORECASE,
)
# Also catch forms like 25280-SEN-0X-DR-M-560X
DRAWING_NO_RE2 = re.compile(
    r"\b(\d{4,5}-SEN-(?:0X|\d{2}|00)-\s*DR-?\s*M-?\s*\d{3,5}[A-Z]?)\b",
    re.IGNORECASE,
)
REV_RE = re.compile(r"\bRev(?:ision)?\s*[:\s]*(P?\d+|[A-Z])\b", re.IGNORECASE)
STAGE_RE = re.compile(r"\bStage\s*([0-9])\b", re.IGNORECASE)
DATE_RE = re.compile(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b")

FLOOR_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bBASEMENT\b", re.I), "Basement"),
    (re.compile(r"\bGROUND\s+FLOOR\b", re.I), "Ground Floor"),
    (re.compile(r"\bFIRST\s+FLOOR\b", re.I), "First Floor"),
    (re.compile(r"\bSECOND\s+FLOOR\b", re.I), "Second Floor"),
    (re.compile(r"\bTHIRD\s+FLOOR\b", re.I), "Third Floor"),
    (re.compile(r"\bFOURTH\s+FLOOR\b", re.I), "Fourth Floor"),
    (re.compile(r"\bFIFTH\s+FLOOR\b", re.I), "Fifth Floor"),
    (re.compile(r"\bSIXTH\s+FLOOR\b", re.I), "Sixth Floor"),
    (re.compile(r"\bSEVENTH\s+FLOOR\b", re.I), "Seventh Floor"),
    (re.compile(r"\bEIGHTH\s+FLOOR\b", re.I), "Eighth Floor"),
    (re.compile(r"\bNINTH\s+FLOOR\b", re.I), "Ninth Floor"),
    (re.compile(r"\bROOF\s+PLANT\b", re.I), "Roof Plant"),
    (re.compile(r"\bROOF\b", re.I), "Roof Plant"),
]

FILENAME_FLOOR: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"Basement", re.I), "Basement"),
    (re.compile(r"Ground\s*Floor", re.I), "Ground Floor"),
    (re.compile(r"Second\s*Floor", re.I), "Second Floor"),
    (re.compile(r"Third\s*Floor", re.I), "Third Floor"),
    (re.compile(r"Fourth\s*Floor", re.I), "Fourth Floor"),
    (re.compile(r"Fifth\s*Floor", re.I), "Fifth Floor"),
    (re.compile(r"Sixth\s*Floor", re.I), "Sixth Floor"),
    (re.compile(r"Seventh\s*Floor", re.I), "Seventh Floor"),
    (re.compile(r"Eighth\s*Floor", re.I), "Eighth Floor"),
    (re.compile(r"Ninth\s*Floor", re.I), "Ninth Floor"),
    (re.compile(r"Roof\s*Plant|Roof", re.I), "Roof Plant"),
]

FILENAME_DWG = re.compile(
    r"(25280-SEN-(?:0X|\d{2})-DR-M-\d{3,5}[A-Z]?|25287-SEN-00-DR-M-\d{3,5})",
    re.IGNORECASE,
)


@dataclass
class ScaleInfo:
    scale_str: str  # e.g. "1:50 @ A1"
    ratio: int  # 50
    paper: str | None
    m_per_pt: float
    measure_m_per_cm: float | None
    source: str  # measure | title | default


def m_per_pt_from_ratio(ratio: int) -> float:
    """1 PDF point = 0.3528 mm on paper; at 1:N that is N/1000 * 0.3528 metres."""
    return (ratio / 1000.0) * 0.3528


def resolve_scale(page_info: PageInfo, full_text: str) -> ScaleInfo:
    measure = page_info.measure_m_per_cm
    m = SCALE_RE.search(full_text)
    if m:
        ratio = int(m.group("n"))
        paper = m.group("paper")
        scale_str = f"1:{ratio}" + (f" @ {paper.upper()}" if paper else "")
        if measure is not None:
            m_per_pt = measure / (72.0 / 2.54)
            source = "measure+title"
        else:
            m_per_pt = m_per_pt_from_ratio(ratio)
            source = "title"
        return ScaleInfo(scale_str, ratio, paper.upper() if paper else None, m_per_pt, measure, source)

    if measure is not None:
        # Infer ratio from measure: m_per_cm = N/100 → N = measure * 100
        ratio = int(round(measure * 100))
        m_per_pt = measure / (72.0 / 2.54)
        return ScaleInfo(f"1:{ratio}", ratio, "A1", m_per_pt, measure, "measure")

    # Seneca H&C plots in this set are 1:50 @ A1
    return ScaleInfo("1:50 @ A1", 50, "A1", m_per_pt_from_ratio(50), None, "default")


def parse_drawing_number(full_text: str, filename: str) -> str | None:
    for rx in (DRAWING_NO_RE, DRAWING_NO_RE2):
        m = rx.search(full_text)
        if m:
            return re.sub(r"\s+", "", m.group(1)).upper().replace("DR-M", "DR-M")
    m = FILENAME_DWG.search(filename)
    if m:
        return m.group(1).upper()
    return None


def parse_floor_tab(full_text: str, filename: str) -> str | None:
    """Resolve floor tab name.

    Filename wins when it clearly names a floor — sheet notes often mention
    other levels (e.g. a roof plant drawing that references the basement).
    """
    for rx, name in FILENAME_FLOOR:
        if rx.search(filename):
            return name
    upper = full_text.upper()
    # Prefer the most specific title hit; check Roof before bare patterns that
    # may appear in cross-references.
    hits = [(name, rx.search(upper) is not None) for rx, name in FLOOR_PATTERNS]
    for name, ok in hits:
        if ok and name == "Roof Plant":
            return name
    for name, ok in hits:
        if ok:
            return name
    return None


def parse_title_fields(full_text: str) -> dict[str, str | None]:
    rev = REV_RE.search(full_text)
    stage = STAGE_RE.search(full_text)
    date = DATE_RE.search(full_text)
    disclaimer = None
    if re.search(r"DO\s+NOT\s+SCALE", full_text, re.I):
        disclaimer = "DO NOT SCALE"
    project = None
    if re.search(r"PREMIER\s+INN|HUB\s+BY", full_text, re.I):
        project = "Hub by Premier Inn Putney"
    return {
        "revision": rev.group(1) if rev else None,
        "stage": f"Stage {stage.group(1)}" if stage else None,
        "date": date.group(1) if date else None,
        "disclaimer": disclaimer,
        "project": project,
    }


def normalise_drawing_number(raw: str | None) -> str | None:
    if not raw:
        return None
    s = re.sub(r"\s+", "", raw).upper()
    # Fix common OCR/spacing: 25280-SEN-0X-DR-M-560X
    s = s.replace("DR-M-", "DR-M-")
    return s
