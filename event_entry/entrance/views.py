from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.utils import timezone
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.core.files import File
from django.conf import settings
from pathlib import Path
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
    sold_filter = request.GET.get('sold', 'all')

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

    # Filter by sold status
    if sold_filter == 'sold':
        staff_list = staff_list.filter(sold=True)
    elif sold_filter == 'not_sold':
        staff_list = staff_list.filter(sold=False)

    # Annotate if any pass is printed
    for staff in staff_list:
        staff.any_printed = staff.passes.filter(printed=True).exists()

    context = {
        'staff_list': staff_list,
        'booth_filter': booth_filter,
        'location_filter': location_filter,
        'status_filter': status_filter,
        'sold_filter': sold_filter,
        'total_count': Staff.objects.count(),
        'printed_count': Staff.objects.filter(printed=True).count(),
        'not_printed_count': Staff.objects.filter(printed=False).count(),
        'sold_count': Staff.objects.filter(sold=True).count(),
        'not_sold_count': Staff.objects.filter(sold=False).count(),
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
    # Descriptive download name without altering QR content
    # Example: STAFF_2Pav02_AuiXMVA.png
    prefix = (staff.staff_type or 'STAFF').upper()
    booth = (staff.booth_id or 'NoBooth').replace(' ', '_')
    location = (staff.location or 'NoLoc').replace(' ', '_')
    short_id = str(staff.id).replace('-', '')[:8]
    download_name = f"{prefix}_{booth}_{location}_{short_id}.png"
    return FileResponse(open(path, 'rb'), as_attachment=True, filename=download_name)

def scan_qr(request):
    return render(request, 'scan.html')


def verify_staff(request, staff_code):
    """
    QR contains ONLY staff_code (e.g. 2PS110)
    """
    import uuid
    # staff_code in our QR is currently the UUID string (primary key)
    try:
        uuid.UUID(str(staff_code))
    except ValueError:
        return render(request, 'pass.html', {'error': 'Invalid QR'})

    try:
        staff = Staff.objects.get(id=staff_code)
    except Staff.DoesNotExist:
        return render(request, 'pass.html', {'error': 'Staff not found'})

    return render(request, 'pass.html', {'staff': staff})


def verify_pass(request, pass_id):
    """
    Verify a pass by scanning its QR code (pass ID).
    Shows pass info with photo if available.
    """
    from datetime import timedelta
    import uuid
    
    # Support payloads like "pass_id|booth|location"
    if '|' in pass_id:
        pass_id = pass_id.split('|', 1)[0]

    # Validate UUID format early; if invalid, show error
    try:
        uuid.UUID(str(pass_id))
    except ValueError:
        return render(request, 'pass.html', {
            'error': 'Invalid QR'
        })

    try:
        pass_obj = Pass.objects.get(id=pass_id)
    except Pass.DoesNotExist:
        return render(request, 'pass.html', {
            'error': 'Pass not found'
        })
    
    # Check if photo is older than 12 hours and delete it
    if pass_obj.photo_taken_at:
        time_diff = timezone.now() - pass_obj.photo_taken_at
        if time_diff > timedelta(hours=12):
            # Delete photo after 12 hours
            if pass_obj.photo:
                pass_obj.photo.delete()
                pass_obj.photo = None
                pass_obj.photo_taken_at = None
                pass_obj.save()

    return render(request, 'pass.html', {
        'pass_obj': pass_obj,
        'staff': pass_obj.staff
    })


# Use Django's built-in auth views for login/logout, wired in urls.py


@login_required
def booth_files(request):
    """
    Show the folder structure created by export_booth_qr:
    BOOTH_QR_EXPORT_ROOT / <location> / <booth_id> / files
    Interactive file browser with expand/collapse, add/delete staff.
    """
    base_dir = Path(getattr(settings, "BOOTH_QR_EXPORT_ROOT", settings.BASE_DIR / "booth_qr_export"))
    locations = []

    # Get unique locations and booths from database (more reliable than filesystem)
    location_set = set(Staff.objects.values_list('location', flat=True).distinct())
    
    for loc_code in sorted(location_set):
        if not loc_code:
            continue
        loc_display = dict(Staff.LOCATION_CHOICES).get(loc_code, loc_code)
        booths = []
        booth_set = set(Staff.objects.filter(location=loc_code).values_list('booth_id', flat=True).distinct())
        
        for booth_id in sorted(booth_set):
            if not booth_id:
                continue
            qs = Staff.objects.filter(location=loc_code, booth_id=booth_id)
            staff_count = qs.count()
            printed_count = qs.filter(printed=True).count()
            sold_count = qs.filter(sold=True).count()
            photo_count = qs.exclude(photo__isnull=True).exclude(photo='').count()
            booths.append({
                "name": booth_id,
                "staff_count": staff_count,
                "printed_count": printed_count,
                "sold_count": sold_count,
                "photo_count": photo_count,
            })
        
        if booths:
            locations.append({
                "code": loc_code,
                "name": loc_display,
                "booths": booths,
            })

    context = {
        "base_dir": str(base_dir),
        "locations": locations,
    }
    return render(request, "booth_files.html", context)


@login_required
def booth_staff_list(request, location, booth_id):
    """
    AJAX endpoint: Get all staff for a specific booth+location combo.
    """
    staff_list = Staff.objects.filter(location=location, booth_id=booth_id).order_by('name')
    data = []
    for staff in staff_list:
        data.append({
            'id': str(staff.id),
            'name': staff.name,
            'phone': staff.phone_number,
            'staff_type': staff.staff_type,
            'staff_code': staff.staff_code,
            'printed': staff.printed,
            'sold': staff.sold,
            'qr_url': staff.qr_code_image.url if staff.qr_code_image else None,
            'photo_url': staff.photo.url if staff.photo else None,
        })
    return JsonResponse({'staff': data})


@login_required
@require_POST
def booth_add_staff(request, location, booth_id):
    """
    AJAX endpoint: Add a new staff member to a booth+location.
    """
    name = request.POST.get('name', '').strip() or 'Unknown'
    phone = request.POST.get('phone_number', '').strip() or 'N/A'
    staff_type = request.POST.get('staff_type', 'Staff').strip()

    if staff_type not in ['VIP', 'Staff']:
        staff_type = 'Staff'

    new_staff = Staff.objects.create(
        name=name,
        phone_number=phone,
        booth_id=booth_id,
        location=location,
        staff_type=staff_type,
    )

    # Generate QR code
    qr_path = generate_qr(new_staff.staff_code)
    with open(qr_path, 'rb') as f:
        new_staff.qr_code_image.save(
            f'staff_{new_staff.staff_code}.png',
            File(f),
            save=True
        )

    return JsonResponse({
        'success': True,
        'staff': {
            'id': str(new_staff.id),
            'name': new_staff.name,
            'phone': new_staff.phone_number,
            'staff_type': new_staff.staff_type,
            'staff_code': new_staff.staff_code,
            'qr_url': new_staff.qr_code_image.url if new_staff.qr_code_image else None,
        }
    })


@login_required
@require_POST
def booth_delete_staff(request, staff_id):
    """
    AJAX endpoint: Delete a staff member.
    """
    staff = get_object_or_404(Staff, id=staff_id)
    location = staff.location
    booth_id = staff.booth_id
    staff.delete()
    return JsonResponse({
        'success': True,
        'location': location,
        'booth_id': booth_id,
    })


@login_required
def create_pass_page(request):
    """
    Admin page to create a pass by scanning staff QR and capturing photo.
    """
    return render(request, 'create_pass.html')


@login_required
def get_staff_info(request, staff_code):
    """
    API endpoint: Get staff info by staff_code (for pass creation).
    """
    import uuid
    try:
        uuid.UUID(str(staff_code))
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid QR'})

    try:
        staff = Staff.objects.get(id=staff_code)
        return JsonResponse({
            'success': True,
            'staff': {
                'id': str(staff.id),
                'name': staff.name,
                'phone_number': staff.phone_number,
                'staff_type': staff.staff_type,
                'booth_id': staff.booth_id,
                'location_display': staff.get_location_display(),
            }
        })
    except Staff.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Staff not found'})


@login_required
@require_POST
def create_pass(request):
    """
    Create a pass with captured photo. Photo auto-deletes after 12 hours.
    """
    import base64
    from django.core.files.base import ContentFile
    from datetime import timedelta
    
    staff_id = request.POST.get('staff_id')
    full_name = request.POST.get('full_name', '').strip()
    phone_number = request.POST.get('phone_number', '').strip()
    photo_data = request.POST.get('photo_data', '')
    
    if not staff_id or not full_name:
        return JsonResponse({'success': False, 'error': 'Missing required fields'})
    
    try:
        staff = Staff.objects.get(id=staff_id)
    except Staff.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Staff not found'})
    
    # Create Pass
    pass_obj = Pass.objects.create(
        staff=staff,
        full_name=full_name,
        phone_number=phone_number or staff.phone_number,
        booth_id=staff.booth_id or '',
        day_entered=timezone.now().date(),
        photo_taken_at=timezone.now(),
    )
    
    # Save photo from base64 data
    if photo_data:
        try:
            # Remove data URL prefix if present
            if ',' in photo_data:
                photo_data = photo_data.split(',')[1]
            
            image_data = base64.b64decode(photo_data)
            photo_file = ContentFile(image_data, name=f'pass_{pass_obj.id}.jpg')
            pass_obj.photo.save(photo_file.name, photo_file, save=True)
        except Exception as e:
            print(f"Error saving photo: {e}")
            # Continue without photo if there's an error
    
    # Generate QR code for the pass (encode pass_id + booth + location)
    from .utils import generate_qr
    qr_payload = f"{pass_obj.id}|{staff.booth_id or ''}|{staff.location or ''}"
    qr_path = generate_qr(qr_payload)
    with open(qr_path, 'rb') as f:
        # Include booth and location in the stored filename for clarity
        booth_safe = (staff.booth_id or "no_booth").replace(" ", "_")
        location_safe = (staff.location or "loc").replace(" ", "_")
        pass_obj.qr_code_image.save(
            f'pass_{pass_obj.id}_{booth_safe}_{location_safe}.png',
            File(f),
            save=True
        )
    
    return JsonResponse({'success': True, 'pass_id': str(pass_obj.id)})


@login_required
@require_POST
def upload_staff_photo(request, staff_id):
    """
    Upload a photo for a staff member. Accepts both file upload and base64 data (from camera).
    """
    import base64
    from django.core.files.base import ContentFile
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        staff = get_object_or_404(Staff, id=staff_id)
        
        # Check if photo is provided as base64 (from camera) or file upload
        photo_data = request.POST.get('photo_data', '')
        photo_file = request.FILES.get('photo', None)
        
        if photo_data:
            # Handle base64 photo data from camera
            try:
                # Remove data URL prefix if present
                if ',' in photo_data:
                    photo_data = photo_data.split(',')[1]
                
                if not photo_data or len(photo_data) < 100:
                    return JsonResponse({'success': False, 'error': 'Invalid photo data provided'})
                
                image_data = base64.b64decode(photo_data)
                
                if not image_data or len(image_data) < 1000:
                    return JsonResponse({'success': False, 'error': 'Photo data too small or invalid'})
                
                # Delete old photo if exists
                if staff.photo:
                    staff.photo.delete(save=False)
                
                photo_file = ContentFile(image_data, name=f'staff_{staff.id}.jpg')
                staff.photo.save(photo_file.name, photo_file, save=True)
                
                logger.info(f'Photo uploaded successfully for staff {staff.id}')
                
                return JsonResponse({
                    'success': True,
                    'photo_url': staff.photo.url
                })
            except base64.binascii.Error as e:
                logger.error(f'Base64 decode error: {str(e)}')
                return JsonResponse({'success': False, 'error': f'Invalid photo format: {str(e)}'})
            except Exception as e:
                logger.error(f'Error processing photo: {str(e)}', exc_info=True)
                return JsonResponse({'success': False, 'error': f'Error processing photo: {str(e)}'})
        
        elif photo_file:
            # Handle file upload
            try:
                # Delete old photo if exists
                if staff.photo:
                    staff.photo.delete(save=False)
                
                staff.photo.save(photo_file.name, photo_file, save=True)
                
                logger.info(f'Photo uploaded successfully for staff {staff.id}')
                
                return JsonResponse({
                    'success': True,
                    'photo_url': staff.photo.url
                })
            except Exception as e:
                logger.error(f'Error saving photo file: {str(e)}', exc_info=True)
                return JsonResponse({'success': False, 'error': f'Error saving photo: {str(e)}'})
        
        return JsonResponse({'success': False, 'error': 'No photo provided'})
    
    except Exception as e:
        logger.error(f'Unexpected error in upload_staff_photo: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
