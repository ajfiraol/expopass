from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Staff


def home(request):
    return render(request, 'home.html')


def admin_redirect(request):
    return redirect('dashboard')


@login_required
def dashboard(request):
    staff = Staff.objects.all()
    return render(request, 'dashboard.html', {
        'staff': staff
    })


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
