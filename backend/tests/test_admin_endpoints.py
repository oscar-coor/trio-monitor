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

# Import the FastAPI app and the admin_api module so we can monkeypatch its services
import admin_api as admin_api_module  # type: ignore  # noqa: E402
from app import app  # type: ignore  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_services(monkeypatch):
    """Ensure services are restored per test."""
    original_admin = admin_api_module.admin_service
    original_theme = admin_api_module.theme_service
    yield
    monkeypatch.setattr(admin_api_module, "admin_service", original_admin, raising=False)
    monkeypatch.setattr(admin_api_module, "theme_service", original_theme, raising=False)


def make_fake_admin_service():
    svc = types.SimpleNamespace()

    async def _get_services():
        return [
            {"id": "svc_001", "name": "Kundservice", "description": ""},
            {"id": "svc_002", "name": "Support", "description": ""},
        ]

    async def _get_users():
        return [
            {"id": "usr_001", "name": "anna", "display_name": "Anna"},
        ]

    def _get_monitored_services(db=None):
        return [
            {
                "id": 1,
                "trio_service_id": "svc_001",
                "service_name": "Kundservice",
                "sla_target_seconds": 20,
                "warning_threshold_seconds": 18,
                "is_active": True,
                "created_at": None,
                "updated_at": None,
            }
        ]

    def _add_monitored_service(db, service):
        # Echo back with id set
        return types.SimpleNamespace(
            id=2,
            trio_service_id=service.trio_service_id,
            service_name=service.service_name,
            sla_target_seconds=service.sla_target_seconds,
            warning_threshold_seconds=service.warning_threshold_seconds,
            is_active=service.is_active,
            created_at=None,
            updated_at=None,
        )

    def _update_monitored_service(db, service_id, service):
        if service_id != 999:
            return types.SimpleNamespace(
                id=service_id,
                trio_service_id=service.trio_service_id,
                service_name=service.service_name,
                sla_target_seconds=service.sla_target_seconds,
                warning_threshold_seconds=service.warning_threshold_seconds,
                is_active=service.is_active,
                created_at=None,
                updated_at=None,
            )
        return None

    def _remove_monitored_service(db, service_id):
        return service_id != 999

    def _get_monitored_users(db=None):
        return [
            {
                "id": 1,
                "trio_user_id": "usr_001",
                "user_name": "anna",
                "display_name": "Anna",
                "is_active": True,
                "created_at": None,
                "updated_at": None,
            }
        ]

    def _add_monitored_user(db, user):
        return types.SimpleNamespace(
            id=2,
            trio_user_id=user.trio_user_id,
            user_name=user.user_name,
            display_name=user.display_name,
            is_active=user.is_active,
            created_at=None,
            updated_at=None,
        )

    def _update_monitored_user(db, user_id, user):
        if user_id != 999:
            return types.SimpleNamespace(
                id=user_id,
                trio_user_id=user.trio_user_id,
                user_name=user.user_name,
                display_name=user.display_name,
                is_active=user.is_active,
                created_at=None,
                updated_at=None,
            )
        return None

    def _remove_monitored_user(db, user_id):
        return user_id != 999

    def _get_time_windows(db=None):
        return [
            {
                "id": 1,
                "name": "Vardag",
                "start_time": "07:00:00",
                "end_time": "21:00:00",
                "weekdays": [1, 2, 3, 4, 5],
                "is_active": True,
                "created_at": None,
                "updated_at": None,
            }
        ]

    def _update_time_windows(db, windows):
        # Echo back
        return windows

    def _get_sla_metrics(db, service_id=None, date_from=None, date_to=None):
        return [
            {
                "id": 1,
                "service_id": 1,
                "measurement_date": "2025-01-01",
                "time_window_id": 1,
                "average_wait_time": 12.5,
                "total_calls": 100,
                "calls_within_sla": 82,
                "sla_percentage": 82.0,
                "peak_wait_time": 30,
                "created_at": None,
            }
        ]

    def _get_admin_config(db=None):
        return types.SimpleNamespace(
            monitored_services=_get_monitored_services(),
            monitored_users=_get_monitored_users(),
            time_windows=_get_time_windows(),
            theme_schedule=[],
        )

    svc.get_available_trio_services = _get_services
    svc.get_available_trio_users = _get_users
    svc.get_monitored_services = _get_monitored_services
    svc.add_monitored_service = _add_monitored_service
    svc.update_monitored_service = _update_monitored_service
    svc.remove_monitored_service = _remove_monitored_service
    svc.get_monitored_users = _get_monitored_users
    svc.add_monitored_user = _add_monitored_user
    svc.update_monitored_user = _update_monitored_user
    svc.remove_monitored_user = _remove_monitored_user
    svc.get_time_windows = _get_time_windows
    svc.update_time_windows = _update_time_windows
    svc.get_sla_metrics = _get_sla_metrics
    svc.get_admin_config = _get_admin_config
    return svc


