from __future__ import annotations
from datetime import date, timezone, datetime


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def calculate_new_streak(last_activity: date | None, current_streak: int) -> tuple[int, bool, int]:
    """
    Returns (new_current_streak, incremented_today, gap_days)
    - If first activity (last_activity None): streak becomes 1, incremented_today True
    - If activity yesterday (diff==1): streak +1
    - If same day (diff==0): no change
    - If missed days (diff>1): reset to 1
    """
    today = utc_today()
    if last_activity is None:
        return 1, True, 999  # gap unknown for first time
    diff = (today - last_activity).days
    if diff == 0:
        return current_streak, False, 0
    if diff == 1:
        return current_streak + 1, True, 1
    # missed at least one day
    return 1, True, diff 