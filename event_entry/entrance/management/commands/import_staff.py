# entrance/management/commands/import_staff.py
import csv
import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from entrance.models import Staff
from entrance.utils import generate_qr  # This should work now
from pathlib import Path


class Command(BaseCommand):
    help = 'Import staff data from CSV and generate QR codes for each staff member'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file'
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        
        # Convert to absolute path if relative
        if not os.path.isabs(csv_file_path):
            csv_file_path = os.path.join(os.getcwd(), csv_file_path)
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found: {csv_file_path}'))
            self.stdout.write(f'Current working directory: {os.getcwd()}')
            return

        self.stdout.write(self.style.SUCCESS(f'Importing from: {csv_file_path}'))
        
        # Create QR code directory if it doesn't exist
        qr_dir = Path(settings.MEDIA_ROOT) / 'staff_qr'
        qr_dir.mkdir(parents=True, exist_ok=True)

        # Counters for reporting
        created_count = 0
        updated_count = 0
        error_count = 0
        total_rows = 0

        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, 1):
                total_rows += 1
                try:
                    # Extract data from CSV row
                    name = row.get('Name', '').strip()
                    booth_id = row.get('Booth ID', '').strip()
                    phone_no = row.get('Phone no', '').strip()
                    staff_code = row.get('Staff Code', '').strip()
                    location = row.get('Location', '').strip()
                    staff_type = row.get('Staff Type', '').strip()
                    
                    # Skip empty rows
                    if not name and not staff_code:
                        self.stdout.write(f'Skipping row {row_num}: No name or staff code')
                        continue
                    
                    # Validate required fields
                    if not staff_code:
                        self.stdout.write(self.style.WARNING(f'Row {row_num}: Missing staff code, skipping'))
                        error_count += 1
                        continue
                    
                    # Prepare location
                    if location in ['1p', '2p', '3p', '4p', 'O']:
                        location_value = location
                    else:
                        location_value = '1p'  # Default
                    
                    # Prepare staff type
                    if staff_type in ['VIP', 'Sales']:
                        staff_type_value = staff_type
                    else:
                        staff_type_value = 'VIP'  # Default
                    
                    # Clean phone number
                    if phone_no:
                        phone_no = ''.join(filter(str.isdigit, phone_no))
                    
                    # Create or update staff record
                    staff, created = Staff.objects.update_or_create(
                        staff_code=staff_code,
                        defaults={
                            'name': name if name else f'Staff {staff_code}',
                            'booth_id': booth_id if booth_id else None,
                            'phone_number': phone_no if phone_no else None,
                            'location': location_value,
                            'staff_type': staff_type_value,
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'[{row_num}] Created: {staff_code} - {name}'))
                        created_count += 1
                    else:
                        self.stdout.write(f'[{row_num}] Updated: {staff_code} - {name}')
                        updated_count += 1
                    
                    # Generate QR code
                    try:
                        qr_path = generate_qr(str(staff.id))
                        
                        if os.path.exists(qr_path):
                            with open(qr_path, 'rb') as f:
                                qr_filename = f'staff_{staff.staff_code}_qr.png'
                                staff.qr_code_image.save(qr_filename, File(f), save=True)
                            
                            self.stdout.write(f'  ✓ QR generated for {staff_code}')
                        else:
                            self.stdout.write(self.style.WARNING(f'  ✗ QR file not created for {staff_code}'))
                    
                    except Exception as qr_error:
                        self.stdout.write(self.style.WARNING(f'  ✗ QR generation failed for {staff_code}: {qr_error}'))
                        error_count += 1
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing row {row_num}: {str(e)}'))
                    error_count += 1
                    continue

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('IMPORT SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'Total rows in CSV: {total_rows}'))
        self.stdout.write(self.style.SUCCESS(f'Successfully created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Successfully updated: {updated_count}'))
        self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        
        if error_count > 0:
            self.stdout.write(self.style.WARNING('Some records had errors. Check the output above.'))