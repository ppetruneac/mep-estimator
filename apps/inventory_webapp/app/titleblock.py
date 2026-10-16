"""Derive project landing summary from drawing title blocks (bottom-left sheet data)."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter


def _mode(values: list[str | None]) -> str | None:
    cleaned = [v.strip() for v in values if v and str(v).strip()]
    if not cleaned:
        return None
    return Counter(cleaned).most_common(1)[0][0]


def _location_from_project_title(title: str | None) -> str | None:
    if not title:
        return None
    # "Hub by Premier Inn Putney" → Putney; "Something, London" → London
    if "," in title:
        return title.split(",")[-1].strip() or None
    parts = title.strip().split()
    if len(parts) >= 2:
        # Prefer last token when it looks like a place name
        last = parts[-1]
        if last[:1].isupper() and last.lower() not in {"ltd", "limited", "plc", "uk"}:
            return last
    return None


def _job_series(drawing_numbers: list[str]) -> list[str]:
    """e.g. 25280-SEN-02-DR-M-5602 → 25280-SEN"""
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


def project_titleblock_summary(conn: sqlite3.Connection, project_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT floor_tab_name, drawing_number, scale, revision, title_block_json
        FROM documents WHERE project_id = ?
        """,
        (project_id,),
    ).fetchall()

    projects, clients, stages, scales, papers, disclaimers, dates, revs = (
        [] for _ in range(8)
    )
    drawing_numbers: list[str] = []
    floors: list[str] = []

    for r in rows:
        drawing_numbers.append(r["drawing_number"] or "")
        if r["floor_tab_name"]:
            floors.append(r["floor_tab_name"])
        tb = {}
        if r["title_block_json"]:
            try:
                tb = json.loads(r["title_block_json"])
            except json.JSONDecodeError:
                tb = {}
        projects.append(tb.get("project"))
        clients.append(tb.get("client"))
        stages.append(tb.get("stage"))
        scales.append(tb.get("scale") or r["scale"])
        papers.append(tb.get("paper"))
        disclaimers.append(tb.get("disclaimer"))
        dates.append(tb.get("date"))
        revs.append(tb.get("revision") or r["revision"])

    display_name = _mode(projects)
    location = _location_from_project_title(display_name)
    return {
        "display_name": display_name,
        "location": location,
        "client": _mode(clients),
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
