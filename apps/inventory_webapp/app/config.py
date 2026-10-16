"""Webapp config — shares DATA_DIR / getriser.sqlite with the extractor."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DATA_DIR = Path("/Users/pico/workspace/data/getriser")


def data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", str(DEFAULT_DATA_DIR))).expanduser().resolve()


def db_path() -> Path:
    raw = os.environ.get("RISER_DB_PATH")
    if raw:
        return Path(raw).expanduser().resolve()
    return data_dir() / "getriser.sqlite"


def cors_origins() -> list[str]:
    raw = os.environ.get(
        "CORS_ORIGINS",
        "http://127.0.0.1:8870,http://localhost:8870,http://127.0.0.1:5173,http://localhost:5173",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


def resolve_pdf_path(stored: str | None) -> Path | None:
    """Map host absolute paths to container mount when DATA_DIR=/data."""
    if not stored:
        return None
    p = Path(stored)
    if p.exists():
        return p
    # Strip known host prefix and rejoin under current DATA_DIR
    marker = "/data/getriser/"
    s = stored.replace("\\", "/")
    if "/getriser/" in s:
        rel = s.split("/getriser/", 1)[1]
        cand = data_dir() / rel
        if cand.exists():
            return cand
    if s.startswith("/data/"):
        cand = Path(s)
        if cand.exists():
            return cand
    return p if p.exists() else None
