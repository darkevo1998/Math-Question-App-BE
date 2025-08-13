from datetime import date, timedelta
from src.services.streak import calculate_new_streak


def test_streak_first_activity():
    new, inc, gap = calculate_new_streak(None, 0)
    assert new == 1 and inc is True


def test_streak_same_day_no_increment(monkeypatch):
    today = date(2024, 8, 1)
    monkeypatch.setattr("src.services.streak.utc_today", lambda: today)
    new, inc, _ = calculate_new_streak(today, 3)
    assert new == 3 and inc is False


def test_streak_yesterday_increment(monkeypatch):
    today = date(2024, 8, 2)
    monkeypatch.setattr("src.services.streak.utc_today", lambda: today)
    new, inc, _ = calculate_new_streak(date(2024, 8, 1), 3)
    assert new == 4 and inc is True


def test_streak_missed_day_resets(monkeypatch):
    today = date(2024, 8, 4)
    monkeypatch.setattr("src.services.streak.utc_today", lambda: today)
    new, inc, _ = calculate_new_streak(date(2024, 8, 1), 5)
    assert new == 1 and inc is True 