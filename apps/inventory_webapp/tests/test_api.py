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


def test_projects_use_uuid_and_title_block(client):
    projects = client.get("/api/projects").json()
    hubby = next(p for p in projects if p["name"] == "HubbyPremierInnLondon")
    assert UUID_RE.match(hubby["uuid"])
    assert hubby["architect"] == "Curio Architects"
    assert hubby["client"] and "Mosser" in hubby["client"]
    assert hubby["owner"] and "Seneca" in hubby["owner"]
    assert client.get("/api/projects/1").status_code == 404


def test_drawing_keyed_by_number_not_int(client):
    projects = client.get("/api/projects").json()
    puuid = next(p["uuid"] for p in projects if p["name"] == "HubbyPremierInnLondon")
    drawings = client.get(f"/api/projects/{puuid}/drawings").json()
    basement = next(d for d in drawings if d["floor_tab_name"] == "Basement")
    assert basement["key"] == basement["drawing_number"]
    assert "560X" in basement["key"] or "0X" in basement["key"]

    r = client.get(f"/api/projects/{puuid}/drawings/{basement['key']}")
    assert r.status_code == 200
    assert r.json()["floor_tab_name"] == "Basement"

    items = client.get(
        f"/api/projects/{puuid}/drawings/{basement['key']}/items"
    ).json()
    assert len(items) > 0
    sample = next(i for i in items if i.get("item_id") == "MEC-CU-IN")
    assert sample["category"] == "FLOW AND RETURN PIPEWORK"
    assert sample["catalog_category"] == "Refrigerant / F+R pipe"
    assert sample["item_label"] and "refrigerant" in sample["item_label"].lower()


def test_facets_and_filters(client):
    projects = client.get("/api/projects").json()
    puuid = next(p["uuid"] for p in projects if p["name"] == "HubbyPremierInnLondon")
    drawings = client.get(f"/api/projects/{puuid}/drawings").json()
    basement = next(d for d in drawings if d["floor_tab_name"] == "Basement")
    key = basement["key"]

    facets = client.get(f"/api/projects/{puuid}/drawings/{key}/facets").json()
    assert any(c["category"] == "INDOOR UNITS AND CONTROLLERS" for c in facets["categories"])
    assert sum(c["count"] for c in facets["categories"]) == basement["item_count"]

    indoor = "INDOOR UNITS AND CONTROLLERS"
    filtered = client.get(
        f"/api/projects/{puuid}/drawings/{key}/items",
        params={"category": indoor},
    ).json()
    assert filtered
    assert all(i["category"] == indoor for i in filtered)

    searched = client.get(
        f"/api/projects/{puuid}/drawings/{key}/items",
        params={"q": "FCU.B.01"},
    ).json()
    assert any("FCU.B.01" in (i.get("annotation") or "") for i in searched)


def test_approve_and_summary(client):
    projects = client.get("/api/projects").json()
    puuid = next(p["uuid"] for p in projects if p["name"] == "HubbyPremierInnLondon")
    drawings = client.get(f"/api/projects/{puuid}/drawings").json()
    basement = next(d for d in drawings if d["floor_tab_name"] == "Basement")
    items = client.get(
        f"/api/projects/{puuid}/drawings/{basement['key']}/items",
        params={"status": "pending"},
    ).json()
    if not items:
        pytest.skip("no pending items")
    item = items[0]
    r = client.patch(f"/api/items/{item['id']}", json={"status": "approved"})
    assert r.status_code == 200
    summary = client.get(f"/api/projects/{puuid}/summary/by-floor").json()
    assert any(s["label"] == "Basement" for s in summary)
