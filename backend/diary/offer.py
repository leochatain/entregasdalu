"""Daily offer module (design.md §4.1).

Deterministic per (date, folder contents). Recomputed only for *today*; past days
are captured by their ``DailyEntry``, so changing folder contents never alters
history. Nothing here is stored.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from .constants import TIERS
from .hashing import seed_for, stable_hash
from .photos import list_tier_files, url_for


@dataclass(frozen=True)
class OfferSlot:
    tier: str
    name: str
    word_target: int
    photo_url: str
    seed_tile: int
    photo_path: str  # internal: pinned by /api/pick; not part of the public payload

    def public(self) -> dict[str, object]:
        """The FE-facing slot fields (§5.1) — photo_path is intentionally omitted."""
        return {
            "tier": self.tier,
            "name": self.name,
            "word_target": self.word_target,
            "photo_url": self.photo_url,
            "seed_tile": self.seed_tile,
        }


def compute_offer(date_str: str, unlocked: set[str]) -> list[OfferSlot | None]:
    """Three slots, one per tier (``None`` for an empty pool → 'sem foto hoje').

    ``unlocked`` is the set of already-submitted ``photo_path``s (raw bytes).
    """
    slots: list[OfferSlot | None] = []
    for tier in TIERS:
        pool = [p for p in list_tier_files(tier.id) if p not in unlocked]
        # B1: stable order before the modulo. Sort key is NFC-normalized (hash-only
        # normalization, §4.0); the stored/served strings stay raw.
        pool.sort(key=lambda p: unicodedata.normalize("NFC", p))
        if not pool:
            slots.append(None)
            continue
        photo_path = pool[stable_hash(f"{date_str}|{tier.id}") % len(pool)]
        slots.append(
            OfferSlot(
                tier=tier.id,
                name=tier.name,
                word_target=tier.word_target,
                photo_url=url_for(photo_path),
                seed_tile=seed_for(date_str, photo_path),
                photo_path=photo_path,
            )
        )
    return slots
