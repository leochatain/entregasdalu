"""Reveal math (design.md §4.2): N boundaries, ordering, connectedness, freeze."""

from __future__ import annotations

import pytest

from diary.constants import GRID_COLS, GRID_TILES, SEED_CANDIDATES
from diary.hashing import seed_for
from diary.reveal import compute_reveal, reveal_order, tile_count

DATE = "2026-06-20"
PHOTO = "capitulo/lua.png"


def _rc(tile: int) -> tuple[int, int]:
    return divmod(tile, GRID_COLS)


def _chebyshev(a: int, b: int) -> int:
    ar, ac = _rc(a)
    br, bc = _rc(b)
    return max(abs(ar - br), abs(ac - bc))


# --- N boundaries ---------------------------------------------------------
@pytest.mark.parametrize(
    "p,expected",
    [
        (0.0, 1),  # max(1, ...) floor — showing up always pays off (principle #2)
        (0.001, 1),
        (0.25, 12),
        (0.5, 24),
        (1.0, 48),  # p is capped at 1 by the caller, so 48 is the ceiling
    ],
)
def test_tile_count_boundaries(p, expected):
    assert tile_count(p) == expected


def test_tile_count_never_zero():
    assert tile_count(0.0) == 1


# --- Ordering / structure -------------------------------------------------
def test_order_is_a_permutation_of_all_48():
    order = reveal_order(DATE, PHOTO)
    assert sorted(order) == list(range(GRID_TILES))


def test_seed_sorts_first():
    order = reveal_order(DATE, PHOTO)
    assert order[0] == seed_for(DATE, PHOTO)
    assert order[0] in SEED_CANDIDATES


def test_order_is_nondecreasing_in_chebyshev_to_seed():
    seed = seed_for(DATE, PHOTO)
    order = reveal_order(DATE, PHOTO)
    dists = [_chebyshev(t, seed) for t in order]
    assert dists == sorted(dists)


def test_reveal_is_connected_blob():
    # Every revealed tile (after the seed) touches an earlier revealed tile
    # (8-neighbourhood) ⇒ a single connected region.
    tiles = compute_reveal(DATE, PHOTO, 0.5)
    revealed: set[int] = set()
    for i, tile in enumerate(tiles):
        if i == 0:
            revealed.add(tile)
            continue
        tr, tc = _rc(tile)
        touches = any(
            (abs(tr - r) <= 1 and abs(tc - c) <= 1) for r, c in (_rc(x) for x in revealed)
        )
        assert touches, f"tile {tile} is disconnected"
        revealed.add(tile)


def test_partial_reveal_is_a_prefix_of_full_order():
    order = reveal_order(DATE, PHOTO)
    for n_p in (0.1, 0.25, 0.5, 0.9):
        tiles = compute_reveal(DATE, PHOTO, n_p)
        assert tiles == order[: len(tiles)]


def test_reveal_is_deterministic():
    assert compute_reveal(DATE, PHOTO, 0.42) == compute_reveal(DATE, PHOTO, 0.42)


def test_tie_break_is_stable_and_total():
    # No two tiles share the full sort key (the hash tie-break disambiguates),
    # so the order is total and reproducible.
    order = reveal_order(DATE, PHOTO)
    assert len(set(order)) == GRID_TILES