def make_fake_theme_service():
    svc = types.SimpleNamespace()

    def _get_theme_schedules(db=None):
        return [
            {
                "id": 1,
                "name": "Dagstema",
                "theme_type": "light",
                "start_time": "06:00:00",
                "end_time": "18:00:00",
                "weekdays": [1, 2, 3, 4, 5, 6, 7],
                "is_active": True,
                "created_at": None,
                "updated_at": None,
            }
        ]

    def _update_theme_schedules(db, schedules):
        return schedules

    def _get_theme_settings(db, theme_type=None):
        return [
            {
                "id": 1,
                "theme_type": "light",
                "primary_color": "#1976d2",
                "background_color": "#ffffff",
                "surface_color": "#f5f5f5",
                "text_primary": "#000000",
                "text_secondary": "#666666",
                "border_color": "#e0e0e0",
                "success_color": "#4caf50",
                "warning_color": "#ff9800",
                "error_color": "#f44336",
                "is_default": True,
                "created_at": None,
                "updated_at": None,
            }
        ]

    def _update_theme_settings(db, settings):
        return settings

    def _get_current_theme_by_time(db=None):
        return "light"

    def _get_theme_status(db=None):
        return {
            "current_theme": "light",
            "auto_theme_enabled": True,
            "next_switch_time": None,
            "manual_override": False,
        }

    def _set_manual_theme_override(theme):
        return None

    def _clear_manual_override():
        return None

    svc.get_theme_schedules = _get_theme_schedules
    svc.update_theme_schedules = _update_theme_schedules
    svc.get_theme_settings = _get_theme_settings
    svc.update_theme_settings = _update_theme_settings
    svc.get_current_theme_by_time = _get_current_theme_by_time
    svc.get_theme_status = _get_theme_status
    svc.set_manual_theme_override = _set_manual_theme_override
    svc.clear_manual_override = _clear_manual_override
    return svc


def test_get_available_services(monkeypatch):
    monkeypatch.setattr(admin_api_module, "admin_service", make_fake_admin_service(), raising=False)
    r = client.get("/api/admin/services")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) >= 2
    assert {"id", "name"}.issubset(data[0].keys())


def test_get_available_users(monkeypatch):
    monkeypatch.setattr(admin_api_module, "admin_service", make_fake_admin_service(), raising=False)
    r = client.get("/api/admin/users")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) >= 1
    assert {"id", "name"}.issubset(data[0].keys())


def test_monitored_services_crud(monkeypatch):
    monkeypatch.setattr(admin_api_module, "admin_service", make_fake_admin_service(), raising=False)

    # List
    r = client.get("/api/admin/monitored-services")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Create
    payload = {
        "trio_service_id": "svc_002",
        "service_name": "Support",
        "sla_target_seconds": 20,
        "warning_threshold_seconds": 18,
        "is_active": True,
    }
    r = client.post("/api/admin/monitored-services", json=payload)
    assert r.status_code == 200
    assert r.json()["id"] == 2

    # Update ok
    update_payload = dict(payload)
    update_payload["service_name"] = "Support uppd"
    r = client.put("/api/admin/monitored-services/2", json=update_payload)
    assert r.status_code == 200
    assert r.json()["service_name"].startswith("Support")

    # Update missing id -> 404
    r = client.put("/api/admin/monitored-services/999", json=update_payload)
    assert r.status_code == 404

    # Delete ok
    r = client.delete("/api/admin/monitored-services/2")
    assert r.status_code == 200
    # Delete missing -> 404
    r = client.delete("/api/admin/monitored-services/999")
    assert r.status_code == 404


def test_monitored_users_crud(monkeypatch):
    monkeypatch.setattr(admin_api_module, "admin_service", make_fake_admin_service(), raising=False)

    # List
    r = client.get("/api/admin/monitored-users")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Create
    payload = {
        "trio_user_id": "usr_002",
        "user_name": "erik",
        "display_name": "Erik",
        "is_active": True,
    }
    r = client.post("/api/admin/monitored-users", json=payload)
    assert r.status_code == 200
    assert r.json()["id"] == 2

    # Update ok
    update_payload = dict(payload)
    update_payload["display_name"] = "Erik E"
    r = client.put("/api/admin/monitored-users/2", json=update_payload)
    assert r.status_code == 200

    # Update missing -> 404
    r = client.put("/api/admin/monitored-users/999", json=update_payload)
    assert r.status_code == 404

    # Delete ok
    r = client.delete("/api/admin/monitored-users/2")
    assert r.status_code == 200
    # Delete missing -> 404
    r = client.delete("/api/admin/monitored-users/999")
    assert r.status_code == 404


def test_time_windows(monkeypatch):
    monkeypatch.setattr(admin_api_module, "admin_service", make_fake_admin_service(), raising=False)

    r = client.get("/api/admin/time-windows")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    payload = [
        {
            "name": "Helg",
            "start_time": "09:00:00",
            "end_time": "16:00:00",
            "weekdays": [6, 7],
            "is_active": True,
        }
    ]
    r = client.put("/api/admin/time-windows", json=payload)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_sla_metrics(monkeypatch):
    monkeypatch.setattr(admin_api_module, "admin_service", make_fake_admin_service(), raising=False)

    r = client.get("/api/admin/sla-metrics")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert {"average_wait_time", "sla_percentage"}.issubset(data[0].keys())


def test_admin_config(monkeypatch):
    monkeypatch.setattr(admin_api_module, "admin_service", make_fake_admin_service(), raising=False)
    monkeypatch.setattr(admin_api_module, "theme_service", make_fake_theme_service(), raising=False)

    r = client.get("/api/admin/config")
    assert r.status_code == 200
    data = r.json()
    assert {"monitored_services", "monitored_users", "time_windows", "theme_schedule"}.issubset(
        data.keys()
    )


def test_theme_endpoints(monkeypatch):
    monkeypatch.setattr(admin_api_module, "theme_service", make_fake_theme_service(), raising=False)

    r = client.get("/api/theme/current")
    assert r.status_code == 200
    assert r.json() in ("light", "dark")

    r = client.get("/api/theme/status")
    assert r.status_code == 200
    data = r.json()
    assert {"current_theme", "auto_theme_enabled", "manual_override"}.issubset(data.keys())

    r = client.post("/api/theme/manual-override", params={"theme": "dark"})
    assert r.status_code == 200

    r = client.delete("/api/theme/manual-override")
    assert r.status_code == 200
