#!/usr/bin/env python3
"""Parse Hubby last.xlsx into expected/*.json for the eval harness."""

from __future__ import annotations

import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
FCU_RE = re.compile(r"FCU[.\s:_-]*([A-Z0-9]+)[.\s:_-]*(\d{1,3})", re.I)
FCU_RANGE_RE = re.compile(
    r"FCU[.\s:_-]*([A-Z0-9]+)[.\s:_-]*(\d{1,3})\s*(?:to|–|-|—)\s*FCU[.\s:_-]*([A-Z0-9]+)[.\s:_-]*(\d{1,3})",
    re.I,
)
HB_RE = re.compile(r"HB[C]?[.\s:_-]*([A-Z0-9]+)[.\s:_-]*(\d{1,3})", re.I)
HB_PLUS_RE = re.compile(
    r"HB[C]?[.\s:_-]*([A-Z0-9]+)[.\s:_-]*(\d{1,3})\s*\+\s*HB[C]?[.\s:_-]*([A-Z0-9]+)[.\s:_-]*(\d{1,3})",
    re.I,
)
PLAN_M_RE = re.compile(r"(\d+(?:\.\d+)?)\s*m\s+plan", re.I)
AVG_PLAN_RE = re.compile(r"Avg(?:erage)?\s+plan\s+(\d+(?:\.\d+)?)\s*m", re.I)
SUM_PLAN_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)\s*\+\s*15%",
    re.I,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "datasets" / "hubby-premier-inn-london" / "manifest.json"
OUT = ROOT / "datasets" / "hubby-premier-inn-london" / "expected"


def _cell_val(c):
    is_el = c.find("m:is", NS)
    v = c.find("m:v", NS)
    if is_el is not None:
        return "".join(x.text or "" for x in is_el.findall(".//m:t", NS))
    if v is not None:
        return v.text
    return None


def _colrow(ref: str):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return m.group(1), int(m.group(2))


def load_sheet(z: zipfile.ZipFile, xml_path: str):
    root = ET.fromstring(z.read(xml_path))
    rows: dict[int, dict[str, str]] = defaultdict(dict)
    maxr = 0
    for c in root.findall(".//m:c", NS):
        ref = c.attrib.get("r")
        if not ref:
            continue
        col, row = _colrow(ref)
        val = _cell_val(c)
        if val is None:
            continue
        rows[row][col] = val
        maxr = max(maxr, row)
    return rows, maxr


