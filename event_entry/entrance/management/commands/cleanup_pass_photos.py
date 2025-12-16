# entrance/management/commands/cleanup_pass_photos.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from entrance.models import Pass


class Command(BaseCommand):
    help = 'Delete pass photos older than 12 hours (run via cron or scheduled task)'

    def handle(self, *args, **options):
        cutoff_time = timezone.now() - timedelta(hours=12)
        
        # Find passes with photos older than 12 hours
        old_passes = Pass.objects.filter(
            photo_taken_at__lt=cutoff_time,
            photo__isnull=False
        )
        
        deleted_count = 0
        for pass_obj in old_passes:
            if pass_obj.photo:
                pass_obj.photo.delete()
                pass_obj.photo = None
                pass_obj.photo_taken_at = None
                pass_obj.save()
                deleted_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {deleted_count} pass photos older than 12 hours.'
            )
        )

