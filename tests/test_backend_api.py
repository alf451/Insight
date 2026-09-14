"""API-level tests that don't need to wait for a poll cycle (device CRUD,
connection test). The full stack — poller, SQLite archiving of readings and
logbook entries, and both write endpoints with readback — was verified
against a real `uvicorn` process over real HTTP; see docs/SSTPROT.md
"Backend end-to-end verification" for the exact reproducible steps and
the annotated output.
"""
import os
import threading

import pytest


@pytest.fixture(scope="module")
def api_client(tmp_path_factory, monkeypatch_module):
    # app.db reads DATABASE_URL once at import time — set it before the
    # first import of app.main anywhere in the test session. Every test in
    # this module shares this one SQLite file; tests below are written to
    # not depend on it being empty (they check for their own device by id,
    # not on absolute list length).
    db_path = tmp_path_factory.mktemp("insight") / "test_insight.db"
    monkeypatch_module.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def monkeypatch_module():
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture()
def mock_device_port():
    from insight_simulator.sstprot_server import SstProtTestServer

    server = SstProtTestServer("127.0.0.1", 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_address[1]
    server.shutdown()


def test_device_crud(api_client):
    r = api_client.post(
        "/api/devices",
        json={"name": "MD01", "host": "10.0.0.5", "port": 10001, "address": "FF", "poll_interval_s": 5.0, "enabled": False},
    )
    assert r.status_code == 200
    device = r.json()
    assert device["name"] == "MD01"
    device_id = device["id"]

    r = api_client.get("/api/devices")
    assert any(d["id"] == device_id for d in r.json())

    r = api_client.put(f"/api/devices/{device_id}", json={"name": "MD01-renamed"})
    assert r.json()["name"] == "MD01-renamed"

    r = api_client.delete(f"/api/devices/{device_id}")
    assert r.json() == {"ok": True}

    r = api_client.get("/api/devices")
    assert not any(d["id"] == device_id for d in r.json())


def test_connection_success_against_mock_device(api_client, mock_device_port):
    r = api_client.post(
        "/api/devices",
        json={"name": "MD-Test", "host": "127.0.0.1", "port": mock_device_port, "address": "01", "enabled": False},
    )
    device_id = r.json()["id"]

    r = api_client.post(f"/api/devices/{device_id}/test")
    body = r.json()
    assert body["ok"] is True
    assert body["device_info"]["device_type_name"] == "GeniusOne"


def test_connection_failure_reports_error_not_crash(api_client):
    r = api_client.post(
        "/api/devices",
        json={"name": "MD-Unreachable", "host": "127.0.0.1", "port": 1, "enabled": False},
    )
    device_id = r.json()["id"]

    r = api_client.post(f"/api/devices/{device_id}/test")
    assert r.status_code == 200  # a device error must not surface as a 500
    assert r.json()["ok"] is False


def test_write_sensitivity_requires_confirm(api_client, mock_device_port):
    r = api_client.post(
        "/api/devices",
        json={"name": "MD-Test", "host": "127.0.0.1", "port": mock_device_port, "address": "01", "enabled": False},
    )
    device_id = r.json()["id"]

    r = api_client.post(
        f"/api/devices/{device_id}/write/sensitivity",
        json={"product_number": 16, "sensitivity": 90, "confirm": False},
    )
    assert r.status_code == 400
