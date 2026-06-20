"""Reveal module (design.md §4.2).

Computed once at submit and persisted as ``revealed_tiles``; the gallery renders
that stored list verbatim and never recomputes. The stored list *is* the frozen
truth — immune to any later change in this algorithm, the grid, or the seed logic.
"""

from __future__ import annotations

from .constants import CENTER_COL, CENTER_ROW, GRID_COLS, GRID_TILES
from .hashing import seed_for, stable_hash


def tile_count(p: float) -> int:
    """N = max(1, round(p*48)); ``round`` is banker's rounding (deterministic)."""
    return max(1, round(p * GRID_TILES))


def reveal_order(date_str: str, photo_path: str) -> list[int]:
    """All 48 tiles sorted nearest-first from the seed → connected, centered blob.

    Sort key (frozen, §4.2): (chebyshev_to_seed, chebyshev_to_center, hash tie-break).
    """
    seed = seed_for(date_str, photo_path)
    seed_row, seed_col = divmod(seed, GRID_COLS)

    def key(tile: int) -> tuple[int, float, int]:
        row, col = divmod(tile, GRID_COLS)
        d_seed = max(abs(row - seed_row), abs(col - seed_col))
        d_center = max(abs(row - CENTER_ROW), abs(col - CENTER_COL))
        return (d_seed, d_center, stable_hash(f"{tile}|{seed}"))

    return sorted(range(GRID_TILES), key=key)


def compute_reveal(date_str: str, photo_path: str, p: float) -> list[int]:
    """The first N tiles in reveal order — the persisted, ordered frozen truth."""
    return reveal_order(date_str, photo_path)[: tile_count(p)]
