from django.core.management.base import BaseCommand

from entries.meaningless_comment_limits import purge_old_meaningless_attempts


class Command(BaseCommand):
    help = 'Delete meaningless comment attempt logs older than the retention setting.'

    def handle(self, *args, **options):
        deleted = purge_old_meaningless_attempts()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} meaningless comment attempt row(s).'))
