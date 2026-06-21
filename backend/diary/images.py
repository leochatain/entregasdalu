"""On-demand downscaled photo derivatives (performance).

Real curated photos are full-resolution camera files (3-7 MP, 1-22 MB each). The
Mosaic only ever displays them ~480px wide, so serving the originals means the
browser downloads megabytes and decodes ~100 MB bitmaps per photo — catastrophic
in the gallery, which renders one per submitted day. We serve a cached, downscaled
JPEG instead.

This is purely cosmetic: reveal math uses no pixels (it sorts tile *indices*), and
the whole photo still reaches the browser — just smaller. That honors the
"frost is a CSS overlay, the full image is allowed through" principle (spec #1);
we're not hiding tiles server-side, only shrinking the bytes.

Derivatives are reproducible from the originals, so they live in a throwaway cache
dir (``THUMBS_ROOT``) — never mixed with the irreplaceable ``data/app.db``. The
cache key folds in mtime + size, so re-curating a path regenerates automatically.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageOps

# Longest edge of the served derivative. Display is ~480px wide; 1280 covers that
# at >2x DPR with headroom for the full-screen gallery modal.
THUMB_MAX_EDGE = 1280
THUMB_QUALITY = 82


def thumb_for(rel_path: str) -> Path | None:
    """Path to a cached downscaled JPEG of ``rel_path``, generated on first use.

    Returns ``None`` when the source is missing or not a regular file (caller 404s).
    The original on disk is never modified.
    """
    src = settings.PHOTOS_ROOT / rel_path
    if not src.is_file():
        return None

    stat = src.stat()
    # Key on (path, mtime, size, params) so any edit/recuration busts the cache.
    key = f"{rel_path}|{int(stat.st_mtime)}|{stat.st_size}|{THUMB_MAX_EDGE}|{THUMB_QUALITY}"
    name = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32] + ".jpg"
    cache_dir: Path = settings.THUMBS_ROOT
    out = cache_dir / name
    if out.exists():
        return out

    cache_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)  # bake in camera orientation (we drop EXIF)
        im = im.convert("RGB")
        im.thumbnail((THUMB_MAX_EDGE, THUMB_MAX_EDGE), Image.Resampling.LANCZOS)
        tmp = out.with_suffix(".tmp")  # write-then-rename so readers never see a partial file
        im.save(tmp, "JPEG", quality=THUMB_QUALITY, optimize=True)
        tmp.replace(out)
    return out
