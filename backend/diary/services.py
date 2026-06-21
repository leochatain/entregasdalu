"""Domain orchestration over the date + filesystem + the single table.

Service functions return plain snake_case dicts; the API layer (schemas.py) aliases
them to camelCase. Errors are raised as ninja ``HttpError`` for clean HTTP signals.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone
from ninja.errors import HttpError

from .constants import TIERS_BY_ID, tier_for_path
from .hashing import seed_for
from .models import DailyEntry
from .offer import compute_offer
from .photos import url_for
from .reveal import compute_reveal


# --- Payload builders -----------------------------------------------------
def _as_date(value: date | str) -> date:
    """A freshly created row keeps the str we assigned; reads give a ``date``."""
    return value if isinstance(value, date) else date.fromisoformat(value)


def _picked_payload(entry: DailyEntry) -> dict[str, Any]:
    tier = tier_for_path(entry.photo_path)
    entry_date = _as_date(entry.date)
    return {
        "photo_path": entry.photo_path,
        "photo_url": url_for(entry.photo_path),
        "tier": tier.id,
        "name": tier.name,
        "word_target": entry.word_target,
        "seed_tile": seed_for(entry_date.isoformat(), entry.photo_path),
    }


def _frozen_payload(entry: DailyEntry) -> dict[str, Any]:
    tier = tier_for_path(entry.photo_path)
    return {
        "date": _as_date(entry.date),
        "tier": tier.id,
        "name": tier.name,
        "word_target": entry.word_target,
        "effective_word_count": entry.effective_word_count,
        "performance_pct": entry.performance_pct,
        "photo_url": url_for(entry.photo_path),
        "revealed_tiles": entry.revealed_tiles,
    }


def _unlocked_set() -> set[str]:
    return set(DailyEntry.objects.filter(status="submitted").values_list("photo_path", flat=True))


# --- Endpoints (design.md §5) ---------------------------------------------
def today_state(date_str: str) -> dict[str, Any]:
    """Discriminated day state for resume routing (§5.1)."""
    entry = DailyEntry.objects.filter(date=date_str).first()
    if entry is None:
        offer = compute_offer(date_str, _unlocked_set())
        return {
            "today": date_str,
            "state": "none",
            "offer": [s.public() if s else None for s in offer],
        }
    if entry.status == "picked":
        return {"today": date_str, "state": "picked", "picked": _picked_payload(entry)}
    return {"today": date_str, "state": "submitted", "submitted": _frozen_payload(entry)}


def pick(date_str: str, tier_id: str) -> dict[str, Any]:
    """Pin the requested tier's deterministic slot. Idempotent (§5.1)."""
    if tier_id not in TIERS_BY_ID:
        raise HttpError(400, "Desafio desconhecido.")

    existing = DailyEntry.objects.filter(date=date_str).first()
    if existing is not None:
        if existing.status == "submitted":
            raise HttpError(409, "Hoje já foi entregue.")
        # Already picked: the pin is final. Same tier → idempotent; different → reject.
        if tier_for_path(existing.photo_path).id != tier_id:
            raise HttpError(409, "Você já escolheu outro desafio hoje.")
        return _picked_payload(existing)

    offer = compute_offer(date_str, _unlocked_set())
    slot = next((s for s in offer if s is not None and s.tier == tier_id), None)
    if slot is None:
        raise HttpError(409, "Sem foto para esse desafio hoje.")

    entry = DailyEntry.objects.create(
        date=date_str,
        photo_path=slot.photo_path,
        word_target=slot.word_target,
        status="picked",
        picked_at=timezone.now(),
    )
    return _picked_payload(entry)


def submit(date_str: str, text: str) -> dict[str, Any]:
    """Count words → compute reveal → freeze exactly once. Idempotent (§4.4)."""
    with transaction.atomic():
        entry = DailyEntry.objects.select_for_update().filter(date=date_str).first()
        if entry is None:
            raise HttpError(409, "Escolha um desafio antes de entregar.")
        if entry.status == "submitted":
            return _frozen_payload(entry)  # never recompute or re-freeze

        word_count = len(text.split())  # v1: word count only, always succeeds (§4.3)
        p = min(1.0, word_count / entry.word_target)
        entry.effective_word_count = word_count
        entry.performance_pct = p
        entry.revealed_tiles = compute_reveal(date_str, entry.photo_path, p)
        entry.submitted_at = timezone.now()
        entry.status = "submitted"
        entry.save()
    return _frozen_payload(entry)


def gallery() -> dict[str, Any]:
    entries = DailyEntry.objects.filter(status="submitted").order_by("-date")
    items = [_frozen_payload(e) for e in entries]
    return {"items": items, "photos_collected": len(items)}


def _streaks(dates: set[date], today: date) -> tuple[int, int]:
    """Current + longest run of consecutive São Paulo calendar days (spec §6)."""
    longest = 0
    for d in dates:
        if d - timedelta(days=1) not in dates:  # start of a run
            length, nxt = 1, d + timedelta(days=1)
            while nxt in dates:
                length += 1
                nxt += timedelta(days=1)
            longest = max(longest, length)
    # Current: count back from today; if today isn't done yet, anchor at yesterday so
    # an unfinished today doesn't read as a broken streak.
    anchor = today if today in dates else today - timedelta(days=1)
    current, d = 0, anchor
    while d in dates:
        current += 1
        d -= timedelta(days=1)
    return current, longest


def stats(date_str: str) -> dict[str, Any]:
    today = date.fromisoformat(date_str)
    entries = list(DailyEntry.objects.filter(status="submitted"))
    dates = {e.date for e in entries}
    current, longest = _streaks(dates, today)
    total_words = sum(e.effective_word_count or 0 for e in entries)
    collected = len(entries)

    month_entries = [
        e for e in entries if e.date.year == today.year and e.date.month == today.month
    ]
    return {
        "today": date_str,
        "current_streak": current,
        "longest_streak": longest,
        "total_words": total_words,
        "days_delivered": collected,
        "photos_collected": collected,
        # Current month only (v1); FE builds the grid from real offset + length (§5.1).
        "year": today.year,
        "month": today.month,
        "days_in_month": calendar.monthrange(today.year, today.month)[1],
        "first_weekday": date(today.year, today.month, 1).weekday(),  # 0=Mon .. 6=Sun
        "calendar": [{"date": e.date, "performance_pct": e.performance_pct} for e in month_entries],
    }
