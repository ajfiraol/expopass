from django.core.management.base import BaseCommand
from django.utils import timezone
from entrance.models import Staff, Pass
import qrcode
from django.core.files.base import ContentFile
from io import BytesIO


class Command(BaseCommand):
    help = "Automatically generate Pass records from Staff members"

    def handle(self, *args, **options):
        today = timezone.now().date()
        created_count = 0

        for staff in Staff.objects.all():

            # Prevent duplicate pass for same staff & day
            if Pass.objects.filter(staff=staff, day_entered=today).exists():
                continue

            pass_obj = Pass.objects.create(
                full_name=staff.name or "Staff Member",
                phone_number=staff.phone_number or "",
                booth_id=staff.booth_id or "N/A",
                staff=staff,
                day_entered=today,
            )

            # Generate QR content
            qr_data = f"PASS|{pass_obj.id}|{staff.staff_code}"
            qr = qrcode.make(qr_data)

            buffer = BytesIO()
            qr.save(buffer, format="PNG")

            pass_obj.qr_code_image.save(
                f"pass_{pass_obj.id}.png",
                ContentFile(buffer.getvalue()),
                save=True
            )

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ {created_count} passes generated successfully")
        )
