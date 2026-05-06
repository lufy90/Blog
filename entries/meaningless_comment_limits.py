"""Retention and per-IP rate limits for rejected meaningless comments."""

from datetime import timedelta

from django.utils import timezone

from settings.models import SiteSettings

from .models import MeaninglessCommentAttempt


def purge_old_meaningless_attempts():
    """Delete attempt rows older than SiteSettings.meaningless_attempt_retention_days."""
    from .models import MeaninglessCommentAttempt

    days = int(SiteSettings.get_value('meaningless_attempt_retention_days', 30) or 30)
    if days < 1:
        days = 1
    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = MeaninglessCommentAttempt.objects.filter(created_on__lt=cutoff).delete()
    return deleted


def meaningless_attempt_count_for_ip(ip, window_minutes):
    """How many meaningless attempts this IP has within the sliding window."""
    from .models import MeaninglessCommentAttempt

    minutes = int(window_minutes or 0)
    if minutes < 1:
        minutes = 1
    since = timezone.now() - timedelta(minutes=minutes)
    qs = MeaninglessCommentAttempt.objects.filter(created_on__gte=since)
    if ip:
        return qs.filter(ip_address=ip).count()
    return qs.filter(ip_address='').count()


def is_meaningless_rate_limited(ip):
    """True when this IP has reached the configured max attempts in the window."""
    max_n = int(SiteSettings.get_value('meaningless_rate_limit_max_attempts', 10) or 0)
    if max_n < 1:
        return False
    window = int(SiteSettings.get_value('meaningless_rate_limit_window_minutes', 60) or 60)
    return meaningless_attempt_count_for_ip(ip, window) >= max_n


def log_meaningless_attempt(entry, content, ip, parent_comment=None):

    text = (content or '')[:10000]
    MeaninglessCommentAttempt.objects.create(
        entry=entry,
        parent_comment=parent_comment,
        content=text,
        ip_address=(ip or '')[:45],
    )
