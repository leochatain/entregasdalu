"""Test settings — sets dev env *before* importing base, so the base module reads
the right values at import time (DEBUG gates secure cookies and the dev-login route).

Mirrors a local `runserver` with the dev-login bypass enabled.
"""

from __future__ import annotations

import os

os.environ["DEBUG"] = "True"
os.environ["DEV_LOGIN_ENABLED"] = "True"
os.environ.setdefault("ALLOWED_EMAILS", "lu@example.com,leochatain@gmail.com")
os.environ.setdefault("DEV_LOGIN_EMAIL", "lu@example.com")

from .settings import *  # noqa: F403
