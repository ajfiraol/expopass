from django.core.management.base import BaseCommand
from django.utils import timezone
from entrance.models import Staff, Pass

class Command(BaseCommand):
    help = "Automatically generate Pass records from Staff members using staff QR"

    def handle(self, *args, **options):
        today = timezone.now().date()
        created_count = 0

        for staff in Staff.objects.all():
            # Skip if Pass already exists for today
            if Pass.objects.filter(staff=staff, day_entered=today).exists():
                continue

            pass_obj = Pass.objects.create(
                full_name=staff.name or "Staff Member",
                phone_number=staff.phone_number or "",
                booth_id=staff.booth_id or "N/A",
                staff=staff,
                day_entered=today,
            )

            # Copy staff QR code to pass
            if staff.qr_code_image:
                pass_obj.qr_code_image.save(
                    staff.qr_code_image.name.split('/')[-1],  # keep the filename
                    staff.qr_code_image.file,
                    save=True
                )

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ {created_count} passes generated successfully")
        )
