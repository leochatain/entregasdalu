"""URL configuration (design.md §7.2).

``/api`` → Ninja; ``/accounts`` → allauth (Google flow). In DEBUG, Django also
serves ``/photos/*`` so the backend runs end-to-end locally without Caddy — but
through a resize view that returns cached, downscaled derivatives (diary/images.py)
rather than the multi-MB originals. When prod infra lands, Caddy should proxy
``/photos/*`` to this view (not serve the raw files) so the same downscaling holds.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404, HttpRequest, HttpResponseBase
from django.urls import include, path, re_path

from diary.api import api
from diary.images import thumb_for

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("accounts/", include("allauth.urls")),
]


def serve_photo(_request: HttpRequest, path: str) -> HttpResponseBase:
    """Serve a cached, downscaled JPEG derivative of a pool photo (404 if missing)."""
    out = thumb_for(path)
    if out is None:
        raise Http404("foto não encontrada")
    return FileResponse(out.open("rb"), content_type="image/jpeg")


if settings.DEBUG:
    urlpatterns += [
        re_path(r"^photos/(?P<path>.*)$", serve_photo),
    ]
