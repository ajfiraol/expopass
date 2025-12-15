# entrance/utils.py
import qrcode
from pathlib import Path
from django.conf import settings


def generate_qr(staff_code: str) -> str:
    """
    Generate QR image using staff_code (STABLE)
    Returns absolute file path
    """

    qr_dir = Path(settings.MEDIA_ROOT) / 'staff_qr'
    qr_dir.mkdir(parents=True, exist_ok=True)

    file_path = qr_dir / f"staff_{staff_code}.png"

    # 🔒 DO NOT regenerate if already exists
    if file_path.exists():
        return str(file_path)

    qr = qrcode.make(staff_code)
    qr.save(file_path)

    return str(file_path)
