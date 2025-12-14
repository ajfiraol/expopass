# Event Entrance (hidasegebeyaexpo theme)

Minimal Django project scaffolding for an event entrance system with QR scanning.

Quick start

1. Create a virtualenv and activate it

```powershell
cd event_entry
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Apply migrations and create a superuser

```powershell
python manage.py migrate
python manage.py createsuperuser
```

3. Run the dev server

```powershell
python manage.py runserver
```

4. Admin: `/admin/` — create `Ticket` entries and generate QR images with `entrance.utils.generate_qr(ticket_id)` or via a small script.

Notes

- Media is served at `/media/` during DEBUG mode.
- The scanner page uses `html5-qrcode` CDN and redirects to `/verify/<ticket_id>` on scan.
