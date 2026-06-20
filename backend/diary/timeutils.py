"""São Paulo calendar time (design.md §8). One source for 'what day is it'."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

SAO_PAULO = ZoneInfo("America/Sao_Paulo")


def today_sp() -> date:
    return datetime.now(SAO_PAULO).date()


def today_str() -> str:
    return today_sp().isoformat()
