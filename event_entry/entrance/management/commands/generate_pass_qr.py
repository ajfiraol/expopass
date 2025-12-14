from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from entrance.models import Pass, Staff
from entrance.utils import generate_qr
from datetime import date


class Command(BaseCommand):
    help = 'Generate QR codes for all Passes.'

    def handle(self, *args, **options):

        # ---- Create staff ----
        staff_data = [
            {"name": "Alice Johnson", "phone_number": "555-1001"},
            {"name": "Bob Smith", "phone_number": "555-1002"},
            {"name": "Carol Lee", "phone_number": "555-1003"},
        ]

        for s in staff_data:
            obj, created = Staff.objects.get_or_create(
                name=s["name"],
                defaults={"phone_number": s["phone_number"]}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created staff: {obj.name}'))

        # ---- Create passes ----
        pass_data = [
            {"full_name": "Eden Abebe", "phone_number": "0911000001", "booth_id": "A1", "staff_name": "Alice Johnson"},
            {"full_name": "Musa Bekele", "phone_number": "0911000002", "booth_id": "B2", "staff_name": "Bob Smith"},
            {"full_name": "Sara Tesfaye", "phone_number": "0911000003", "booth_id": "C3", "staff_name": "Carol Lee"},
        ]

        for pd in pass_data:
            staff = Staff.objects.get(name=pd["staff_name"])

            p, created = Pass.objects.get_or_create(
                full_name=pd["full_name"],
                phone_number=pd["phone_number"],
                booth_id=pd["booth_id"],
                staff=staff,
                day_entered=date.today(),
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created pass: {p.full_name}'))

            # ---- Generate QR ----
            qr_path = generate_qr(p.id)

            # ---- Save QR correctly to ImageField ----
            with open(qr_path, "rb") as f:
                p.qr_code_image.save(
                    qr_path.name,
                    File(f),
                    save=True
                )

            self.stdout.write(
                self.style.SUCCESS(f'Generated QR for {p.full_name}')
            )

        self.stdout.write(self.style.SUCCESS('Created 3 passes and generated QR codes successfully.'))
