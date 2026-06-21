"""Photo filesystem access (design.md §3.3, §4.0).

A photo's identity *is* its relative path (raw filesystem bytes). We never
normalize stored/served paths — only the hash input (see hashing.py).
"""

from __future__ import annotations

import os
from urllib.parse import quote

from django.conf import settings

from .constants import VALID_EXTENSIONS


def url_for(photo_path: str) -> str:
    """FE-ready static URL. ``safe="/"`` keeps separators while percent-encoding
    accents/spaces, so it matches the on-disk file and survives Caddy routing.
    """
    return "/photos/" + quote(photo_path, safe="/")


def list_tier_files(tier_id: str) -> list[str]:
    """Raw relative paths (``"{tier}/{name}"``) of valid photos in a tier folder.

    Skips dotfiles, subdirectories, and non-image files (keeps ``.DS_Store`` out).
    Returns the raw ``listdir`` bytes verbatim — no normalization (§4.0).
    """
    folder = settings.PHOTOS_ROOT / tier_id
    if not folder.is_dir():
        return []
    result: list[str] = []
    for name in os.listdir(folder):
        if name.startswith("."):
            continue
        full = folder / name
        if not full.is_file():
            continue
        if os.path.splitext(name)[1].lower() not in VALID_EXTENSIONS:
            continue
        result.append(f"{tier_id}/{name}")
    return result
