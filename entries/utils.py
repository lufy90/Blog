"""Small helpers shared by views and admin."""


def get_client_ip(request):
    """Best-effort client IP; prefers X-Forwarded-For when behind a proxy."""
    if request is None:
        return ''
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()[:45]
    addr = request.META.get('REMOTE_ADDR') or ''
    return str(addr)[:45]
