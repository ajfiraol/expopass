# entrance/management/commands/import_staff.py

import csv
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from entrance.models import Staff
from entrance.utils import generate_qr


class Command(BaseCommand):
    help = 'Import staff data from CSV and generate QR codes (UUID BASED)'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file to import.')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        # Make absolute path if needed
        if not os.path.isabs(csv_file_path):
            csv_file_path = os.path.join(os.getcwd(), csv_file_path)

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found: {csv_file_path}'))
            return

        created_count = 0
        error_count = 0

        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row_num, row in enumerate(reader, start=1):
                try:
                    # Extract and sanitize fields
                    name = row.get('Name', '').strip() or 'Unknown'
                    booth_id = row.get('Booth ID', '').strip() or None
                    phone_no = row.get('Phone no', '').strip()
                    location = row.get('Location', '1p').strip()
                    staff_type = row.get('Staff Type', 'Staff').strip()

                    # Normalize phone number
                    phone_no = ''.join(filter(str.isdigit, phone_no)) if phone_no else 'N/A'

                    # Validate location
                    if location not in dict(Staff.LOCATION_CHOICES):
                        location = '1p'

                    # Normalize staff_type
                    staff_type = staff_type.upper()
                    if staff_type != 'VIP':
                        staff_type = 'Staff'

                    # ✅ CREATE a new staff record
                    staff = Staff.objects.create(
                        name=name,
                        booth_id=booth_id,
                        phone_number=phone_no,
                        location=location,
                        staff_type=staff_type
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Row {row_num}: Created {staff.name} ({staff_type})'))

                    # ✅ Generate QR code using staff_code (what scanner expects)
                    qr_path = generate_qr(staff.staff_code)
                    with open(qr_path, 'rb') as f:
                        staff.qr_code_image.save(
                            f'staff_{staff.staff_code}.png',
                            File(f),
                            save=True
                        )

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'Row {row_num} error: {str(e)}'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n==== IMPORT SUMMARY ===='))        
        self.stdout.write(self.style.SUCCESS(f'Total created: {created_count}'))
        self.stdout.write(self.style.ERROR(f'Total errors: {error_count}'))