def parse_plan_m(notes: str, tender: float | None) -> float | None:
    if not notes:
        return None
    m = PLAN_M_RE.search(notes)
    if m:
        return float(m.group(1))
    m = AVG_PLAN_RE.search(notes)
    if m:
        return float(m.group(1))
    m = SUM_PLAN_RE.search(notes)
    if m:
        return sum(float(x) for x in m.groups())
    # tender_m ≈ plan*2*1.15 + 3 → plan ≈ (tender - 3) / 2.3
    if tender and tender > 3:
        # Only for pair runs that mention 15% / tails
        if "15%" in notes or "tails" in notes.lower() or "× 2" in notes or "x 2" in notes.lower():
            return round((tender - 3.0) / 2.3, 2)
        if "1.15" in notes:
            return round(tender / 1.15, 2)
    return None


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    training = Path(
        __import__("os").environ.get(
            manifest["training_dir_env"], manifest["default_training_dir"]
        )
    )
    xlsx = training / manifest["gold_xlsx"]
    if not xlsx.exists():
        raise SystemExit(f"gold xlsx not found: {xlsx}")

    z = zipfile.ZipFile(xlsx)
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    sheets = []
    for i, s in enumerate(wb.findall("m:sheets/m:sheet", NS), start=1):
        sheets.append((s.attrib["name"], f"xl/worksheets/sheet{i}.xml"))

    floors: dict[str, dict] = {}
    for name, xml_path in sheets:
        if name == "Summary" or name in manifest["skip_floors"]:
            continue
        rows, maxr = load_sheet(z, xml_path)
        header = " ".join(str(rows[r].get("A", "")) for r in range(1, 7))
        tags = []
        plan_lengths = []
        headlines = {}
        for r in range(8, maxr + 1):
            a = rows[r].get("A", "")
            b = rows[r].get("B", "")
            g = rows[r].get("G", "")
            i = rows[r].get("I", "")
            notes = i or ""
            try:
                tender = float(g) if g not in ("", None, "—", "-") else None
            except ValueError:
                tender = None

            # FCU ranges often live in Notes ("FCU.02.01 to FCU.02.31")
            for m in FCU_RANGE_RE.finditer(f"{b} {notes}"):
                lvl_a, n0, lvl_b, n1 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
                if lvl_a.upper() == lvl_b.upper():
                    for n in range(min(n0, n1), max(n0, n1) + 1):
                        tags.append(f"FCU.{lvl_a.upper()}.{n:02d}")
            for m in FCU_RE.finditer(b):
                tags.append(f"FCU.{m.group(1).upper()}.{int(m.group(2)):02d}")
            # HB tags only from the annotation column — notes create false hits
            for m in HB_PLUS_RE.finditer(b):
                tags.append(f"HB:{m.group(1).upper()}:{int(m.group(2)):02d}")
                tags.append(f"HB:{m.group(3).upper()}:{int(m.group(4)):02d}")
            for m in HB_RE.finditer(b):
                lvl = m.group(1)
                if lvl.upper() in {"CONTROLLER", "CONT", "BOX", "BOXES", "CONTROLLERS"}:
                    continue
                # Require a level token that looks like a floor code (0B, 02, B, …)
                if not re.match(r"^(?:0?[B0-9]{1,2}|[0-9]{1,2})$", lvl, re.I):
                    continue
                tags.append(f"HB:{lvl.upper()}:{int(m.group(2)):02d}")

            plan = parse_plan_m(notes, tender)
            if plan is not None and ("F+R" in b or "pair" in b.lower() or "plan" in notes.lower()):
                plan_lengths.append(
                    {
                        "line": a,
                        "annotation": b[:120],
                        "plan_m": plan,
                        "tender_m": tender,
                        "notes": notes[:200],
                    }
                )

            if a.startswith("H") and a[1:].isdigit():
                try:
                    headlines[a] = {
                        "annotation": b,
                        "count": float(rows[r].get("D") or 0),
                        "tender": tender,
                    }
                except ValueError:
                    pass

        # drawing number from header
        dwg = None
        m = re.search(
            r"(25280-SEN-(?:0X|\d{2})-DR-M-\d{3,5}[A-Z]?|25287-SEN-00-DR-M-\d{3,5})",
            header,
            re.I,
        )
        if m:
            dwg = m.group(1).upper()

        fcu_count = len({t for t in tags if t.startswith("FCU.")})
        hbc_count = len({t for t in tags if t.startswith("HB:")})
        # Bedroom floors often list "FCU.02.01 to FCU.02.31" in notes; if range
        # parse failed, fall back to H1 wall-VRF / FCU headline count.
        if fcu_count == 0:
            for meta in headlines.values():
                ann = meta["annotation"].lower()
                if "fcu" in ann or "vrf" in ann or "wall mounted" in ann:
                    if meta["count"] and meta["count"] > 1:
                        fcu_count = int(meta["count"])
                        break
        if hbc_count == 0:
            for meta in headlines.values():
                if "hbc" in meta["annotation"].lower():
                    if meta["count"]:
                        hbc_count = int(meta["count"])
                        break

        floors[name] = {
            "floor_tab_name": name,
            "drawing_number": dwg,
            "scale": "1:50 @ A1" if "1:50" in header or "1:50" in str(rows.get(3, {}).get("A", "")) else None,
            "header": header[:400],
            "tags": sorted(set(tags)),
            "fcu_count": fcu_count,
            "hbc_count": hbc_count,
            "plan_lengths": plan_lengths,
            "headlines": headlines,
        }

    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / "floors.json"
    out_path.write_text(json.dumps({"floors": floors}, indent=2), encoding="utf-8")
    print(f"wrote {out_path} ({len(floors)} floors)")
    for name, f in floors.items():
        print(
            f"  {name}: dwg={f['drawing_number']} fcu={f['fcu_count']} "
            f"hbc={f['hbc_count']} plan_rows={len(f['plan_lengths'])}"
        )


if __name__ == "__main__":
    main()
