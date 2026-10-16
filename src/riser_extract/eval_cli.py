"""CLI: riser-eval — run Hubby gold eval and write reports."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from riser_extract.pipeline import extract_drawing

REPO = Path(__file__).resolve().parents[2]
EVALS = REPO / "evals"
MANIFEST = EVALS / "datasets" / "hubby-premier-inn-london" / "manifest.json"
EXPECTED = EVALS / "datasets" / "hubby-premier-inn-london" / "expected" / "floors.json"
REPORTS = EVALS / "reports"


def _training_dir(manifest: dict) -> Path:
    import os

    return Path(os.environ.get(manifest["training_dir_env"], manifest["default_training_dir"]))


def _rel_err(pred: float, gold: float) -> float:
    if gold == 0:
        return 0.0 if pred == 0 else 1.0
    return abs(pred - gold) / abs(gold)


def _match_pdf(training: Path, drawing_number: str | None, floor: str) -> Path | None:
    pdfs = list(training.glob("*.pdf"))
    if drawing_number:
        # Normalise 560X / 5600 variants in filenames
        key = drawing_number.replace("DR-M-", "DR-M-").upper()
        for p in pdfs:
            name = p.name.upper().replace(" ", "")
            token = key.replace(" ", "")
            # Filename uses 560X / 5600 / 5602 etc.
            short = token.split("-")[-1]
            if short in name or token.replace("-", "")[:20] in name.replace("-", ""):
                if floor == "Basement" and "BASEMENT" in name:
                    return p
                if floor == "Ground Floor" and "GROUND" in name:
                    return p
                if floor == "Roof Plant" and "ROOF" in name:
                    return p
                if floor.replace(" ", "").upper() in name.replace(" ", ""):
                    return p
                if short in name and floor not in {"Basement", "Ground Floor", "Roof Plant"}:
                    # bedroom floors: M-5602 etc unique
                    return p
    # Filename floor fallback
    for p in pdfs:
        if floor.replace(" ", "").lower() in p.name.replace(" ", "").lower():
            return p
        if floor == "Basement" and "Basement" in p.name:
            return p
        if floor == "Roof Plant" and "Roof" in p.name:
            return p
    return None


def evaluate_floor(gold: dict, result) -> dict:
    pred_tags = set()
    for o in result.occurrences:
        for m in re.finditer(r"FCU\.[A-Z0-9]+\.\d{2}", o.annotation.upper()):
            pred_tags.add(m.group(0))
        for m in re.finditer(r"HB:[A-Z0-9]+:\d{2}", o.annotation.upper()):
            pred_tags.add(m.group(0))
        # Also normalised tags stored as annotation for FCU/HB
        if o.annotation.startswith("FCU.") or o.annotation.startswith("HB:"):
            pred_tags.add(o.annotation.upper())

    gold_tags = set(t.upper() for t in gold["tags"])
    # Only score FCU/HB tags
    gold_eq = {t for t in gold_tags if t.startswith("FCU.") or t.startswith("HB:")}
    pred_eq = {t for t in pred_tags if t.startswith("FCU.") or t.startswith("HB:")}
    hits = gold_eq & pred_eq
    recall = len(hits) / len(gold_eq) if gold_eq else 1.0
    precision = len(hits) / len(pred_eq) if pred_eq else 1.0

    fcu_pred = sum(1 for o in result.occurrences if o.item_id and "FCU" in o.item_id)
    hbc_pred = sum(1 for o in result.occurrences if o.item_id == "MEC-HBC")

    # Plan length comparison for rows with gold plan_m
    length_errors = []
    pred_plans = [
        o.length_m
        for o in result.occurrences
        if o.item_id == "MEC-CU-IN" and o.unit == "m" and o.length_m is not None
    ]
    gold_plans = [row["plan_m"] for row in gold.get("plan_lengths", []) if row.get("plan_m")]
    # Match by sorted order (both are per-FCU home-runs when present)
    if pred_plans and gold_plans and len(pred_plans) == len(gold_plans):
        for p, g in zip(sorted(pred_plans), sorted(gold_plans)):
            length_errors.append(_rel_err(p, g))
    elif pred_plans and gold_plans:
        # Compare totals
        length_errors.append(_rel_err(sum(pred_plans), sum(gold_plans)))

    tray_pred = sum(
        (o.length_m or 0.0)
        for o in result.occurrences
        if o.item_id and "TRAY" in o.item_id and o.unit == "m"
    )
    tray_gold_plan = None
    for row in gold.get("plan_lengths", []):
        if "tray" in row["annotation"].lower() or "TRAY" in row["annotation"]:
            tray_gold_plan = row["plan_m"]
            break
    # Basement headline H5 tender 34 → plan ≈ 34/1.15
    if tray_gold_plan is None:
        for h, meta in gold.get("headlines", {}).items():
            if "tray" in meta["annotation"].lower():
                tender = meta.get("tender") or meta.get("count")
                if tender:
                    tray_gold_plan = float(tender) / 1.15
                break

    tray_err = _rel_err(tray_pred, tray_gold_plan) if tray_gold_plan and tray_pred else None

    tb = result.title_block
    return {
        "floor": gold["floor_tab_name"],
        "drawing_number_match": (tb.drawing_number or "").upper()
        == (gold.get("drawing_number") or "").upper(),
        "pred_drawing_number": tb.drawing_number,
        "gold_drawing_number": gold.get("drawing_number"),
        "scale_ok": bool(tb.scale and "1:50" in tb.scale),
        "floor_match": tb.floor_tab_name == gold["floor_tab_name"],
        "tag_recall": round(recall, 4),
        "tag_precision": round(precision, 4),
        "missing_tags": sorted(gold_eq - pred_eq),
        "extra_tags": sorted(pred_eq - gold_eq),
        "fcu_pred": fcu_pred,
        "fcu_gold": gold.get("fcu_count"),
        "hbc_pred": hbc_pred,
        "hbc_gold": gold.get("hbc_count"),
        "plan_m_rel_errors": [round(e, 4) for e in length_errors],
        "plan_m_median_rel_error": round(sorted(length_errors)[len(length_errors) // 2], 4)
        if length_errors
        else None,
        "tray_pred_m": round(tray_pred, 2) if tray_pred else 0.0,
        "tray_gold_plan_m": round(tray_gold_plan, 2) if tray_gold_plan else None,
        "tray_rel_error": round(tray_err, 4) if tray_err is not None else None,
        "n_occurrences": len(result.occurrences),
    }


def run_eval(*, primary_only: bool = False) -> dict:
    manifest = json.loads(MANIFEST.read_text())
    if not EXPECTED.exists():
        # Generate expected on the fly
        from subprocess import check_call

        check_call([sys.executable, str(EVALS / "scripts" / "parse_ground_truth.py")])
    expected = json.loads(EXPECTED.read_text())["floors"]
    training = _training_dir(manifest)
    gates = manifest["gates"]
    primary = set(manifest["primary_floors"])

    floor_reports = []
    for floor, gold in expected.items():
        if primary_only and floor not in primary:
            continue
        pdf = _match_pdf(training, gold.get("drawing_number"), floor)
        if pdf is None:
            floor_reports.append({"floor": floor, "error": "pdf_not_found"})
            continue
        result = extract_drawing(pdf)
        floor_reports.append(evaluate_floor(gold, result))

    # Gate checks on primary floors
    failures = []
    for rep in floor_reports:
        if rep.get("error"):
            if rep["floor"] in primary:
                failures.append(f"{rep['floor']}: {rep['error']}")
            continue
        if rep["floor"] not in primary:
            continue
        if not rep["drawing_number_match"]:
            failures.append(f"{rep['floor']}: drawing_number mismatch")
        if not rep["scale_ok"]:
            failures.append(f"{rep['floor']}: scale not 1:50")
        if not rep["floor_match"]:
            failures.append(f"{rep['floor']}: floor tab mismatch")
        if rep["tag_recall"] < gates["tag_recall_primary"]:
            failures.append(
                f"{rep['floor']}: tag recall {rep['tag_recall']} < {gates['tag_recall_primary']}"
            )
        if rep["floor"] == "Basement":
            if rep["fcu_pred"] != gates["basement_fcu_count"]:
                failures.append(
                    f"Basement FCU {rep['fcu_pred']} != {gates['basement_fcu_count']}"
                )
            if rep["hbc_pred"] != gates["basement_hbc_count"]:
                failures.append(
                    f"Basement HBC {rep['hbc_pred']} != {gates['basement_hbc_count']}"
                )
            med = rep.get("plan_m_median_rel_error")
            if med is not None and med > gates["basement_plan_m_median_rel_error"]:
                failures.append(
                    f"Basement plan_m median rel err {med} > {gates['basement_plan_m_median_rel_error']}"
                )
            terr = rep.get("tray_rel_error")
            if terr is not None and terr > gates["basement_tray_rel_error"]:
                failures.append(
                    f"Basement tray rel err {terr} > {gates['basement_tray_rel_error']}"
                )
        if rep["floor"] == "Second Floor":
            if rep["fcu_pred"] != gates["second_fcu_count"]:
                failures.append(
                    f"Second Floor FCU {rep['fcu_pred']} != {gates['second_fcu_count']}"
                )
            if rep["hbc_pred"] != gates["second_hbc_count"]:
                failures.append(
                    f"Second Floor HBC {rep['hbc_pred']} != {gates['second_hbc_count']}"
                )

    passed = len(failures) == 0
    report = {
        "date": date.today().isoformat(),
        "dataset": manifest["name"],
        "passed": passed,
        "failures": failures,
        "floors": floor_reports,
    }
    return report


def write_report(report: dict) -> tuple[Path, Path]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = report["date"]
    json_path = REPORTS / f"{stamp}-hubby.json"
    md_path = REPORTS / f"{stamp}-hubby.md"
    latest = REPORTS / "latest.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        f"# Eval report — {report['dataset']} ({report['date']})",
        "",
        f"**Result:** {'PASS' if report['passed'] else 'FAIL'}",
        "",
    ]
    if report["failures"]:
        lines.append("## Failures")
        for f in report["failures"]:
            lines.append(f"- {f}")
        lines.append("")
    lines.append("## Floors")
    lines.append("")
    lines.append(
        "| Floor | Dwg | Scale | Recall | FCU p/g | HBC p/g | plan_m med err | tray err |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in report["floors"]:
        if r.get("error"):
            lines.append(f"| {r['floor']} | — | — | ERROR: {r['error']} | | | | |")
            continue
        lines.append(
            f"| {r['floor']} | {'✓' if r['drawing_number_match'] else '✗'} | "
            f"{'✓' if r['scale_ok'] else '✗'} | {r['tag_recall']:.2f} | "
            f"{r['fcu_pred']}/{r['fcu_gold']} | {r['hbc_pred']}/{r['hbc_gold']} | "
            f"{r['plan_m_median_rel_error'] if r['plan_m_median_rel_error'] is not None else '—'} | "
            f"{r['tray_rel_error'] if r['tray_rel_error'] is not None else '—'} |"
        )
    lines.append("")
    lines.append("## Missing tags (primary)")
    for r in report["floors"]:
        if r.get("missing_tags"):
            lines.append(f"- **{r['floor']}**: {', '.join(r['missing_tags'])}")
    lines.append("")
    md = "\n".join(lines)
    md_path.write_text(md, encoding="utf-8")
    latest.write_text(md, encoding="utf-8")
    return json_path, latest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="riser-eval")
    parser.add_argument("--primary-only", action="store_true")
    args = parser.parse_args(argv)
    report = run_eval(primary_only=args.primary_only)
    json_path, latest = write_report(report)
    print(latest.read_text())
    print(f"wrote {json_path}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
