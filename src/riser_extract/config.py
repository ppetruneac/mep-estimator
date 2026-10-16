"""Runtime paths for Riser extract / inventory.

Environment
-----------
DATA_DIR           Root data directory (default ``/Users/pico/workspace/data/getriser``)
RISER_DB_PATH      SQLite file (default ``$DATA_DIR/getriser.sqlite``)
RISER_TRAINING_DIR Training PDFs + gold xlsx (default under DATA_DIR)
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DATA_DIR = Path("/Users/pico/workspace/data/getriser")


def data_dir() -> Path:
    raw = os.environ.get("DATA_DIR", str(DEFAULT_DATA_DIR))
    return Path(raw).expanduser().resolve()


def db_path() -> Path:
    raw = os.environ.get("RISER_DB_PATH")
    if raw:
        return Path(raw).expanduser().resolve()
    return data_dir() / "getriser.sqlite"


def training_dir() -> Path:
    raw = os.environ.get("RISER_TRAINING_DIR")
    if raw:
        return Path(raw).expanduser().resolve()
    return data_dir() / "training-docs" / "HeatingandCooling" / "HubbyPremierInnLondon"


def exports_dir(project: str | None = None) -> Path:
    base = data_dir() / "exports"
    return base / project if project else base
