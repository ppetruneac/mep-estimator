"""Compare project inventory against Hubby gold xlsx (count gates)."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import date
from pathlib import Path

# Reuse gold parser from evals if available
FCU_RE = re.compile(r"FCU[.\s:_-]*([A-Z0-9]+)[.\s:_-]*(\d{1,3})", re.I)
HB_RE = re.compile(r"\bHB[C]?[.\s:_-]*([A-Z0-9]+)[.\s:_-]*(\d{1,3})\b", re.I)


def _count_item(conn: sqlite3.Connection, project_id: int, item_ids: set[str], floor: str | None = None) -> float:
    sql = """
        SELECT SUM(
            CASE WHEN o.unit = 'm' THEN COALESCE(o.length_m, o.qty, 0) ELSE o.qty END
        ) AS n
        FROM occurrences o
        JOIN documents d ON d.id = o.document_id
        WHERE o.project_id = ? AND o.item_id IN ({})
    """.format(",".join("?" * len(item_ids)))
    params: list = [project_id, *item_ids]
    if floor:
        sql += " AND d.floor_tab_name = ?"
        params.append(floor)
    row = conn.execute(sql, params).fetchone()
    return float(row["n"] or 0)


def compare_primary_counts(conn: sqlite3.Connection, project_name: str) -> dict:
    """Hard gates aligned with GR-2 symbol counts vs Hubby gold."""
    proj = conn.execute(
        "SELECT id FROM projects WHERE name = ?", (project_name,)
    ).fetchone()
    if not proj:
        raise ValueError(f"unknown project: {project_name}")
    pid = proj["id"]

    checks = [
        ("Basement", "FCU", {"MEC-FCU-CASS", "MEC-FCU-WALL"}, 10),
        ("Basement", "HBC", {"MEC-HBC"}, 1),
        ("Basement", "PANEL", {"ELEC-PNL"}, 7),
        ("Second Floor", "FCU", {"MEC-FCU-WALL", "MEC-FCU-CASS"}, 31),
        ("Second Floor", "HBC", {"MEC-HBC"}, 2),
    ]
    results = []
    failures = []
    for floor, label, ids, expected in checks:
        # Count discrete printed equipment only (exclude geometry length rows)
        row = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM occurrences o
            JOIN documents d ON d.id = o.document_id
            WHERE o.project_id = ?
              AND d.floor_tab_name = ?
              AND o.item_id IN ({})
              AND o.unit = 'no.'
              AND COALESCE(o.symbol_class, '') != ''
            """.format(",".join("?" * len(ids))),
            [pid, floor, *ids],
        ).fetchone()
        # Fallback: count by item without requiring symbol_class
        if int(row["n"] or 0) == 0:
            row = conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM occurrences o
                JOIN documents d ON d.id = o.document_id
                WHERE o.project_id = ?
                  AND d.floor_tab_name = ?
                  AND o.item_id IN ({})
                  AND o.unit = 'no.'
                """.format(",".join("?" * len(ids))),
                [pid, floor, *ids],
            ).fetchone()
        got = int(row["n"] or 0)
        ok = got == expected
        results.append(
            {
                "floor": floor,
                "label": label,
                "expected": expected,
                "got": got,
                "ok": ok,
            }
        )
        if not ok:
            failures.append(f"{floor} {label}: got {got}, expected {expected}")

    # Catalog matched rate
    inv = conn.execute(
        "SELECT COUNT(*) AS n, SUM(CASE WHEN catalog_status = 'matched' THEN 1 ELSE 0 END) AS m FROM inventory_lines WHERE project_id = ?",
        (pid,),
    ).fetchone()
    catalog = {
        "lines": int(inv["n"] or 0),
        "matched": int(inv["m"] or 0),
    }

    # Traceability: inventory lines with qty>0 should have occurrences with bbox
    trace_fail = []
    for line in conn.execute(
        "SELECT item_id, qty_building FROM inventory_lines WHERE project_id = ? AND qty_building > 0",
        (pid,),
    ):
        n_bbox = conn.execute(
            """
            SELECT COUNT(*) AS n FROM occurrences
            WHERE project_id = ? AND item_id = ? AND pixel_bbox_json IS NOT NULL
            """,
            (pid, line["item_id"]),
        ).fetchone()["n"]
        if int(n_bbox or 0) < 1:
            trace_fail.append(line["item_id"])

    passed = not failures and not trace_fail
    return {
        "project": project_name,
        "date": date.today().isoformat(),
        "passed": passed,
        "failures": failures,
        "trace_missing_bbox": trace_fail,
        "checks": results,
        "catalog": catalog,
    }


def write_compare_report(report: dict, out_path: Path) -> Path:
    lines = [
        f"# Inventory compare — {report['project']} ({report['date']})",
        "",
        f"**Result:** {'PASS' if report['passed'] else 'FAIL'}",
        "",
        "## Count gates",
        "",
        "| Floor | Item | Expected | Got | OK |",
        "|---|---|---|---|---|",
    ]
    for c in report["checks"]:
        lines.append(
            f"| {c['floor']} | {c['label']} | {c['expected']} | {c['got']} | "
            f"{'✓' if c['ok'] else '✗'} |"
        )
    lines += [
        "",
        f"Catalog lines: {report['catalog']['lines']} matched: {report['catalog']['matched']}",
        "",
    ]
    if report["failures"]:
        lines.append("## Failures")
        for f in report["failures"]:
            lines.append(f"- {f}")
        lines.append("")
    if report["trace_missing_bbox"]:
        lines.append("## Missing bbox traceability")
        for i in report["trace_missing_bbox"]:
            lines.append(f"- `{i}`")
        lines.append("")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    out_path.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out_path
