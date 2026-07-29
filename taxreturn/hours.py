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


def distribute_hours(total: float, n: int, rate: float = 0.8) -> list[int]:
    """Split `rate` (e.g. 80%) of `total` hours across `n` PRs as whole hours.

    Uses the largest-remainder method: the refundable total is rounded to a whole
    number of hours, then shared as evenly as possible. The leftover hours are given
    out one per PR (no rounding down), so the shares sum exactly to that total and
    differ by at most one hour.
    """
    if n == 0:
        return []
    returnable = round(total * rate)
    base, remainder = divmod(returnable, n)
    return [base + 1 if i < remainder else base for i in range(n)]
