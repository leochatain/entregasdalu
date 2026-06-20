"""Determinism substrate (design.md §4.0) — the highest-value contract."""

from __future__ import annotations

import unicodedata

from diary.constants import SEED_CANDIDATES
from diary.hashing import seed_for, stable_hash


def test_stable_hash_is_deterministic():
    assert stable_hash("2026-06-20|capitulo") == stable_hash("2026-06-20|capitulo")


def test_stable_hash_is_unsigned_64bit():
    h = stable_hash("anything")
    assert 0 <= h < 2**64


def test_stable_hash_known_value():
    # Pin the exact substrate so a refactor that changes the math is caught.
    # sha256(b"2026-06-20|capitulo")[:8] big-endian.
    import hashlib

    expected = int.from_bytes(hashlib.sha256(b"2026-06-20|capitulo").digest()[:8], "big")
    assert stable_hash("2026-06-20|capitulo") == expected


def test_nfc_and_nfd_hash_identically():
    # "manhã": composed (NFC) vs decomposed (NFD) must hash the same, because
    # normalization is applied to the hash input.
    nfc = unicodedata.normalize("NFC", "manhã")
    nfd = unicodedata.normalize("NFD", "manhã")
    assert nfc != nfd  # different byte sequences on disk...
    assert stable_hash(nfc) == stable_hash(nfd)  # ...identical hash


def test_seed_for_is_in_candidates_and_stable():
    seed = seed_for("2026-06-20", "capitulo/lua.png")
    assert seed in SEED_CANDIDATES
    assert seed == seed_for("2026-06-20", "capitulo/lua.png")


def test_seed_for_nfc_invariant():
    nfd = unicodedata.normalize("NFD", "capitulo/manhã.png")
    nfc = unicodedata.normalize("NFC", "capitulo/manhã.png")
    assert seed_for("2026-06-20", nfd) == seed_for("2026-06-20", nfc)
