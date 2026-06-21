"""Django settings for entregasdalu (single-user academic-writing habit toy).

Env-driven (design.md §7.4). Dev needs no Google and no secrets: run with
``DEBUG=True DEV_LOGIN_ENABLED=True`` and the ``POST /api/dev/login`` bypass.
"""

from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# backend/ ; repo root is one level up (holds photos/ and data/).
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent

# Load a repo-root .env for local dev (no-op if absent). Real env always wins.
load_dotenv(REPO_ROOT / ".env")


def _env_bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _env_list(key: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(key, default).split(",") if item.strip()]


DEBUG = _env_bool("DEBUG", False)

# Dev-insecure fallback so `migrate`/tests run with zero config; prod must set it.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-do-not-use-in-prod")

ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS") or ["localhost", "127.0.0.1", "testserver"]
CSRF_TRUSTED_ORIGINS = _env_list("CSRF_TRUSTED_ORIGINS")

# Single-email allowlist (design.md §6.2), lowercased for case-insensitive checks.
ALLOWED_EMAILS = {e.lower() for e in _env_list("ALLOWED_EMAILS", "leochatain@gmail.com")}

# Dev-login bypass (design.md §6.4). Hard prod guard below.
DEV_LOGIN_ENABLED = _env_bool("DEV_LOGIN_ENABLED", False)
DEV_LOGIN_EMAIL = os.environ.get("DEV_LOGIN_EMAIL") or (
    next(iter(ALLOWED_EMAILS)) if ALLOWED_EMAILS else "dev@example.com"
)
if DEV_LOGIN_ENABLED and not DEBUG:
    raise ImproperlyConfigured("DEV_LOGIN_ENABLED must never be set while DEBUG=False.")

# Photo pool + the irreplaceable SQLite artifact. Default to the repo-root dirs
# so local dev and the compose bind-mounts share one set of paths (CLAUDE.md).
PHOTOS_ROOT = Path(os.environ.get("PHOTOS_ROOT", REPO_ROOT / "photos"))
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", REPO_ROOT / "data" / "app.db"))
# Throwaway cache for downscaled photo derivatives (diary/images.py). Reproducible
# from the originals, so it's safe to delete — kept out of the irreplaceable data/app.db.
THUMBS_ROOT = Path(os.environ.get("THUMBS_ROOT", REPO_ROOT / "data" / "thumbs"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "diary",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DATABASE_PATH),
        # A rare overlapping request never throws "database is locked" (design.md §7.4).
        "OPTIONS": {"timeout": 20, "init_command": "PRAGMA journal_mode=WAL;"},
    }
}

AUTH_PASSWORD_VALIDATORS = []  # one trusted user, password auth unused (principle #1)

LANGUAGE_CODE = "pt-br"
# DB/PK dates are São Paulo calendar dates; storage timestamps stay UTC (design.md §8).
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth / allauth -------------------------------------------------------
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
ACCOUNT_ADAPTER = "diary.adapters.AllowlistAccountAdapter"
SOCIALACCOUNT_ADAPTER = "diary.adapters.AllowlistSocialAccountAdapter"
# Skip allauth's "you are about to sign in with Google" interstitial: a plain GET
# on /accounts/google/login/ goes straight to Google. Safe for one trusted user —
# the only provider is Google and there's nothing to confirm. (Our SignIn button is
# a GET <a href>, which would otherwise land on that confirmation page.)
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
            "secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# --- Session / CSRF cookie (design.md §6.3) -------------------------------
# Same-origin in prod (Caddy) and dev (Vite proxy), so cookies just work.
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # the SPA reads csrftoken to echo it as X-CSRFToken
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
