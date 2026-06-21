"""São Paulo calendar time (design.md §8). One source for 'what day is it'."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

SAO_PAULO = ZoneInfo("America/Sao_Paulo")

# In-memory dev-only day shift (DEBUG dev tools; resets on server restart).
_DEV_OFFSET_DAYS = 0


def today_sp() -> date:
    return (datetime.now(SAO_PAULO) + timedelta(days=_DEV_OFFSET_DAYS)).date()


def today_str() -> str:
    return today_sp().isoformat()


def advance_dev_days(n: int = 1) -> None:
    """Shift the dev clock forward by ``n`` days (DEBUG-gated by the caller)."""
    global _DEV_OFFSET_DAYS
    _DEV_OFFSET_DAYS += n


def reset_dev_clock() -> None:
    """Return the dev clock to the real current date."""
    global _DEV_OFFSET_DAYS
    _DEV_OFFSET_DAYS = 0
