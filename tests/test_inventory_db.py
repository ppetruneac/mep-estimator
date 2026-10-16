"""GR-3 SQLite upsert + catalog tests (tmp DB, synthetic extract fixture)."""

from __future__ import annotations

from pathlib import Path

import pytest

from riser_extract.db.catalog import lookup, seed_catalog
from riser_extract.db.connection import connect, migrate
from riser_extract.db.upsert import ensure_project, ingest_pdf
from riser_extract.ids import CATALOGUE


FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_hvac.pdf"


@pytest.fixture()
def db(tmp_path: Path):
    path = tmp_path / "getriser.sqlite"
    conn = connect(path)
    migrate(conn)
    seed_catalog(conn)
    yield conn, path
    conn.close()


def test_seed_catalog_matched(db):
    conn, _ = db
    assert len(CATALOGUE) >= 10
    row = lookup(conn, "MEC-FCU-WALL")
    assert row is not None
    assert row["catalog_sku"]
    assert row["legacy_item_id"] == "HC-FCU-WALL"


def test_ensure_project_premise_default_mep(db):
    conn, _ = db
    pid = ensure_project(conn, "DemoProject")
    row = conn.execute("SELECT premise FROM projects WHERE id = ?", (pid,)).fetchone()
    assert row["premise"] == "mep"
    # second call upserts same id
    pid2 = ensure_project(conn, "DemoProject")
    assert pid == pid2
    n = conn.execute("SELECT COUNT(*) AS n FROM projects WHERE name = 'DemoProject'").fetchone()["n"]
    assert n == 1


def test_ingest_upsert_idempotent(db):
    conn, _ = db
    if not FIXTURE.exists():
        pytest.skip("synthetic fixture missing")
    r1 = ingest_pdf(conn, project_name="HubbyPremierInnLondon", pdf_path=FIXTURE, force=True)
    r2 = ingest_pdf(conn, project_name="HubbyPremierInnLondon", pdf_path=FIXTURE, force=False)
    assert r2["skipped_unchanged"] is True
    docs = conn.execute(
        "SELECT COUNT(*) AS n FROM documents WHERE project_id = ?",
        (r1["project_id"],),
    ).fetchone()["n"]
    assert docs == 1
    # force re-ingest still one document
    r3 = ingest_pdf(conn, project_name="HubbyPremierInnLondon", pdf_path=FIXTURE, force=True)
    docs3 = conn.execute(
        "SELECT COUNT(*) AS n FROM documents WHERE project_id = ?",
        (r3["project_id"],),
    ).fetchone()["n"]
    assert docs3 == 1
