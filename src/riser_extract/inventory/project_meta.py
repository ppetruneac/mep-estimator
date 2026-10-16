"""Project-level title-block / party summary for export + API consumers."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path

from riser_extract.scale import parse_parties


def _mode(values: list[str | None]) -> str | None:
    cleaned = [v.strip() for v in values if v and str(v).strip()]
    if not cleaned:
        return None
    return Counter(cleaned).most_common(1)[0][0]


def _parties_from_pdf(source_pdf: str | None) -> dict[str, str | None]:
    if not source_pdf:
        return {}
    path = Path(source_pdf)
    if not path.exists():
        return {}
    try:
        import pymupdf as fitz

        doc = fitz.open(path)
        try:
            text = doc[0].get_text("text")
        finally:
            doc.close()
        return parse_parties(text)
    except Exception:
        return {}


def enrich_document_title_block(conn: sqlite3.Connection, document_id: int) -> dict:
    """Re-parse parties from the PDF and merge into stored title_block_json."""
    row = conn.execute(
        "SELECT title_block_json, source_pdf FROM documents WHERE id = ?",
        (document_id,),
    ).fetchone()
    if not row:
        return {}
    tb = {}
    if row["title_block_json"]:
        try:
            tb = json.loads(row["title_block_json"])
        except json.JSONDecodeError:
            tb = {}
    parties = _parties_from_pdf(row["source_pdf"])
    changed = False
    for key, val in parties.items():
        if val and not tb.get(key):
            tb[key] = val
            changed = True
    if changed:
        conn.execute(
            "UPDATE documents SET title_block_json = ? WHERE id = ?",
            (json.dumps(tb), document_id),
        )
    return tb


def backfill_project_parties(conn: sqlite3.Connection, project_id: int) -> dict:
    """Ensure every document has party fields; return project-level consensus."""
    docs = conn.execute(
        "SELECT id FROM documents WHERE project_id = ?",
        (project_id,),
    ).fetchall()
    for d in docs:
        enrich_document_title_block(conn, d["id"])
    conn.commit()
    return project_meta(conn, project_id)


def project_meta(conn: sqlite3.Connection, project_id: int) -> dict:
    proj = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not proj:
        raise ValueError(f"unknown project id {project_id}")

    clients, architects, meps, mep_addrs, mep_webs, projects = ([] for _ in range(6))
    stages, scales, papers, disclaimers, dates, revs = ([] for _ in range(6))
    for d in conn.execute(
        "SELECT title_block_json, scale, revision, source_pdf FROM documents WHERE project_id = ?",
        (project_id,),
    ):
        tb = {}
        if d["title_block_json"]:
            try:
                tb = json.loads(d["title_block_json"])
            except json.JSONDecodeError:
                tb = {}
        # live fallback if still empty
        if not tb.get("client") or not tb.get("architect") or not tb.get("mep"):
            parties = _parties_from_pdf(d["source_pdf"])
            for k, v in parties.items():
                if v and not tb.get(k):
                    tb[k] = v
        projects.append(tb.get("project"))
        clients.append(tb.get("client"))
        architects.append(tb.get("architect"))
        meps.append(tb.get("mep"))
        mep_addrs.append(tb.get("mep_address"))
        mep_webs.append(tb.get("mep_web"))
        stages.append(tb.get("stage"))
        scales.append(tb.get("scale") or d["scale"])
        papers.append(tb.get("paper"))
        disclaimers.append(tb.get("disclaimer"))
        dates.append(tb.get("date"))
        revs.append(tb.get("revision") or d["revision"])

    owner = None
    if "owner" in proj.keys():
        owner = proj["owner"]
    owner = owner or _mode(meps) or "Seneca Group Ltd"

    display_name = _mode(projects)
    location = None
    if display_name:
        parts = display_name.strip().split()
        if parts:
            location = parts[-1]

    return {
        "id": proj["id"],
        "uuid": proj["uuid"] if "uuid" in proj.keys() else None,
        "name": proj["name"],
        "premise": proj["premise"],
        "owner": owner,
        "client": _mode(clients),
        "architect": _mode(architects),
        "mep": _mode(meps),
        "mep_address": _mode(mep_addrs),
        "mep_web": _mode(mep_webs),
        "display_name": display_name,
        "location": location,
        "stage": _mode(stages),
        "scale": _mode(scales),
        "paper": _mode(papers),
        "disclaimer": _mode(disclaimers),
        "revision": _mode(revs),
        "latest_date": _mode(dates),
    }
