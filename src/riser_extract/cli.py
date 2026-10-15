"""CLI: riser-extract <pdf|dir> -o <out_dir>"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from riser_extract.pipeline import extract_and_write


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="riser-extract",
        description="Deterministic geometry & text extraction from MEP PDF drawings (Riser Phase 1).",
    )
    parser.add_argument("input", help="PDF file or directory of PDFs")
    parser.add_argument(
        "-o",
        "--out",
        default="out",
        help="Output directory (inventory_json/ + overlays/)",
    )
    parser.add_argument("--no-overlay", action="store_true", help="Skip overlay PDF")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    src = Path(args.input)
    if not src.exists():
        print(f"not found: {src}", file=sys.stderr)
        return 2

    pdfs = [src] if src.is_file() else sorted(src.glob("*.pdf"))
    if not pdfs:
        print(f"no PDFs under {src}", file=sys.stderr)
        return 2

    out = Path(args.out)
    for pdf in pdfs:
        result, json_path = extract_and_write(
            pdf, out, overlay=not args.no_overlay
        )
        s = result.summary()
        print(
            f"{pdf.name} → {json_path.name} | "
            f"{s['floor_tab_name']} | {s['scale']} | "
            f"occ={s['n_occurrences']} | backend={s['backend']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
