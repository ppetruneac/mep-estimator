"""CLI helpers for Phase 2: dataset export, optional YOLO train, decision log."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from riser_extract.dataset import export_yolo_dataset
from riser_extract.pipeline import extract_and_write
from riser_extract.symbols import RULE_SOLVED_CLASSES, YOLO_RESIDUAL_CANDIDATES
from riser_extract.yolo import mps_available, train_yolo


def _training_dir() -> Path:
    return Path(
        os.environ.get(
            "RISER_TRAINING_DIR",
            "/Users/pico/workspace/data/getriser/training-docs/HeatingandCooling/HubbyPremierInnLondon",
        )
    )


def cmd_extract(args: argparse.Namespace) -> int:
    src = Path(args.input)
    pdfs = [src] if src.is_file() else sorted(src.glob("*.pdf"))
    out = Path(args.out)
    for pdf in pdfs:
        result, path = extract_and_write(pdf, out, overlay=not args.no_overlay, annotated_png=True)
        s = result.summary()
        print(
            f"{pdf.name} → symbols={s['n_symbols']} "
            f"{s.get('symbols')} amber="
            f"{sum(1 for x in result.symbols if x.amber_flag)}"
        )
    return 0


def cmd_dataset(args: argparse.Namespace) -> int:
    training = Path(args.input) if args.input else _training_dir()
    pdfs = sorted(training.glob("*.pdf"))
    out = Path(args.out)
    export_yolo_dataset(pdfs, out, dpi=args.dpi, skip_amber=args.skip_amber)
    print(f"dataset → {out} ({len(pdfs)} pages)")
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    weights = train_yolo(
        args.dataset,
        out_dir=args.out,
        epochs=args.epochs,
        model=args.model,
        imgsz=args.imgsz,
    )
    print(f"weights → {weights} (mps={mps_available()})")
    return 0


def cmd_decision_log(args: argparse.Namespace) -> int:
    """Write the rules-vs-YOLO decision log from the latest symbol eval."""
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "date": date.today().isoformat(),
        "ticket": "GR-2",
        "rules_solved_classes": RULE_SOLVED_CLASSES,
        "yolo_residual_candidates": YOLO_RESIDUAL_CANDIDATES,
        "decision": (
            "On the Hubby Seneca H&C set, starter classes "
            "(FCU wall/cassette, HBC, panel heater, door curtain, AHU, ASHP, tray notes) "
            "are identified by deterministic rules: tag proximity + CAD layer + colour + "
            "compact geometry. YOLO is optional residual for roof-plant classes "
            "(ODU modules, dampers, valves) that lack stable tags on these sheets."
        ),
        "annotation_dataset": (
            "Rule proposals exported as YOLO-format boxes (weak labels guided by inventory "
            "counts). Amber boxes are low-confidence and intended for human correction."
        ),
        "mps_available": mps_available(),
        "evidence": args.evidence or [],
    }
    # Markdown
    lines = [
        f"# GR-2 decision log — {body['date']}",
        "",
        "## Decision",
        "",
        body["decision"],
        "",
        "## Classes solved by rules",
        "",
    ]
    for c in RULE_SOLVED_CLASSES:
        lines.append(f"- `{c}`")
    lines += ["", "## Residual candidates for YOLO (not required for Hubby H&C gates)", ""]
    for c in YOLO_RESIDUAL_CANDIDATES:
        lines.append(f"- `{c}`")
    lines += [
        "",
        "## Annotation dataset",
        "",
        body["annotation_dataset"],
        "",
        f"Apple MPS available for training: **{mps_available()}**",
        "",
    ]
    if args.evidence:
        lines += ["## Evidence artifacts", ""]
        for e in args.evidence:
            lines.append(f"- `{e}`")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(body, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="riser-symbols")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ex = sub.add_parser("extract", help="Extract + annotate sheets")
    p_ex.add_argument("input")
    p_ex.add_argument("-o", "--out", default="out/symbols")
    p_ex.add_argument("--no-overlay", action="store_true")
    p_ex.set_defaults(func=cmd_extract)

    p_ds = sub.add_parser("dataset", help="Export YOLO annotation dataset from rules")
    p_ds.add_argument("input", nargs="?", default=None)
    p_ds.add_argument("-o", "--out", default="evals/datasets/hubby-premier-inn-london/yolo")
    p_ds.add_argument("--dpi", type=int, default=110)
    p_ds.add_argument("--skip-amber", action="store_true")
    p_ds.set_defaults(func=cmd_dataset)

    p_tr = sub.add_parser("train", help="Optional YOLO11 fine-tune on the dataset")
    p_tr.add_argument("dataset")
    p_tr.add_argument("-o", "--out", default="evals/models/symbol_yolo")
    p_tr.add_argument("--epochs", type=int, default=30)
    p_tr.add_argument("--model", default="yolo11n.pt")
    p_tr.add_argument("--imgsz", type=int, default=1280)
    p_tr.set_defaults(func=cmd_train)

    p_dl = sub.add_parser("decision-log", help="Write rules-vs-YOLO decision log")
    p_dl.add_argument("-o", "--out", default="evals/reports/gr2-decision-log.md")
    p_dl.add_argument("--evidence", nargs="*", default=[])
    p_dl.set_defaults(func=cmd_decision_log)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
