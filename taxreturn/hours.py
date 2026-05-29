"""Polish working-hours calculation and the 80% distribution across PRs."""
from __future__ import annotations

import calendar
import datetime as dt

from workalendar.europe import Poland

_cal = Poland()


def working_days_count(year: int, month: int) -> int:
    """Number of working days in the month per the Polish public-holiday calendar."""
    last_day = calendar.monthrange(year, month)[1]
    return sum(
        1
        for day in range(1, last_day + 1)
        if _cal.is_working_day(dt.date(year, month, day))
    )


def total_working_hours(year: int, month: int, hours_per_day: float = 8.0) -> float:
    return working_days_count(year, month) * hours_per_day


def distribute_hours(total: float, n: int, rate: float = 0.8) -> list[float]:
    """Split `rate` (e.g. 80%) of `total` hours evenly across `n` PRs.

    Each share is rounded to 2 decimals; the last one absorbs the rounding
    drift so the list sums exactly to `total * rate`.
    """
    if n == 0:
        return []
    returnable = total * rate
    per = round(returnable / n, 2)
    shares = [per] * n
    shares[-1] = round(returnable - per * (n - 1), 2)
    return shares
