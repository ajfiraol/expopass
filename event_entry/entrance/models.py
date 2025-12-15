from django.db import models
import uuid
from django.utils import timezone

class Staff(models.Model):
    STAFF_TYPE_CHOICES = [
        ('VIP', 'VIP (Owner)'),
        ('Sales', 'Sales Staff'),
    ]
    LOCATION_CHOICES = [
        ('1p', 'Pavilion 1'),
        ('2p', 'Pavilion 2'),
        ('3p', 'Pavilion 3'),
        ('4p', 'Pavilion 4'),
        ('O', 'Outdoor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    booth_id = models.CharField(max_length=20, blank=True, null=True)
    staff_code = models.CharField(max_length=20, unique=True, db_index=True)
    staff_type = models.CharField(max_length=10, choices=STAFF_TYPE_CHOICES, default='VIP')
    location = models.CharField(max_length=10, choices=LOCATION_CHOICES, default='1p')
    qr_code_image = models.ImageField(upload_to='staff_qr/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['booth_id']

    def __str__(self):
        return f"{self.staff_code} - {self.name or 'Unnamed'}"

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

    def __str__(self):
        return f"{self.full_name} | {self.staff.staff_code} | {self.day_entered}"
