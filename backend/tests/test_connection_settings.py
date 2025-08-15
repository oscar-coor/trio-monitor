import pathlib
import sys
import types

import pytest
from fastapi.testclient import TestClient

# Ensure backend package is on sys.path when running from repo root
ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Import the FastAPI app and the admin_api module so we can monkeypatch its service
import admin_api as admin_api_module  # type: ignore  # noqa: E402
from app import app  # type: ignore  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_admin_service(monkeypatch):
    """Ensure admin_service is restored per test."""
    original = admin_api_module.admin_service
    yield
    monkeypatch.setattr(admin_api_module, "admin_service", original, raising=False)


def make_fake_service(get_payload=None, put_payload=None, test_ok=True):
    svc = types.SimpleNamespace()

    async def _test_conn():
        return bool(test_ok)

    def _get_conn(db=None):
        return get_payload or {
            "base_url": "https://trio.example.com/te/api",
            "username": "user",
            "password": None,
            "api_token": None,
            "contact_center_id": "1",
            "has_token": True,
        }

    def _put_conn(db=None, new=None):
        return put_payload or {
            "base_url": new.base_url if hasattr(new, "base_url") else "https://trio.example.com/te/api",
            "username": getattr(new, "username", None),
            "password": None,
            "api_token": None,
            "contact_center_id": getattr(new, "contact_center_id", "1"),
            "has_token": True,
        }

    svc.test_trio_connection = _test_conn
    svc.get_connection_settings = _get_conn
    svc.update_connection_settings = _put_conn
    return svc


def test_get_connection_settings(monkeypatch):
    fake = make_fake_service(get_payload={
        "base_url": "https://trio.example.com/te/api",
        "username": "",
        "password": None,
        "api_token": None,
        "contact_center_id": "1",
        "has_token": False,
    })
    monkeypatch.setattr(admin_api_module, "admin_service", fake, raising=False)

    r = client.get("/api/admin/connection-settings")
    assert r.status_code == 200
    data = r.json()
    assert set([
        "base_url",
        "username",
        "password",
        "api_token",
        "contact_center_id",
        "has_token",
    ]).issubset(data.keys())
    assert data["api_token"] is None  # never expose token value


def test_update_connection_settings_validation_error(monkeypatch):
    # Force service to be called only if validation passes; we'll rely on API validation to fail
    fake = make_fake_service()
    monkeypatch.setattr(admin_api_module, "admin_service", fake, raising=False)

    payload = {
        # missing base_url
        "username": "u",
        "password": "p",
        "contact_center_id": "1",
    }
    r = client.put("/api/admin/connection-settings", json=payload)
    # Pydantic validation error (missing required field) => 422
    assert r.status_code == 422
    # Ensure error mentions base_url in validation details
    detail = r.json().get("detail", [])
    assert any("base_url" in str(item) for item in detail)


def test_update_connection_settings_success(monkeypatch):
    fake = make_fake_service()
    monkeypatch.setattr(admin_api_module, "admin_service", fake, raising=False)

    payload = {
        "base_url": "https://trio.example.com/te/api",
        "username": "u",
        "password": "p",
        "contact_center_id": "1",
    }
    r = client.put("/api/admin/connection-settings", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["base_url"].startswith("https://")
    assert data["has_token"] in (True, False)


def test_test_connection_ok(monkeypatch):
    fake = make_fake_service(test_ok=True)
    monkeypatch.setattr(admin_api_module, "admin_service", fake, raising=False)

    r = client.post("/api/admin/test-connection")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_test_connection_fail(monkeypatch):
    fake = make_fake_service(test_ok=False)
    monkeypatch.setattr(admin_api_module, "admin_service", fake, raising=False)

    r = client.post("/api/admin/test-connection")
    assert r.status_code == 200
    assert r.json() == {"ok": False}
