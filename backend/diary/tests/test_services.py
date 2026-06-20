"""Service orchestration: pick/submit/today/gallery/stats (design.md §4.4, §5.1)."""

from __future__ import annotations

from datetime import date

import pytest
from django.utils import timezone
from ninja.errors import HttpError

from diary import services
from diary.models import DailyEntry
from diary.reveal import compute_reveal

pytestmark = pytest.mark.django_db

DATE = "2026-06-20"


# --- Resume routing (each status → expected state) ------------------------
def test_today_none_returns_offer(photos):
    state = services.today_state(DATE)
    assert state["state"] == "none"
    assert len(state["offer"]) == 3


def test_today_picked_routes_to_editor(photos):
    services.pick(DATE, "capitulo")
    state = services.today_state(DATE)
    assert state["state"] == "picked"
    assert state["picked"]["tier"] == "capitulo"
    assert state["picked"]["word_target"] == 400


def test_today_submitted_routes_to_jaentregue(photos):
    services.pick(DATE, "rascunho")
    services.submit(DATE, "uma frase qualquer")
    state = services.today_state(DATE)
    assert state["state"] == "submitted"
    assert state["submitted"]["revealed_tiles"]


# --- Pick guards ----------------------------------------------------------
def test_pick_creates_picked_entry(photos):
    out = services.pick(DATE, "tese")
    entry = DailyEntry.objects.get(date=DATE)
    assert entry.status == "picked"
    assert entry.word_target == 800
    assert out["seed_tile"] in (20, 21, 26, 27)


def test_pick_is_idempotent_same_tier(photos):
    first = services.pick(DATE, "capitulo")
    second = services.pick(DATE, "capitulo")
    assert first["photo_path"] == second["photo_path"]
    assert DailyEntry.objects.count() == 1


def test_pick_different_tier_after_pick_is_rejected(photos):
    services.pick(DATE, "capitulo")
    with pytest.raises(HttpError) as exc:
        services.pick(DATE, "tese")
    assert exc.value.status_code == 409


def test_pick_unknown_tier_is_400(photos):
    with pytest.raises(HttpError) as exc:
        services.pick(DATE, "doutorado")
    assert exc.value.status_code == 400


def test_pick_empty_pool_is_rejected(photos, settings):
    for f in (settings.PHOTOS_ROOT / "tese").iterdir():
        f.unlink()
    with pytest.raises(HttpError) as exc:
        services.pick(DATE, "tese")
    assert exc.value.status_code == 409


def test_pick_after_submit_is_rejected(photos):
    services.pick(DATE, "rascunho")
    services.submit(DATE, "algumas palavras aqui")
    with pytest.raises(HttpError) as exc:
        services.pick(DATE, "rascunho")
    assert exc.value.status_code == 409


# --- Submit: word-count / p / freeze --------------------------------------
def test_submit_without_pick_is_rejected(photos):
    with pytest.raises(HttpError) as exc:
        services.submit(DATE, "texto")
    assert exc.value.status_code == 409


def test_submit_counts_words_and_computes_p(photos):
    services.pick(DATE, "rascunho")  # target 150
    out = services.submit(DATE, "palavra " * 75)  # 75 words → p = 0.5
    assert out["effective_word_count"] == 75
    assert out["performance_pct"] == pytest.approx(0.5)


def test_submit_caps_p_at_one(photos):
    services.pick(DATE, "rascunho")  # target 150
    out = services.submit(DATE, "x " * 500)  # well over target
    assert out["performance_pct"] == 1.0
    assert len(out["revealed_tiles"]) == 48


def test_submit_short_entry_still_reveals(photos):
    services.pick(DATE, "tese")  # target 800
    out = services.submit(DATE, "só três palavras")  # 3 words
    assert out["effective_word_count"] == 3
    assert len(out["revealed_tiles"]) >= 1  # principle #2


def test_submit_matches_reveal_module(photos):
    entry_out = services.pick(DATE, "capitulo")
    submit_out = services.submit(DATE, "palavra " * 200)  # 200/400 → 0.5
    expected = compute_reveal(DATE, entry_out["photo_path"], 0.5)
    assert submit_out["revealed_tiles"] == expected


def test_submit_is_idempotent(photos):
    services.pick(DATE, "capitulo")
    first = services.submit(DATE, "palavra " * 100)
    second = services.submit(DATE, "texto completamente diferente e mais longo " * 20)
    # The freeze happens once: the second submit returns the first result unchanged.
    assert first["revealed_tiles"] == second["revealed_tiles"]
    assert first["effective_word_count"] == second["effective_word_count"]


# --- Gallery & stats ------------------------------------------------------
def _make_submitted(date_str: str, tier: str, words: int):
    services.pick(date_str, tier)
    services.submit(date_str, "w " * words)


def test_gallery_lists_submitted_with_pool_total(photos):
    _make_submitted(DATE, "rascunho", 150)
    gal = services.gallery()
    assert gal["photos_collected"] == 1
    assert gal["pool_total"] == 12  # 4 per tier
    assert len(gal["items"]) == 1


def test_gallery_excludes_picked_only(photos):
    services.pick(DATE, "tese")  # picked but not submitted
    assert services.gallery()["photos_collected"] == 0


def test_stats_streaks_and_totals(photos):
    # Three consecutive days, today = the last one.
    _make_submitted("2026-06-18", "rascunho", 150)
    _make_submitted("2026-06-19", "capitulo", 400)
    _make_submitted("2026-06-20", "tese", 800)
    stats = services.stats("2026-06-20")
    assert stats["current_streak"] == 3
    assert stats["longest_streak"] == 3
    assert stats["days_delivered"] == 3
    assert stats["total_words"] == 150 + 400 + 800


def test_stats_streak_breaks_on_gap(photos):
    _make_submitted("2026-06-15", "rascunho", 150)
    _make_submitted("2026-06-19", "capitulo", 400)
    _make_submitted("2026-06-20", "tese", 800)
    stats = services.stats("2026-06-20")
    assert stats["current_streak"] == 2  # 19th + 20th
    assert stats["longest_streak"] == 2


def test_stats_calendar_is_current_month_only(photos):
    _make_submitted("2026-05-30", "rascunho", 150)  # previous month
    _make_submitted("2026-06-20", "tese", 800)  # current month
    stats = services.stats("2026-06-20")
    assert stats["year"] == 2026
    assert stats["month"] == 6
    assert stats["days_in_month"] == 30
    assert stats["first_weekday"] == date(2026, 6, 1).weekday()
    cal_dates = {c["date"] for c in stats["calendar"]}
    assert date(2026, 6, 20) in cal_dates
    assert date(2026, 5, 30) not in cal_dates


def test_stats_unfinished_today_keeps_streak(photos):
    # Yesterday delivered, today not yet → current streak still counts (anchors back).
    _make_submitted("2026-06-19", "rascunho", 150)
    stats = services.stats("2026-06-20")
    assert stats["current_streak"] == 1


def test_picked_at_is_tz_aware(photos):
    services.pick(DATE, "rascunho")
    entry = DailyEntry.objects.get(date=DATE)
    assert timezone.is_aware(entry.picked_at)
