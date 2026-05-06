"""Cached frozenset of blocked IPs for middleware."""

from django.core.cache import cache

BLOCKED_IP_CACHE_KEY = 'blocked_ip_address_set_v1'
BLOCKED_IP_CACHE_TTL = 300


def invalidate_blocked_ip_cache():
    cache.delete(BLOCKED_IP_CACHE_KEY)


def get_blocked_ip_frozenset():
    cached = cache.get(BLOCKED_IP_CACHE_KEY)
    if cached is not None:
        return cached
    from settings.models import BlockedIPAddress

    rows = BlockedIPAddress.objects.exclude(ip_address='').values_list('ip_address', flat=True)
    ips = frozenset(str(s).strip() for s in rows if s and str(s).strip())
    cache.set(BLOCKED_IP_CACHE_KEY, ips, BLOCKED_IP_CACHE_TTL)
    return ips
