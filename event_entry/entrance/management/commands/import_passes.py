import csv
from django.core.management.base import BaseCommand
from entrance.models import Pass, Staff
from entrance.utils import generate_qr
from django.conf import settings
from pathlib import Path
from uuid import UUID
from datetime import datetime

class Command(BaseCommand):
    help = 'Import passes from a CSV file and generate QR codes.'

    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csvfile = options['csvfile']
        with open(csvfile, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Required columns: full_name, phone_number, booth_id, staff_name, day_entered (YYYY-MM-DD)
                staff, _ = Staff.objects.get_or_create(name=row['staff_name'], defaults={'phone_number': row.get('staff_phone', '')})
                pass_obj = Pass.objects.create(
                    full_name=row['full_name'],
                    phone_number=row['phone_number'],
                    booth_id=row['booth_id'],
                    staff=staff,
                    day_entered=datetime.strptime(row['day_entered'], '%Y-%m-%d').date()
                )
                # Generate QR code for this pass
                generate_qr(pass_obj.id)
                self.stdout.write(self.style.SUCCESS(f'Created pass for {pass_obj.full_name}'))
        self.stdout.write(self.style.SUCCESS('Import complete.'))
