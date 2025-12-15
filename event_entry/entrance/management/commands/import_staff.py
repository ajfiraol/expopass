# entrance/management/commands/import_staff.py
import csv
import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from entrance.models import Staff
from entrance.utils import generate_qr
from pathlib import Path


class Command(BaseCommand):
    help = 'Import staff data from CSV and generate QR codes (STAFF CODE BASED)'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        if not os.path.isabs(csv_file_path):
            csv_file_path = os.path.join(os.getcwd(), csv_file_path)

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'CSV not found: {csv_file_path}'))
            return

        created_count = 0
        updated_count = 0
        error_count = 0

        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row_num, row in enumerate(reader, start=1):
                try:
                    name = row.get('Name', '').strip()
                    booth_id = row.get('Booth ID', '').strip()
                    phone_no = row.get('Phone no', '').strip()
                    staff_code = row.get('Staff Code', '').strip()
                    location = row.get('Location', '1p').strip()
                    staff_type = row.get('Staff Type', 'VIP').strip()

                    if not staff_code:
                        self.stdout.write(self.style.WARNING(
                            f'Row {row_num}: Missing staff_code, skipped'
                        ))
                        error_count += 1
                        continue

                    phone_no = ''.join(filter(str.isdigit, phone_no)) if phone_no else None

                    staff, created = Staff.objects.update_or_create(
                        staff_code=staff_code,
                        defaults={
                            'name': name or f'Staff {staff_code}',
                            'booth_id': booth_id or None,
                            'phone_number': phone_no,
                            'location': location if location in ['1p', '2p', '3p', '4p', 'O'] else '1p',
                            'staff_type': staff_type if staff_type in ['VIP', 'Sales'] else 'VIP',
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'Created {staff_code}'))
                    else:
                        updated_count += 1
                        self.stdout.write(f'Updated {staff_code}')

                    # ✅ GENERATE QR FROM STAFF CODE
                    qr_path = generate_qr(staff.staff_code)

                    if not staff.qr_code_image:
                        with open(qr_path, 'rb') as f:
                            staff.qr_code_image.save(
                                f'staff_{staff.staff_code}.png',
                                File(f),
                                save=True
                            )

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(
                        f'Row {row_num} error: {str(e)}'
                    ))

        self.stdout.write(self.style.SUCCESS('\n==== IMPORT SUMMARY ===='))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count}'))
        self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
