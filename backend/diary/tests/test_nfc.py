"""Raw-bytes identity vs NFC-only hashing (design.md §4.0).

A filename that differs NFC-vs-NFD must hash stably, yet be stored and served as
the raw bytes that landed on disk — otherwise the static lookup 404s and an already
-won photo could re-appear in the menu.
"""

from __future__ import annotations

import unicodedata

import pytest

from diary import services
from diary.hashing import stable_hash
from diary.models import DailyEntry
from diary.offer import compute_offer

DATE = "2026-06-20"
NAME_NFD = unicodedata.normalize("NFD", "manhã-no-arpoador.png")
NAME_NFC = unicodedata.normalize("NFC", "manhã-no-arpoador.png")


@pytest.fixture
def accented_photos(tmp_path, settings):
    """A single tese photo whose name is stored in NFD (macOS-style) form."""
    root = tmp_path / "photos"
    (root / "tese").mkdir(parents=True)
    (root / "tese" / NAME_NFD).write_bytes(b"\x89PNG\r\n")
    settings.PHOTOS_ROOT = root
    return root


def test_hash_input_is_nfc_invariant():
    assert stable_hash(f"{DATE}|tese/{NAME_NFD}") == stable_hash(f"{DATE}|tese/{NAME_NFC}")


def test_offer_serves_raw_bytes(accented_photos):
    from urllib.parse import unquote

    slot = compute_offer(DATE, set())[2]  # tese
    assert slot is not None
    # The stored/served path is the RAW (NFD) name, not a re-normalized copy.
    assert slot.photo_path == f"tese/{NAME_NFD}"
    # The URL percent-encodes but decodes back to the exact raw on-disk path.
    assert unquote(slot.photo_url) == "/photos/" + slot.photo_path


@pytest.mark.django_db
def test_won_photo_stored_raw_and_excluded_next_time(accented_photos):
    services.pick(DATE, "tese")
    entry = DailyEntry.objects.get(date=DATE)
    assert entry.photo_path == f"tese/{NAME_NFD}"  # raw bytes persisted

    services.submit(DATE, "algumas palavras")
    # Set-difference uses raw bytes, so the won photo is gone from a later offer.
    unlocked = {entry.photo_path}
    assert compute_offer("2026-06-21", unlocked)[2] is None
