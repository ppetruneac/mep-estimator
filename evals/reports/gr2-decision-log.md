# GR-2 decision log — 2026-10-16

## Decision

On the Hubby Seneca H&C set, starter classes are identified by deterministic rules (tag proximity + CAD layer + colour + compact geometry). Primary gates pass on symbol counts vs inventory. YOLO11n was fine-tuned for 15 epochs on Apple M4 Max MPS using rule-proposed weak labels (11 pages) to prove the training loop; mAP on this tiny same-split set is not a production metric. YOLO remains optional residual for untagged roof-plant classes (ODU modules, dampers, valves).

**Primary eval:** PASS — Basement Sym FCU 10 HBC 1 panel 7/7; Second Floor Sym FCU 31 HBC 2

**Apple MPS available:** True

## Classes solved by rules

- `fcu_wall`
- `fcu_cass`
- `hbc`
- `panel_heater`
- `door_curtain`
- `ahu`
- `ashp`
- `tray_note`

## Residual candidates for YOLO

- `odu_module`
- `damper`
- `valve`
- `smoke_extract_fan`
- `calorifier`

## Evidence symbol counts (rules)

| Floor | Symbols | Classes |
|---|---|---|
| Basement | 19 | `{"fcu_cass": {"count": 10, "avg_confidence": 0.9}, "hbc": {"count": 1, "avg_confidence": 0.6}, "panel_heater": {"count": 7, "avg_confidence": 0.627}, "tray_note": {"count": 1, "avg_confidence": 0.6}}` |
| Ground Floor | 2 | `{"door_curtain": {"count": 1, "avg_confidence": 0.75}, "panel_heater": {"count": 1, "avg_confidence": 0.82}}` |
| Second Floor | 34 | `{"fcu_wall": {"count": 31, "avg_confidence": 0.9}, "hbc": {"count": 2, "avg_confidence": 0.675}, "tray_note": {"count": 1, "avg_confidence": 0.6}}` |
| Fifth Floor | 34 | `{"fcu_wall": {"count": 31, "avg_confidence": 0.9}, "hbc": {"count": 2, "avg_confidence": 0.675}, "tray_note": {"count": 1, "avg_confidence": 0.6}}` |
| Ninth Floor | 11 | `{"fcu_wall": {"count": 9, "avg_confidence": 0.9}, "hbc": {"count": 1, "avg_confidence": 0.6}, "tray_note": {"count": 1, "avg_confidence": 0.75}}` |
| Roof Plant | 5 | `{"ahu": {"count": 3, "avg_confidence": 0.9}, "ashp": {"count": 2, "avg_confidence": 0.675}}` |

## Artifacts

- `evals/evidence/gr2/annotated/`
- `evals/evidence/gr2/overlays/`
- `evals/evidence/gr2/symbol_counts.json`
- `evals/datasets/hubby-premier-inn-london/yolo/manifest.json`
- `evals/datasets/hubby-premier-inn-london/yolo/labels/`
- `evals/models/symbol_yolo/best.pt`
- `evals/reports/latest.md`
