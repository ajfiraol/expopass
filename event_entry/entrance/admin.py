from django.contrib import admin
from .models import Pass, Staff
from django.utils.html import format_html

@admin.register(Pass)
class PassAdmin(admin.ModelAdmin):
	list_display = ("full_name", "phone_number", "booth_id", "staff", "day_entered", "created_at", "qr_preview")
	readonly_fields = ("qr_preview",)

	def qr_preview(self, obj):
		if obj.qr_code_image:
			return format_html('<img src="{}" width="100" />', obj.qr_code_image.url)
		return "No QR"
	qr_preview.short_description = "QR Code"

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
	list_display = ("name", "phone_number", "qr_code_image")
