from __future__ import annotations

from fastapi import APIRouter

from app.config import db_path
from app.db import connect, migrate

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    migrate()
    conn = connect(readonly=True)
    try:
        n = conn.execute("SELECT COUNT(*) AS n FROM projects").fetchone()["n"]
        return {"ok": True, "db": str(db_path()), "project_count": n}
    finally:
        conn.close()
