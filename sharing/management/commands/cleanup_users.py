"""
Management command to clean up stale online users
Run this on server startup to clear old sessions
"""
from django.core.management.base import BaseCommand
from sharing.models import OnlineUser


class Command(BaseCommand):
    help = 'Clear all stale online users from previous sessions'

    def handle(self, *args, **options):
        count = OnlineUser.objects.all().count()
        OnlineUser.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned up {count} stale online users')
        )
