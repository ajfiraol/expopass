import qrcode
from django.conf import settings
from pathlib import Path

def generate_qr(ticket_id):
    qr = qrcode.make(str(ticket_id))
    qr_dir = Path(settings.MEDIA_ROOT)
    qr_dir.mkdir(parents=True, exist_ok=True)
    qr_path = qr_dir / f"qr_{ticket_id}.png"
    qr.save(qr_path)
    return qr_path
