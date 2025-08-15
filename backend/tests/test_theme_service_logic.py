import pathlib
import sys
from datetime import datetime, time as dt_time, timedelta
import types

import pytest

# Ensure backend package is on sys.path when running from repo root
ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from theme_service import ThemeService, ThemeType  # type: ignore  # noqa: E402


class FakeQuery:
    def __init__(self, items):
        self._items = items

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._items

    def count(self):
        return len(self._items)


class FakeSession:
    def __init__(self, schedules=None, settings=None):
        self._schedules = schedules or []
        self._settings = settings or []

    def query(self, model):
        # We don't need model types for logic-only tests
        if model.__name__.lower().startswith("themeschedule"):
            return FakeQuery(self._schedules)
        return FakeQuery(self._settings)


def make_schedule(theme_type: str, start: dt_time, end: dt_time, weekdays: list[int], is_active=True):
    return types.SimpleNamespace(
        id=1,
        name="sched",
        theme_type=theme_type,
        start_time=start,
        end_time=end,
        weekdays=weekdays,
        is_active=is_active,
        created_at=None,
        updated_at=None,
    )


def test_is_time_in_schedule_same_day():
    svc = ThemeService()
    sched = make_schedule("light", dt_time(9, 0), dt_time(17, 0), [1, 2, 3, 4, 5])
    # Monday 12:00
    assert svc._is_time_in_schedule(dt_time(12, 0), 1, sched) is True
    # Monday 08:00
    assert svc._is_time_in_schedule(dt_time(8, 0), 1, sched) is False
    # Sunday 12:00 (weekday 7)
    assert svc._is_time_in_schedule(dt_time(12, 0), 7, sched) is False


def test_is_time_in_schedule_overnight():
    svc = ThemeService()
    sched = make_schedule("dark", dt_time(18, 0), dt_time(6, 0), [1, 2, 3, 4, 5, 6, 7])
    # 23:00 matches
    assert svc._is_time_in_schedule(dt_time(23, 0), 3, sched) is True
    # 05:30 matches (overnight end)
    assert svc._is_time_in_schedule(dt_time(5, 30), 4, sched) is True
    # 12:00 does not match
    assert svc._is_time_in_schedule(dt_time(12, 0), 3, sched) is False


def test_get_current_theme_by_time_with_schedules(monkeypatch):
    svc = ThemeService()

    # Build schedules: Light 06-18, Dark 18-06
    schedules = [
        make_schedule("light", dt_time(6, 0), dt_time(18, 0), [1, 2, 3, 4, 5, 6, 7]),
        make_schedule("dark", dt_time(18, 0), dt_time(6, 0), [1, 2, 3, 4, 5, 6, 7]),
    ]

    fake_db = FakeSession(schedules=schedules)

    # 10:00 -> light
    class FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 1, 1, 10, 0, 0)

    monkeypatch.setattr("theme_service.datetime", FakeDT)
    assert svc.get_current_theme_by_time(fake_db) == ThemeType.LIGHT

    # 20:00 -> dark
    class FakeDT2(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 1, 1, 20, 0, 0)

    monkeypatch.setattr("theme_service.datetime", FakeDT2)
    assert svc.get_current_theme_by_time(fake_db) == ThemeType.DARK


def test_manual_override_takes_precedence(monkeypatch):
    svc = ThemeService()
    svc.set_manual_theme_override(ThemeType.DARK)

    schedules = [make_schedule("light", dt_time(6, 0), dt_time(18, 0), [1, 2, 3, 4, 5, 6, 7])]
    fake_db = FakeSession(schedules=schedules)

    class FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 1, 1, 10, 0, 0)

    monkeypatch.setattr("theme_service.datetime", FakeDT)
    assert svc.get_current_theme_by_time(fake_db) == ThemeType.DARK

    svc.clear_manual_override()
    assert svc.get_current_theme_by_time(fake_db) == ThemeType.LIGHT


def test_get_next_switch_time(monkeypatch):
    svc = ThemeService()
    schedules = [
        make_schedule("light", dt_time(6, 0), dt_time(18, 0), [3]),  # Wednesday only
    ]
    fake_db = FakeSession(schedules=schedules)

    # Wednesday 05:00 -> next switch at 06:00
    class FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            # 2025-01-01 is Wednesday
            return datetime(2025, 1, 1, 5, 0, 0)

    monkeypatch.setattr("theme_service.datetime", FakeDT)
    nxt = svc.get_next_switch_time(fake_db)
    assert nxt is not None
    assert nxt.hour == 6 and nxt.minute == 0

    # Later same day 17:30 -> next switch 18:00
    class FakeDT2(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 1, 1, 17, 30, 0)

    monkeypatch.setattr("theme_service.datetime", FakeDT2)
    nxt2 = svc.get_next_switch_time(fake_db)
    assert nxt2 is not None
    assert nxt2.hour == 18 and nxt2.minute == 0


def test_get_theme_status(monkeypatch):
    svc = ThemeService()
    schedules = [
        make_schedule("light", dt_time(6, 0), dt_time(18, 0), [1, 2, 3, 4, 5, 6, 7])
    ]
    fake_db = FakeSession(schedules=schedules)

    class FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2025, 1, 1, 7, 0, 0)

    monkeypatch.setattr("theme_service.datetime", FakeDT)
    status = svc.get_theme_status(fake_db)
    assert status.current_theme == ThemeType.LIGHT
    assert status.auto_theme_enabled is True
    assert status.manual_override is False
