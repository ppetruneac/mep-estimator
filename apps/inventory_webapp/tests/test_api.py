"""API tests against live getriser.sqlite (Hubby must be ingested)."""

from __future__ import annotations

import os
import re

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATA_DIR", "/Users/pico/workspace/data/getriser")

from app.db import db_path, migrate  # noqa: E402
from app.main import app  # noqa: E402

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)


@pytest.fixture(scope="module")
def client():
    if not db_path().exists():
        pytest.skip("getriser.sqlite missing — run make seed-hubby")
    migrate()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["project_count"] >= 1


def test_projects_use_uuid_and_title_block(client):
    projects = client.get("/api/projects").json()
    hubby = next(p for p in projects if p["name"] == "HubbyPremierInnLondon")
    assert UUID_RE.match(hubby["uuid"])
    tb = hubby["title_block"]
    assert tb["display_name"] == "Hub by Premier Inn Putney"
    assert tb["location"] == "Putney"
    assert "25280-SEN" in tb["job_series"]
    assert tb["scale"] and "1:50" in tb["scale"]

    # Detail route is UUID, not integer id
    r = client.get(f"/api/projects/{hubby['uuid']}")
    assert r.status_code == 200
    assert r.json()["uuid"] == hubby["uuid"]
    assert client.get("/api/projects/1").status_code == 404


def test_list_drawings_and_items_via_uuid(client):
    projects = client.get("/api/projects").json()
    puuid = next(p["uuid"] for p in projects if p["name"] == "HubbyPremierInnLondon")
    drawings = client.get(f"/api/projects/{puuid}/drawings").json()
    assert len(drawings) >= 10
    basement = next(d for d in drawings if d["floor_tab_name"] == "Basement")
    items = client.get(f"/api/drawings/{basement['id']}/items").json()
    assert len(items) > 0


def test_approve_and_summary(client):
    projects = client.get("/api/projects").json()
    puuid = next(p["uuid"] for p in projects if p["name"] == "HubbyPremierInnLondon")
    drawings = client.get(f"/api/projects/{puuid}/drawings").json()
    basement = next(d for d in drawings if d["floor_tab_name"] == "Basement")
    items = client.get(f"/api/drawings/{basement['id']}/items?status=pending").json()
    assert items
    item = items[0]
    r = client.patch(f"/api/items/{item['id']}", json={"status": "approved"})
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    assert r.json()["reviewed_at"]

    summary = client.get(f"/api/projects/{puuid}/summary/by-floor").json()
    row = next(s for s in summary if s["label"] == "Basement")
    assert row["item_count"] >= 1


def test_bulk_approve(client):
    projects = client.get("/api/projects").json()
    puuid = next(p["uuid"] for p in projects if p["name"] == "HubbyPremierInnLondon")
    drawings = client.get(f"/api/projects/{puuid}/drawings").json()
    ground = next(d for d in drawings if d["floor_tab_name"] == "Ground Floor")
    r = client.post(
        f"/api/drawings/{ground['id']}/items/bulk",
        json={"action": "approve", "only_pending": True},
    )
    assert r.status_code == 200
    assert r.json()["updated"] >= 0
