"""Frozen contracts and tier config (design.md §3.5, §4.2; spec.md §3).

Everything here is interpreted against persisted ``DailyEntry`` rows. Changing a
grid constant or a tier id silently corrupts history — treat as append-only.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Mosaic grid (frozen, app-wide) ---------------------------------------
GRID_ROWS = 8
GRID_COLS = 6
GRID_TILES = GRID_ROWS * GRID_COLS  # 48, row-major: idx = row*6 + col

# Seed candidates = the inner 2x2 block (rows {3,4} x cols {2,3}).
SEED_CANDIDATES: tuple[int, ...] = (20, 21, 26, 27)

# Geometric center sits *between* tiles (even dims), so the .5 is the midline.
CENTER_ROW = (GRID_ROWS - 1) / 2  # 3.5
CENTER_COL = (GRID_COLS - 1) / 2  # 2.5

# --- Photo pool -----------------------------------------------------------
VALID_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png"})


# --- Difficulty tiers (spec.md §3; "Forgiving" set) -----------------------
@dataclass(frozen=True)
class Tier:
    id: str  # == folder name under PHOTOS_ROOT
    name: str  # display name (pt-BR)
    word_target: int


TIERS: tuple[Tier, ...] = (
    Tier("rascunho", "Rascunho", 150),
    Tier("capitulo", "Capítulo", 400),
    Tier("tese", "Tese", 800),
)

TIERS_BY_ID: dict[str, Tier] = {t.id: t for t in TIERS}


def tier_for_path(photo_path: str) -> Tier:
    """Tier of a stored photo: identity is the path, tier = its top folder."""
    return TIERS_BY_ID[photo_path.split("/", 1)[0]]
