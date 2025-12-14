from django.db import models
import uuid


# New Staff model with QR code
class Staff(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    qr_code_image = models.ImageField(upload_to='staff_qr/', blank=True, null=True)

    def __str__(self):
        return self.name

class Pass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    booth_id = models.CharField(max_length=100)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='passes')
    day_entered = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - Booth: {self.booth_id} - Day: {self.day_entered}"
