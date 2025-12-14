from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils import timezone
def admin_redirect(request):
    return redirect('dashboard')
from .models import Pass, Staff
@login_required
def dashboard(request):
    passes = Pass.objects.all().order_by('-created_at')[:20]
    staff = Staff.objects.all()
    return render(request, 'dashboard.html', {'passes': passes, 'staff': staff})
def home(request):
    return render(request, 'home.html')
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse


def pass_detail(request, pass_id):
    p = get_object_or_404(Pass, id=pass_id)
    return render(request, 'pass.html', {'pass_obj': p, 'staff': p.staff})
def scan_qr(request):
    return render(request, 'scan.html')

def verify_pass(request, pass_id):
    """
    pass_id here is actually STAFF ID (from QR)
    """
    staff = get_object_or_404(Staff, id=pass_id)

    today = timezone.now().date()

    # Find today's pass for this staff
    p = get_object_or_404(
        Pass,
        staff=staff,
        day_entered=today
    )

    return redirect('pass', pass_id=p.id)
