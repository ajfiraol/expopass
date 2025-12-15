from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Staff, Pass
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Pass
import os
from django.views.decorators.csrf import csrf_exempt


def home(request):
    return render(request, 'home.html')


def admin_redirect(request):
    return redirect('dashboard')





def dashboard(request):
    booth_filter = request.GET.get('booth_id', '')
    location_filter = request.GET.get('location', '')

    staff_list = Staff.objects.all()
    if booth_filter:
        staff_list = staff_list.filter(booth_id__icontains=booth_filter)
    if location_filter:
        staff_list = staff_list.filter(location=location_filter)

    # Annotate if any pass is printed
    for staff in staff_list:
        staff.any_printed = staff.passes.filter(printed=True).exists()

    context = {
        'staff_list': staff_list,
        'booth_filter': booth_filter,
        'location_filter': location_filter
    }
    return render(request, 'dashboard.html', context)

@csrf_exempt  # for simplicity
def toggle_printed(request, staff_id):
    if request.method == 'POST':
        staff = get_object_or_404(Staff, id=staff_id)
        passes = staff.passes.all()
        # Determine new status: if any printed, we uncheck; otherwise check all
        new_status = not passes.filter(printed=True).exists()
        passes.update(printed=new_status)  # update DB
        return JsonResponse({'printed': new_status})
    return JsonResponse({'error': 'Invalid request'}, status=400)

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
    staff = get_object_or_404(Staff, staff_code=staff_code)

    return render(request, 'pass.html', {
        'staff': staff
    })
