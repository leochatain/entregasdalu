"""URL configuration (design.md §7.2).

``/api`` → Ninja; ``/accounts`` → allauth (Google flow); ``/photos`` → a resize
view that returns cached, downscaled JPEG derivatives (diary/images.py) rather
than the multi-MB originals. The photo route is always mounted: in dev Django
serves it directly, and in prod Caddy reverse-proxies ``/photos/*`` here (a
deliberate deviation from §7.2's static file_server, so the same downscaling
applies in both environments).
"""

from __future__ import annotations

from django.contrib import admin
from django.http import FileResponse, Http404, HttpRequest, HttpResponseBase
from django.urls import include, path, re_path

from diary.api import api
from diary.images import thumb_for


def serve_photo(_request: HttpRequest, path: str) -> HttpResponseBase:
    """Serve a cached, downscaled JPEG derivative of a pool photo (404 if missing)."""
    out = thumb_for(path)
    if out is None:
        raise Http404("foto não encontrada")
    resp = FileResponse(out.open("rb"), content_type="image/jpeg")
    # Derivatives are content-addressed (cache key folds in mtime+size), so a long
    # browser cache is safe — recuration changes the URL's bytes via a new thumb.
    resp["Cache-Control"] = "public, max-age=86400"
    return resp


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("accounts/", include("allauth.urls")),
    re_path(r"^photos/(?P<path>.*)$", serve_photo),
]
