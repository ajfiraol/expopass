from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.utils import timezone
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.core.files import File
from .models import Staff, Pass
from .utils import generate_qr
import os



def home(request):
    return render(request, 'home.html')


def admin_redirect(request):
    return redirect('dashboard')





@login_required
def dashboard(request):
    booth_filter = request.GET.get('booth_id', '')
    location_filter = request.GET.get('location', '')
    status_filter = request.GET.get('status', 'all')

    staff_list = Staff.objects.all()
    if booth_filter:
        staff_list = staff_list.filter(booth_id__icontains=booth_filter)
    if location_filter:
        staff_list = staff_list.filter(location=location_filter)

    # Filter by printed status
    if status_filter == 'printed':
        staff_list = staff_list.filter(printed=True)
    elif status_filter == 'not_printed':
        staff_list = staff_list.filter(printed=False)

    # Annotate if any pass is printed
    for staff in staff_list:
        staff.any_printed = staff.passes.filter(printed=True).exists()

    context = {
        'staff_list': staff_list,
        'booth_filter': booth_filter,
        'location_filter': location_filter,
        'status_filter': status_filter,
        'total_count': Staff.objects.count(),
        'printed_count': Staff.objects.filter(printed=True).count(),
        'not_printed_count': Staff.objects.filter(printed=False).count(),
    }
    return render(request, 'dashboard.html', context)


@require_POST
def save_printed(request):
    """
    Saves printed (checkbox) state per Staff.
    Only checked staff will be marked as printed=True.
    Unchecked staff will be printed=False.
    """

    # IDs of checked staff from the form
    checked_ids = request.POST.getlist('printed_staff')

    # Reset all to False first
    Staff.objects.update(printed=False)

    # Set checked staff to True
    if checked_ids:
        Staff.objects.filter(id__in=checked_ids).update(printed=True)

    return redirect('dashboard')


@require_POST
def toggle_printed(request, staff_id):
    """
    Toggle the 'printed' flag for a single Staff instance.
    Used by the dashboard checkbox via AJAX.
    """
    staff = get_object_or_404(Staff, id=staff_id)
    staff.printed = not staff.printed
    staff.save(update_fields=['printed'])
    return JsonResponse({'success': True, 'printed': staff.printed})


@login_required
def edit_staff(request, staff_id):
    """
    Edit a single staff/booth, and adjust the number of staff entries for that booth.
    New staff entries get auto-generated UUIDs and QR codes like the import command.
    """
    staff = get_object_or_404(Staff, id=staff_id)

    # All staff that share this booth_id AND location (booth group)
    booth_qs = Staff.objects.filter(booth_id=staff.booth_id, location=staff.location)
    current_count = booth_qs.count()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip() or staff.name
        phone = request.POST.get('phone_number', '').strip() or staff.phone_number
        booth_id = request.POST.get('booth_id', '').strip() or None
        location = request.POST.get('location', staff.location)
        staff_type = request.POST.get('staff_type', staff.staff_type)
        try:
            desired_count = int(request.POST.get('staff_count', current_count))
        except ValueError:
            desired_count = current_count

        # Update all staff in this booth+location group with new shared details
        booth_qs.update(
            name=name,
            phone_number=phone,
            booth_id=booth_id,
            location=location,
            staff_type=staff_type,
        )

        # Refresh instance from DB (values just updated)
        staff.refresh_from_db()

        # Ensure it has a QR code (using staff_code, which scan expects)
        if not staff.qr_code_image:
            qr_path = generate_qr(staff.staff_code)
            with open(qr_path, 'rb') as f:
                staff.qr_code_image.save(
                    f'staff_{staff.staff_code}.png',
                    File(f),
                    save=True
                )

        # Refresh booth queryset if booth_id or location changed
        booth_qs = Staff.objects.filter(booth_id=staff.booth_id, location=staff.location)
        current_count = booth_qs.count()

        # Increase: create extra staff records with same booth details
        if desired_count > current_count:
            to_create = desired_count - current_count
            for _ in range(to_create):
                new_staff = Staff.objects.create(
                    name=name,
                    phone_number=phone,
                    booth_id=staff.booth_id,
                    location=location,
                    staff_type=staff_type,
                )
                qr_path = generate_qr(new_staff.staff_code)
                with open(qr_path, 'rb') as f:
                    new_staff.qr_code_image.save(
                        f'staff_{new_staff.staff_code}.png',
                        File(f),
                        save=True
                    )

        # Decrease: delete extra staff (excluding the current one first)
        elif desired_count < current_count:
            to_delete = current_count - desired_count
            others = booth_qs.exclude(id=staff.id)[:to_delete]
            # If still need to delete more and we excluded current, delete including current queryset slice
            remaining = to_delete - others.count()
            if remaining > 0:
                more = booth_qs.exclude(id__in=[s.id for s in others])[:remaining]
                to_remove_ids = list(others.values_list('id', flat=True)) + list(more.values_list('id', flat=True))
            else:
                to_remove_ids = list(others.values_list('id', flat=True))
            if to_remove_ids:
                Staff.objects.filter(id__in=to_remove_ids).delete()

        return redirect('dashboard')

    # GET: render simple form
    context = {
        'staff': staff,
        'current_count': current_count,
    }
    return render(request, 'edit_staff.html', context)

def download_qr(request, staff_id):
    import os
    from django.http import FileResponse
    staff = get_object_or_404(Staff, id=staff_id)
    if not staff.qr_code_image:
        return JsonResponse({'error': 'No QR'})
    path = staff.qr_code_image.path
    return FileResponse(open(path, 'rb'), as_attachment=True, filename=os.path.basename(path))

def scan_qr(request):
    return render(request, 'scan.html')


def verify_staff(request, staff_code):
    """
    QR contains ONLY staff_code (e.g. 2PS110)
    """
    # staff_code in our QR is currently the UUID string (primary key)
    staff = get_object_or_404(Staff, id=staff_code)

    return render(request, 'pass.html', {
        'staff': staff
    })


# Use Django's built-in auth views for login/logout, wired in urls.py
