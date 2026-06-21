"""Ninja schemas — the snake_case → camelCase translation point (design.md §3.1, §5.1).

DB/Python are snake_case; responses alias to camelCase for the FE-generated types.
Inputs accept either casing (``populate_by_name``).
"""

from __future__ import annotations

from datetime import date

from ninja import Schema
from pydantic.alias_generators import to_camel


class CamelSchema(Schema):
    model_config = {"alias_generator": to_camel, "populate_by_name": True}


# --- Inputs ---------------------------------------------------------------
class PickIn(Schema):
    tier: str


class SubmitIn(Schema):
    text: str


# --- Outputs --------------------------------------------------------------
class ConfigOut(CamelSchema):
    dev_login: bool


class OfferSlotOut(CamelSchema):
    tier: str
    name: str
    word_target: int
    photo_url: str
    seed_tile: int


class PickedOut(CamelSchema):
    photo_path: str
    photo_url: str
    tier: str
    name: str
    word_target: int
    seed_tile: int


class FrozenEntryOut(CamelSchema):
    date: date
    tier: str
    name: str
    word_target: int
    effective_word_count: int
    performance_pct: float
    photo_url: str
    revealed_tiles: list[int]


class TodayOut(CamelSchema):
    today: date  # server's effective São Paulo date (honors the dev clock)
    state: str  # 'none' | 'picked' | 'submitted'
    offer: list[OfferSlotOut | None] | None = None
    picked: PickedOut | None = None
    submitted: FrozenEntryOut | None = None


class GalleryOut(CamelSchema):
    items: list[FrozenEntryOut]
    photos_collected: int


class CalendarDayOut(CamelSchema):
    date: date
    performance_pct: float


class StatsOut(CamelSchema):
    today: date  # server's effective São Paulo date (honors the dev clock)
    current_streak: int
    longest_streak: int
    total_words: int
    days_delivered: int
    photos_collected: int
    year: int
    month: int
    days_in_month: int
    first_weekday: int
    calendar: list[CalendarDayOut]
