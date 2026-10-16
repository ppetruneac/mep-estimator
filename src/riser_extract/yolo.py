"""Optional YOLO residual path (GR-2).

Rules solve the Hubby starter classes. This module trains / runs YOLO11 only
when explicitly requested, using the rule-proposed annotation dataset.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from riser_extract.dataset import CLASS_TO_IDX, YOLO_CLASSES, export_yolo_dataset
from riser_extract.schema import SymbolDetection

log = logging.getLogger(__name__)


def mps_available() -> bool:
    try:
        import torch

        return bool(torch.backends.mps.is_available())
    except Exception:
        return False


def train_yolo(
    dataset_dir: str | Path,
    *,
    out_dir: str | Path,
    epochs: int = 40,
    model: str = "yolo11n.pt",
    imgsz: int = 1280,
) -> Path:
    """Fine-tune YOLO11 on the rule-proposed dataset. Returns best weights path."""
    from ultralytics import YOLO

    dataset_dir = Path(dataset_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_yaml = dataset_dir / "data.yaml"
    if not data_yaml.exists():
        raise FileNotFoundError(f"missing {data_yaml}; run dataset export first")

    device = "mps" if mps_available() else "cpu"
    log.info("Training YOLO on device=%s epochs=%s", device, epochs)
    yolo = YOLO(model)
    project = (out_dir / "ultralytics").resolve()
    project.mkdir(parents=True, exist_ok=True)
    yolo.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        device=device,
        project=str(project),
        name="symbol_yolo",
        exist_ok=True,
        patience=15,
        batch=4 if device == "mps" else 2,
        workers=0,
        verbose=True,
    )
    candidates = list(project.rglob("best.pt")) + list(Path.cwd().rglob("**/symbol_yolo/weights/best.pt"))
    # Prefer the newest best.pt under our project tree
    candidates = sorted({c.resolve() for c in candidates if c.exists()}, key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("YOLO training finished but best.pt not found")
    best_src = candidates[0]
    best = out_dir / "best.pt"
    best.write_bytes(best_src.read_bytes())
    meta = {
        "weights": str(best),
        "weights_src": str(best_src),
        "device": device,
        "epochs": epochs,
        "model": model,
        "classes": YOLO_CLASSES,
        "dataset": str(dataset_dir),
        "note": (
            "Short fine-tune on rule-proposed weak labels. Rules remain the "
            "production path for Hubby starter classes; YOLO is residual."
        ),
    }
    (out_dir / "train_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return best


def detect_yolo(
    weights: str | Path,
    image_path: str | Path,
    *,
    page_width: float,
    page_height: float,
    m_per_pt: float,
    conf: float = 0.25,
) -> list[SymbolDetection]:
    """Run YOLO on a rendered page image; return SymbolDetection in page-point space.

    ``image_path`` must be a raster of the displayed page. Bboxes are scaled
    from image pixels back to PDF points using page_width/height.
    """
    from ultralytics import YOLO

    yolo = YOLO(str(weights))
    results = yolo.predict(str(image_path), conf=conf, verbose=False)
    if not results:
        return []
    r0 = results[0]
    ih, iw = r0.orig_shape  # h, w
    sx = page_width / float(iw)
    sy = page_height / float(ih)
    out: list[SymbolDetection] = []
    names = r0.names or {i: n for i, n in enumerate(YOLO_CLASSES)}
    if r0.boxes is None:
        return []
    for box in r0.boxes:
        cls_id = int(box.cls.item())
        score = float(box.conf.item())
        x0, y0, x1, y1 = [float(v) for v in box.xyxy[0].tolist()]
        bbox = [x0 * sx, y0 * sy, x1 * sx, y1 * sy]
        cls_name = names.get(cls_id, YOLO_CLASSES[cls_id] if cls_id < len(YOLO_CLASSES) else str(cls_id))
        item_id = None
        from riser_extract.symbols import CLASS_TO_ITEM
        from riser_extract.ids import CATALOGUE

        item_id = CLASS_TO_ITEM.get(cls_name)
        legacy = CATALOGUE[item_id].legacy_item_id if item_id and item_id in CATALOGUE else None
        cx = 0.5 * (bbox[0] + bbox[2])
        cy = 0.5 * (bbox[1] + bbox[3])
        out.append(
            SymbolDetection(
                symbol_class=cls_name,
                item_id=item_id,
                legacy_item_id=legacy,
                confidence=round(score, 3),
                source="yolo",
                amber_flag=score < 0.45,
                pixel_bbox=[round(v, 2) for v in bbox],
                centroid_px=[round(cx, 2), round(cy, 2)],
                real_world_coords={
                    "x_m": round(cx * m_per_pt, 3),
                    "y_m": round((page_height - cy) * m_per_pt, 3),
                },
                notes="yolo residual/detection",
            )
        )
    return out


def build_dataset_from_training_dir(
    training_dir: str | Path,
    out_dir: str | Path,
    *,
    floors: list[str] | None = None,
) -> Path:
    training_dir = Path(training_dir)
    pdfs = sorted(training_dir.glob("*.pdf"))
    if floors:
        # filter by filename tokens
        keep = []
        for p in pdfs:
            name = p.name.lower()
            if any(f.lower().replace(" ", "") in name.replace(" ", "") for f in floors):
                keep.append(p)
            elif any(tok in name for tok in floors):
                keep.append(p)
        pdfs = keep or pdfs
    return export_yolo_dataset(pdfs, out_dir)
