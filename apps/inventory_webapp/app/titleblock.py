"""Derive project landing summary from drawing title blocks (sheet title block)."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from collections import Counter
from pathlib import Path

from app.config import resolve_pdf_path

log = logging.getLogger(__name__)


def _mode(values: list[str | None]) -> str | None:
    cleaned = [v.strip() for v in values if v and str(v).strip()]
    if not cleaned:
        return None
    return Counter(cleaned).most_common(1)[0][0]


def _location_from_project_title(title: str | None) -> str | None:
    if not title:
        return None
    if "," in title:
        return title.split(",")[-1].strip() or None
    parts = title.strip().split()
    if len(parts) >= 2:
        last = parts[-1]
        if last[:1].isupper() and last.lower() not in {"ltd", "limited", "plc", "uk"}:
            return last
    return None


def _job_series(drawing_numbers: list[str]) -> list[str]:
    series: list[str] = []
    seen: set[str] = set()
    for dn in drawing_numbers:
        m = re.match(r"^(\d{4,5}-[A-Z]{2,4})", dn or "", re.I)
        if not m:
            continue
        key = m.group(1).upper()
        if key not in seen:
            seen.add(key)
            series.append(key)
    return series


def _parties_from_pdf(source_pdf: str | None) -> dict[str, str | None]:
    """Fallback when stored title_block_json predates party parsing."""
    path = resolve_pdf_path(source_pdf)
    if not path or not path.exists():
        return {}
    try:
        import pymupdf as fitz
        from riser_extract.scale import parse_parties

        doc = fitz.open(path)
        try:
            text = doc[0].get_text("text")
        finally:
            doc.close()
        return parse_parties(text)
    except Exception as exc:  # pragma: no cover
        log.debug("party parse failed for %s: %s", path, exc)
        return {}


def project_titleblock_summary(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT floor_tab_name, drawing_number, scale, revision, title_block_json, source_pdf
        FROM documents WHERE project_id = ?
        """,
        (project_id,),
    ).fetchall()

    projects, clients, architects, meps, mep_addrs, mep_webs = ([] for _ in range(6))
    stages, scales, papers, disclaimers, dates, revs = ([] for _ in range(6))
    drawing_numbers: list[str] = []
    floors: list[str] = []
    pdf_paths: list[str] = []

    for r in rows:
        drawing_numbers.append(r["drawing_number"] or "")
        if r["floor_tab_name"]:
            floors.append(r["floor_tab_name"])
        if r["source_pdf"]:
            pdf_paths.append(r["source_pdf"])
        tb = {}
        if r["title_block_json"]:
            try:
                tb = json.loads(r["title_block_json"])
            except json.JSONDecodeError:
                tb = {}
        projects.append(tb.get("project"))
        clients.append(tb.get("client"))
        architects.append(tb.get("architect"))
        meps.append(tb.get("mep"))
        mep_addrs.append(tb.get("mep_address"))
        mep_webs.append(tb.get("mep_web"))
        stages.append(tb.get("stage"))
        scales.append(tb.get("scale") or r["scale"])
        papers.append(tb.get("paper"))
        disclaimers.append(tb.get("disclaimer"))
        dates.append(tb.get("date"))
        revs.append(tb.get("revision") or r["revision"])

    client = _mode(clients)
    architect = _mode(architects)
    mep = _mode(meps)
    mep_address = _mode(mep_addrs)
    mep_web = _mode(mep_webs)

    # Enrich from a live PDF when stored blocks lack party fields (pre-upgrade extracts)
    if not (client and architect and mep) and pdf_paths:
        parties = _parties_from_pdf(pdf_paths[0])
        client = client or parties.get("client")
        architect = architect or parties.get("architect")
        mep = mep or parties.get("mep")
        mep_address = mep_address or parties.get("mep_address")
        mep_web = mep_web or parties.get("mep_web")

    display_name = _mode(projects)
    location = _location_from_project_title(display_name)
    return {
        "display_name": display_name,
        "location": location,
        "client": client,
        "architect": architect,
        "mep": mep,
        "mep_address": mep_address,
        "mep_web": mep_web,
        "stage": _mode(stages),
        "scale": _mode(scales),
        "paper": _mode(papers),
        "disclaimer": _mode(disclaimers),
        "revision": _mode(revs),
        "latest_date": _mode(dates),
        "job_series": _job_series(drawing_numbers),
        "floors": floors,
        "drawing_count_from_blocks": len(rows),
    }
