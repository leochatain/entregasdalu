"""Shared fixtures: a controlled temp photo pool + auth helpers."""

from __future__ import annotations

import pytest

# Known, fixed pools so determinism assertions are reproducible.
TIER_FILES: dict[str, list[str]] = {
    "rascunho": ["sol.png", "gato.png", "limao.png", "pato.png"],
    "capitulo": ["cafe.png", "lua.png", "pao.png", "planta.png"],
    "tese": ["mar.png", "coracao.png", "melancia.png", "montanha.png"],
}

# A minimal valid PNG header is enough — the backend never decodes the bytes.
_PNG = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def photos(tmp_path, settings):
    """Build a temp PHOTOS_ROOT with the fixed tier pools and point settings at it."""
    root = tmp_path / "photos"
    for tier, files in TIER_FILES.items():
        folder = root / tier
        folder.mkdir(parents=True)
        for name in files:
            (folder / name).write_bytes(_PNG)
    settings.PHOTOS_ROOT = root
    return root


@pytest.fixture
def auth_client(client, django_user_model):
    """A test client logged in as an allowlisted user (bypasses Google + CSRF)."""
    user = django_user_model.objects.create_user(username="lu@example.com", email="lu@example.com")
    client.force_login(user)
    return client
