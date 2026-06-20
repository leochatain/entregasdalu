"""The single table (design.md §3.1). One row per São Paulo calendar day."""

from __future__ import annotations

from django.db import models


class DailyEntry(models.Model):
    date = models.DateField(primary_key=True)  # São Paulo calendar date (no time/tz)
    photo_path = models.CharField(max_length=255)  # relative to PHOTOS_ROOT (raw bytes)
    word_target = models.PositiveIntegerField()  # denormalized on purpose (§3.1)
    status = models.CharField(
        max_length=12,
        default="picked",
        choices=[("picked", "picked"), ("submitted", "submitted")],
    )
    # Submit-time fields: null while 'picked', set atomically on submit (§4.4).
    effective_word_count = models.PositiveIntegerField(null=True)
    performance_pct = models.FloatField(null=True)  # p in [0, 1]
    revealed_tiles = models.JSONField(null=True)  # list[int] <= 48 — the frozen truth
    picked_at = models.DateTimeField()  # tz-aware (UTC)
    submitted_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.date} {self.photo_path} ({self.status})"
