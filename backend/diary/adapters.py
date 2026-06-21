"""Allauth allowlist gate (design.md §6.2, layer 1).

Reject any non-allowlisted Google account *before* a Django user/session is
created, so unauthorized accounts never come into existence.
"""

from __future__ import annotations

from typing import Any

from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpResponseForbidden


class AllowlistSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request: Any, sociallogin: Any) -> bool:
        # Google signup must stay OPEN so first-time login can create the user.
        # The allowlist below is the real gate. (allauth's default delegates this
        # to the *account* adapter, which closes local signup — that would also
        # block first social login, hence this override.)
        return True

    def pre_social_login(self, request: Any, sociallogin: Any) -> None:
        email = (getattr(sociallogin.user, "email", "") or "").lower()
        if email not in settings.ALLOWED_EMAILS:
            raise ImmediateHttpResponse(HttpResponseForbidden("Só a Lu entra aqui."))


class AllowlistAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: Any) -> bool:
        # No local-account signup; access is the social allowlist only.
        return False
