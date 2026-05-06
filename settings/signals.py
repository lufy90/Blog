from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .ip_blacklist import invalidate_blocked_ip_cache
from .models import BlockedIPAddress


@receiver([post_save, post_delete], sender=BlockedIPAddress)
def clear_blocked_ip_cache_on_change(sender, **kwargs):
    invalidate_blocked_ip_cache()
