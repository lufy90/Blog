from django.http import HttpResponseForbidden

from entries.utils import get_client_ip

from settings.ip_blacklist import get_blocked_ip_frozenset


class IPBlacklistMiddleware:
    """Return 403 for any request whose client IP is listed in BlockedIPAddress."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        blocked = get_blocked_ip_frozenset()
        if blocked:
            ip = get_client_ip(request)
            if ip and ip in blocked:
                return HttpResponseForbidden('Forbidden')
        return self.get_response(request)
