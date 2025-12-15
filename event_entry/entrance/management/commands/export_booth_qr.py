import os
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

from entrance.models import Staff
from entrance.utils import generate_qr


class Command(BaseCommand):
    help = "Export staff QR codes into local folders grouped by location/booth, with a staff list per booth."

    def handle(self, *args, **options):
        # Use default root from settings so UI can read it
        export_root = Path(getattr(settings, "BOOTH_QR_EXPORT_ROOT", settings.BASE_DIR / "booth_qr_export")).resolve()
        export_root.mkdir(parents=True, exist_ok=True)

        total_qr = 0
        booths_seen = set()

        # Order for nice grouping
        queryset = Staff.objects.all().order_by("location", "booth_id", "name")

        for staff in queryset:
            location = staff.location or "unknown_location"
            booth_id = staff.booth_id or "no_booth"

            # Folder structure: root/location/booth_id/
            booth_dir = export_root / location / booth_id
            booth_dir.mkdir(parents=True, exist_ok=True)

            # Ensure QR exists in media using staff_code (UUID-based)
            qr_path = generate_qr(staff.staff_code)

            # Copy QR into this folder with a stable filename
            qr_filename = f"{staff.staff_code}.png"
            target_file = booth_dir / qr_filename

            with open(qr_path, "rb") as src, open(target_file, "wb") as dst:
                dst.write(src.read())

            total_qr += 1

            # Track booths we have processed so we can build a per‑booth staff list
            booths_seen.add((location, booth_id))

        # For each booth, write a staff_list.txt with basic info
        for (location, booth_id) in booths_seen:
            booth_dir = export_root / location / booth_id
            staff_in_booth = queryset.filter(location=location, booth_id=booth_id)

            list_path = booth_dir / "staff_list.txt"
            with open(list_path, "w", encoding="utf-8") as f:
                f.write(f"Location: {location}\n")
                f.write(f"Booth ID: {booth_id}\n")
                f.write(f"Total staff: {staff_in_booth.count()}\n")
                f.write("\n")
                f.write("staff_code,name,phone_number,staff_type\n")
                for s in staff_in_booth:
                    line = f"{s.staff_code},{s.name},{s.phone_number},{s.staff_type}\n"
                    f.write(line)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Exported {total_qr} QR codes into {export_root} "
                f"with staff_list.txt per booth."
            )
        )


