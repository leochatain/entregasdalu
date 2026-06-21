"""HTTP layer: auth guards, dev-login, camelCase aliasing, the full loop, OpenAPI."""

from __future__ import annotations

import json

import pytest
from django.conf import settings

pytestmark = pytest.mark.django_db


# --- Auth guard (design.md §6.2) ------------------------------------------
def test_today_requires_auth():
    from django.test import Client

    resp = Client().get("/api/today")
    assert resp.status_code == 401


def test_config_is_auth_exempt():
    from django.test import Client

    resp = Client().get("/api/config")
    assert resp.status_code == 200
    assert resp.json() == {"devLogin": True}  # DEBUG + DEV_LOGIN_ENABLED in tests


def test_non_allowlisted_user_is_403(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="intruder@example.com", email="intruder@example.com"
    )
    client.force_login(user)
    assert client.get("/api/today").status_code == 403


# --- Dev login (design.md §6.4) -------------------------------------------
@pytest.mark.skipif(
    not (settings.DEBUG and settings.DEV_LOGIN_ENABLED),
    reason="dev-login route only registered when DEBUG and DEV_LOGIN_ENABLED",
)
def test_dev_login_then_authenticated(client):
    assert client.get("/api/today").status_code == 401
    resp = client.post("/api/dev/login")
    assert resp.status_code == 200
    assert resp.json()["email"] == settings.DEV_LOGIN_EMAIL
    # Session now established → protected endpoint works.
    assert client.get("/api/today").status_code == 200


# --- camelCase + full loop (design.md §5.1) -------------------------------
def test_today_offer_uses_camelcase(auth_client, photos):
    body = auth_client.get("/api/today").json()
    assert body["state"] == "none"
    slot = body["offer"][0]
    assert set(slot) == {"tier", "name", "wordTarget", "photoUrl", "seedTile"}


def test_full_loop(auth_client, photos):
    # config → today/offer → pick → submit → gallery → stats
    today = auth_client.get("/api/today").json()
    assert today["state"] == "none"

    pick = auth_client.post(
        "/api/pick", data=json.dumps({"tier": "capitulo"}), content_type="application/json"
    ).json()
    assert pick["tier"] == "capitulo"
    assert pick["wordTarget"] == 400

    submit = auth_client.post(
        "/api/submit",
        data=json.dumps({"text": "palavra " * 200}),
        content_type="application/json",
    ).json()
    assert submit["effectiveWordCount"] == 200
    assert submit["performancePct"] == pytest.approx(0.5)
    assert len(submit["revealedTiles"]) == 24

    gallery = auth_client.get("/api/gallery").json()
    assert gallery["photosCollected"] == 1
    assert "poolTotal" not in gallery

    stats = auth_client.get("/api/stats").json()
    assert stats["daysDelivered"] == 1
    assert stats["currentStreak"] == 1


def test_resume_after_pick_routes_to_editor(auth_client, photos):
    auth_client.post(
        "/api/pick", data=json.dumps({"tier": "tese"}), content_type="application/json"
    )
    body = auth_client.get("/api/today").json()
    assert body["state"] == "picked"
    assert body["picked"]["wordTarget"] == 800


def test_openapi_schema_generates(auth_client):
    resp = auth_client.get("/api/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "/api/today" in schema["paths"]
    assert "/api/submit" in schema["paths"]
