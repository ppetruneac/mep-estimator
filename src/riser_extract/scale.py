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


def parse_parties(full_text: str) -> dict[str, str | None]:
    """Architect / client / MEP from title-block labels and nearby lines."""
    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
    upper_lines = [ln.upper() for ln in lines]

    def after_label(label: str) -> str | None:
        for i, u in enumerate(upper_lines):
            if u == label or u.startswith(label + " ") or u.startswith(label + ":"):
                # same line after colon
                if ":" in lines[i]:
                    rest = lines[i].split(":", 1)[1].strip(" :-")
                    if rest and len(rest) > 1:
                        return rest
                # next non-empty content line(s)
                for j in range(i + 1, min(i + 4, len(lines))):
                    cand = lines[j].strip(" :-")
                    if not cand:
                        continue
                    if cand.upper() in {"ARCHITECT", "CLIENT", "ENGINEER", "MEP", "DRAWN", "CHECKED", "REV", "SCALE", "DATE", "TITLE", "PROJECT", "DISCLAIMER"}:
                        continue
                    if cand.upper().startswith(("ARCHITECT", "CLIENT", "SCALE", "DATE", "DRAWING", "REV")):
                        continue
                    return cand
        return None

    client = after_label("CLIENT")
    # Title block order is often ARCHITECT: / CLIENT: / Mosser / curio email…
    # so the first content after ARCHITECT may be the client name — prefer Curio contacts.
    architect = None
    if re.search(r"([\w.-]+@curioarchitects\.co\.uk|www\.curioarchitects\.co\.uk)", full_text, re.I):
        architect = "Curio Architects"
    if not architect:
        architect = after_label("ARCHITECT")
        if architect and "@" in architect:
            domain = architect.split("@", 1)[1].split("/", 1)[0]
            host = domain.split(".")[0]
            if "curio" in host.lower():
                architect = "Curio Architects"
            else:
                architect = host.replace("-", " ").title()
    # If ARCHITECT resolved to the same string as CLIENT, drop it
    if architect and client and architect.upper().rstrip(".") == client.upper().rstrip("."):
        architect = None
        if re.search(r"curioarchitects", full_text, re.I):
            architect = "Curio Architects"

    mep = None
    mep_address = None
    mep_web = None
    m = re.search(r"\bSeneca\s+Group\s+Ltd\b", full_text, re.I)
    if m:
        mep = "Seneca Group Ltd"
    if not mep:
        m = re.search(r"\b(Seneca\s+(?:Engineering\s+)?(?:Group\s+)?Ltd)\b", full_text, re.I)
        if m:
            mep = re.sub(r"\s+", " ", m.group(1)).strip()
    addr = re.search(
        r"(4th\s+Floor,\s+Silverstream\s+House,[^\n]+Fitzrovia[^\n]*)",
        full_text,
        re.I,
    )
    if addr:
        mep_address = re.sub(r"\s+", " ", addr.group(1)).strip(" ,")
    web = re.search(r"(www\.senecagrp\.com)", full_text, re.I)
    if web:
        mep_web = web.group(1).lower()

    # Normalise client casing
    if client:
        client = re.sub(r"\s+", " ", client).strip()
        if client.isupper() and len(client) < 40:
            client = client.title().replace("Ltd", "Ltd")

    return {
        "client": client,
        "architect": architect,
        "mep": mep,
        "mep_address": mep_address,
        "mep_web": mep_web,
    }


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
    out: dict[str, str | None] = {
        "revision": rev.group(1) if rev else None,
        "stage": f"Stage {stage.group(1)}" if stage else None,
        "date": date.group(1) if date else None,
        "disclaimer": disclaimer,
        "project": project,
    }
    out.update(parse_parties(full_text))
    return out


def normalise_drawing_number(raw: str | None) -> str | None:
    if not raw:
        return None
    s = re.sub(r"\s+", "", raw).upper()
    # Fix common OCR/spacing: 25280-SEN-0X-DR-M-560X
    s = s.replace("DR-M-", "DR-M-")
    return s
