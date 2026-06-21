"""Django-Ninja API (design.md §5, §6).

Global session-cookie auth guard with two exemptions: the public ``GET /api/config``
and the DEBUG-only ``POST /api/dev/login``. CSRF stays on (§6.3).
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import HttpRequest
from django.middleware.csrf import get_token
from ninja import NinjaAPI
from ninja.errors import HttpError
from ninja.security import SessionAuth

from . import services
from .models import DailyEntry
from .schemas import (
    ConfigOut,
    FrozenEntryOut,
    GalleryOut,
    PickedOut,
    PickIn,
    StatsOut,
    SubmitIn,
    TodayOut,
)
from .timeutils import advance_dev_days, reset_dev_clock, today_str


class AllowlistAuth(SessionAuth):
    """Session-cookie auth + CSRF (inherited) + the §6.2 allowlist.

    Anonymous → 401 (return None); authenticated-but-not-allowlisted → 403.
    """

    def authenticate(self, request: HttpRequest, key: str | None) -> Any:
        user = request.user
        if not user.is_authenticated:
            return None
        if (getattr(user, "email", "") or "").lower() not in settings.ALLOWED_EMAILS:
            raise HttpError(403, "Esta conta não tem acesso.")
        return user


api = NinjaAPI(auth=AllowlistAuth(), title="entregasdalu")


@api.get("/config", auth=None, response=ConfigOut, by_alias=True)
def config(request: HttpRequest) -> dict[str, Any]:
    # Force the csrftoken cookie so the unauthenticated SPA can POST dev-login.
    get_token(request)
    return {"dev_login": settings.DEBUG and settings.DEV_LOGIN_ENABLED}


@api.get("/today", response=TodayOut, by_alias=True)
def today(request: HttpRequest) -> dict[str, Any]:
    return services.today_state(today_str())


@api.post("/pick", response=PickedOut, by_alias=True)
def pick(request: HttpRequest, payload: PickIn) -> dict[str, Any]:
    return services.pick(today_str(), payload.tier)


@api.post("/submit", response=FrozenEntryOut, by_alias=True)
def submit(request: HttpRequest, payload: SubmitIn) -> dict[str, Any]:
    return services.submit(today_str(), payload.text)


@api.get("/gallery", response=GalleryOut, by_alias=True)
def gallery(request: HttpRequest) -> dict[str, Any]:
    return services.gallery()


@api.get("/stats", response=StatsOut, by_alias=True)
def stats(request: HttpRequest) -> dict[str, Any]:
    return services.stats(today_str())


# Dev-login bypass: registered ONLY when DEBUG and DEV_LOGIN_ENABLED (§6.4). The
# settings module additionally refuses to boot if enabled while DEBUG=False.
if settings.DEBUG and settings.DEV_LOGIN_ENABLED:

    @api.post("/dev/login", auth=None)
    def dev_login(request: HttpRequest) -> dict[str, Any]:
        email = settings.DEV_LOGIN_EMAIL
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(username=email, defaults={"email": email})
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return {"ok": True, "email": email}

    @api.post("/dev/advance-day")
    def dev_advance_day(request: HttpRequest) -> dict[str, Any]:
        """Shift the in-memory dev clock forward one day (testing the daily loop)."""
        advance_dev_days(1)
        return {"today": today_str()}

    @api.post("/dev/reset")
    def dev_reset(request: HttpRequest) -> dict[str, Any]:
        """Wipe all entries and return the dev clock to today — a clean slate."""
        DailyEntry.objects.all().delete()
        reset_dev_clock()
        return {"today": today_str()}
