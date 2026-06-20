"""Determinism substrate (design.md §4.0).

Never use Python's builtin ``hash()`` — it is per-process salted, which would make
offers/seeds non-reproducible across restarts (breaks spec §1.4). NFC normalization
is applied **only** to the hash input; stored/served paths use raw filesystem bytes.
"""

from __future__ import annotations

import hashlib
import unicodedata

from .constants import SEED_CANDIDATES


def stable_hash(s: str) -> int:
    """Leading 8 bytes of sha256(NFC-normalized s) as an unsigned 64-bit int."""
    b = unicodedata.normalize("NFC", s).encode("utf-8")
    return int.from_bytes(hashlib.sha256(b).digest()[:8], "big")


def seed_for(date_str: str, photo_path: str) -> int:
    """The shared seed tile (teaser center == reveal center). Pure, server-side.

    ``date_str`` is the ISO ``YYYY-MM-DD`` calendar date; ``photo_path`` is the raw
    relative path. Canonical pipe-delimited input ``"{date}|{photo_path}"``.
    """
    return SEED_CANDIDATES[stable_hash(f"{date_str}|{photo_path}") % len(SEED_CANDIDATES)]
