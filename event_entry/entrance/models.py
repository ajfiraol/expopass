from django.db import models
import uuid
from django.utils import timezone

class Staff(models.Model):
    STAFF_TYPES = (
        ('VIP', 'VIP'),
        ('Staff', 'Staff'),
    )

    LOCATION_CHOICES = (
        ('1p','Pavilion 1'),
        ('2p','Pavilion 2'),
        ('3p','Pavilion 3'),
        ('4p','Pavilion 4'),
        ('O','Outdoor'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, default='Unknown')
    phone_number = models.CharField(max_length=20, default='N/A')
    booth_id = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=2, choices=LOCATION_CHOICES)
    staff_type = models.CharField(max_length=10, choices=STAFF_TYPES)
    qr_code_image = models.ImageField(upload_to='staff_qr/', blank=True, null=True)
    printed = models.BooleanField(default=False)
    sold = models.BooleanField(default=False, help_text="Whether this booth/staff slot is sold (from Excel 'Sold' column).")
    staff_code_sheet = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text="Staff code from Excel/CSV (e.g. 1PV01, 1PS02)"
    )

    @property
    def staff_code(self) -> str:
        """
        Stable code used inside the QR. For now we use the UUID string,
        so anything that scans the QR can look up the staff by primary key.
        """
        return str(self.id)

    def __str__(self):
        return f"{self.name} ({self.staff_type})"

class Pass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='passes')
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    booth_id = models.CharField(max_length=100)
    day_entered = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    printed = models.BooleanField(default=False)  # Track printed status
    qr_code_image = models.ImageField(upload_to='pass_qr/', blank=True, null=True)
    photo = models.ImageField(upload_to='pass_photos/', blank=True, null=True)
    photo_taken_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} | {self.staff.staff_code} | {self.day_entered}"
