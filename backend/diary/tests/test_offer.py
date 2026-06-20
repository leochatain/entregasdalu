"""Offer determinism (design.md §4.1; spec §1.4)."""

from __future__ import annotations

from diary.constants import TIERS
from diary.hashing import seed_for
from diary.offer import compute_offer

DATE = "2026-06-20"


def test_same_date_same_offer(photos):
    a = compute_offer(DATE, set())
    b = compute_offer(DATE, set())
    assert [s.photo_path for s in a if s] == [s.photo_path for s in b if s]


def test_offer_has_one_slot_per_tier(photos):
    offer = compute_offer(DATE, set())
    assert len(offer) == len(TIERS)
    assert [s.tier for s in offer if s] == [t.id for t in TIERS]


def test_slot_seed_matches_shared_seed_fn(photos):
    # The teaser tile must equal the reveal's seed for the same (date, photo).
    for slot in compute_offer(DATE, set()):
        assert slot is not None
        assert slot.seed_tile == seed_for(DATE, slot.photo_path)


def test_slot_photo_is_from_its_own_tier(photos):
    for slot in compute_offer(DATE, set()):
        assert slot is not None
        assert slot.photo_path.split("/", 1)[0] == slot.tier


def test_unlocked_photo_is_excluded(photos):
    chosen = compute_offer(DATE, set())[1]
    assert chosen is not None
    reoffer = compute_offer(DATE, {chosen.photo_path})
    new_slot = reoffer[1]
    assert new_slot is not None
    assert new_slot.photo_path != chosen.photo_path


def test_empty_pool_yields_none(photos, settings):
    # Drain the rascunho folder entirely.
    for f in (settings.PHOTOS_ROOT / "rascunho").iterdir():
        f.unlink()
    offer = compute_offer(DATE, set())
    assert offer[0] is None  # rascunho slot
    assert offer[1] is not None  # others unaffected


def test_photo_url_is_percent_encoded_with_separators(photos):
    slot = compute_offer(DATE, set())[0]
    assert slot is not None
    assert slot.photo_url.startswith("/photos/")
    assert "/" in slot.photo_url.removeprefix("/photos/")


def test_different_dates_can_differ(photos):
    # Not guaranteed different, but across many dates the choice must vary.
    seen = {
        tuple(s.photo_path for s in compute_offer(f"2026-06-{d:02d}", set()) if s)
        for d in range(1, 29)
    }
    assert len(seen) > 1
