import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File

from entrance.models import Staff
from entrance.utils import generate_qr


class Command(BaseCommand):
    help = "Upsert Staff records from cleaned.csv without deleting existing data."

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        csv_path = Path(base_dir) / "cleaned.csv"

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"cleaned.csv not found at {csv_path}"))
            return

        created = 0
        updated = 0
        skipped = 0

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("Name") or "").strip() or "Unknown"
                booth_id = (row.get("Booth ID") or "").strip() or None
                staff_code_sheet = (row.get("Staff Code") or "").strip()
                phone_no = (row.get("Phone no") or "").strip()
                location = (row.get("Location") or "").strip() or "1p"
                staff_type = (row.get("Staff Type") or "").strip() or "Staff"
                sold_raw = (row.get("Sold") or "").strip().lower()

                # Normalize phone number
                phone_no_norm = "".join(filter(str.isdigit, phone_no)) if phone_no else "N/A"

                # Validate location
                if location not in dict(Staff.LOCATION_CHOICES):
                    location = "1p"

                # Normalize staff_type
                staff_type_norm = staff_type.upper()
                if staff_type_norm not in ("VIP", "STAFF", "SALES"):
                    staff_type_norm = "Staff"
                if staff_type_norm == "SALES":
                    staff_type_norm = "Staff"

                # Interpret Sold (yes/no) if column exists; default False
                sold_flag = sold_raw in ("yes", "y", "true", "1")

                if not staff_code_sheet:
                    self.stdout.write(
                        self.style.WARNING(f"Skipping row without Staff Code: {row}")
                    )
                    skipped += 1
                    continue

                staff, created_flag = Staff.objects.get_or_create(
                    staff_code_sheet=staff_code_sheet,
                    defaults={
                        "name": name,
                        "booth_id": booth_id,
                        "phone_number": phone_no_norm,
                        "location": location,
                        "staff_type": staff_type_norm,
                        "sold": sold_flag,
                    },
                )

                if created_flag:
                    created += 1
                    # Generate QR if missing
                    if not staff.qr_code_image:
                        qr_path = generate_qr(staff.staff_code)
                        with open(qr_path, "rb") as qf:
                            staff.qr_code_image.save(
                                f"staff_{staff.staff_code}.png",
                                File(qf),
                                save=True,
                            )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created staff {staff} (sheet code: {staff_code_sheet})"
                        )
                    )
                else:
                    # Optional: light update without destroying existing relationships
                    changed = False
                    if staff.name != name:
                        staff.name = name
                        changed = True
                    if staff.booth_id != booth_id:
                        staff.booth_id = booth_id
                        changed = True
                    if staff.phone_number != phone_no_norm:
                        staff.phone_number = phone_no_norm
                        changed = True
                    if staff.location != location:
                        staff.location = location
                        changed = True
                    if staff.staff_type != staff_type_norm:
                        staff.staff_type = staff_type_norm
                        changed = True

                    if staff.sold != sold_flag:
                        staff.sold = sold_flag
                        changed = True

                    if changed:
                        staff.save()
                        updated += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updated staff {staff} (sheet code: {staff_code_sheet})"
                            )
                        )
                    else:
                        skipped += 1

        self.stdout.write(self.style.SUCCESS("==== STAFF UPDATE SUMMARY ===="))
        self.stdout.write(self.style.SUCCESS(f"Created: {created}"))
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated}"))
        self.stdout.write(self.style.SUCCESS(f"Skipped (no change or no code): {skipped}"))


