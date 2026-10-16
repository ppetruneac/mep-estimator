"""CLI: riser-inventory seed-catalog | ingest | export | compare"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from riser_extract.config import data_dir, db_path, training_dir
from riser_extract.db.catalog import seed_catalog
from riser_extract.db.connection import connect, migrate
from riser_extract.db.upsert import ingest_path
from riser_extract.inventory.compare import compare_primary_counts, write_compare_report
from riser_extract.inventory.export_json import export_json
from riser_extract.inventory.export_xlsx import export_xlsx


def cmd_seed(args: argparse.Namespace) -> int:
    conn = migrate()
    n = seed_catalog(conn)
    print(f"seeded {n} catalog items → {db_path()}")
    conn.close()
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    conn = migrate()
    seed_catalog(conn)
    path = Path(args.input) if args.input else training_dir()
    results = ingest_path(
        conn,
        project_name=args.project,
        path=path,
        premise=args.premise,
        force=args.force,
    )
    for r in results:
        flag = "skip" if r["skipped_unchanged"] else "upsert"
        print(
            f"{flag} {r['drawing_number']} ({r['floor_tab_name']}) "
            f"occ={r['occurrences']} sym={r['n_symbols']}"
        )
    # Idempotence summary
    pid = results[0]["project_id"] if results else None
    if pid:
        docs = conn.execute(
            "SELECT COUNT(*) AS n FROM documents WHERE project_id = ?", (pid,)
        ).fetchone()["n"]
        occs = conn.execute(
            "SELECT COUNT(*) AS n FROM occurrences WHERE project_id = ?", (pid,)
        ).fetchone()["n"]
        print(f"project={args.project} documents={docs} occurrences={occs} db={db_path()}")
    conn.close()
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    conn = migrate()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    jp = export_json(conn, args.project, out / "inventory.json")
    xp = export_xlsx(conn, args.project, out / "inventory.xlsx")
    print(f"json → {jp}")
    print(f"xlsx → {xp}")
    conn.close()
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    conn = migrate()
    report = compare_primary_counts(conn, args.project)
    out = Path(args.out) if args.out else Path("evals/reports") / f"{report['date']}-inventory-compare.md"
    write_compare_report(report, out)
    print(out.read_text())
    conn.close()
    return 0 if report["passed"] else 1


def cmd_paths(_: argparse.Namespace) -> int:
    print(json.dumps(
        {
            "DATA_DIR": str(data_dir()),
            "RISER_DB_PATH": str(db_path()),
            "RISER_TRAINING_DIR": str(training_dir()),
        },
        indent=2,
    ))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="riser-inventory")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("paths", help="Show resolved DATA_DIR / DB paths")
    p.set_defaults(func=cmd_paths)

    p = sub.add_parser("seed-catalog", help="Upsert shared catalog_items from ids.CATALOGUE")
    p.set_defaults(func=cmd_seed)

    p = sub.add_parser("ingest", help="Extract PDFs and upsert into getriser.sqlite")
    p.add_argument("--project", required=True, help="Project name, e.g. HubbyPremierInnLondon")
    p.add_argument("input", nargs="?", help="PDF file or directory (default: RISER_TRAINING_DIR)")
    p.add_argument("--premise", default="mep")
    p.add_argument("--force", action="store_true", help="Re-extract even if content_hash matches")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("export", help="Write inventory.json + inventory.xlsx for a project")
    p.add_argument("--project", required=True)
    p.add_argument("-o", "--out", default="out/inventory")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("compare", help="Compare project counts to Hubby primary gates")
    p.add_argument("--project", required=True)
    p.add_argument("-o", "--out", default=None)
    p.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
