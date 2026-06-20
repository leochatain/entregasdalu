"""URL configuration (design.md §7.2).

``/api`` → Ninja; ``/accounts`` → allauth (Google flow). In DEBUG, Django also
serves ``/photos/*`` so the backend runs end-to-end locally without Caddy.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from diary.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("accounts/", include("allauth.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(
            r"^photos/(?P<path>.*)$",
            serve,
            {"document_root": str(settings.PHOTOS_ROOT)},
        ),
    ]
