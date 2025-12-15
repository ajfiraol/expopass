from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse

from .models import Staff, Pass


def home(request):
    return render(request, 'home.html')


def admin_redirect(request):
    return redirect('dashboard')


@login_required
def dashboard(request):
    passes = Pass.objects.all().order_by('-created_at')[:20]
    staff = Staff.objects.all()
    return render(request, 'dashboard.html', {
        'passes': passes,
        'staff': staff
    })


def scan_qr(request):
    return render(request, 'scan.html')


def verify_pass(request, staff_code):
    """
    QR CODE = staff_code (STABLE)
    """

    staff = get_object_or_404(Staff, staff_code=staff_code)

    today = timezone.now().date()

    # one pass per staff per day
    p = get_object_or_404(
        Pass,
        staff=staff,
        day_entered=today
    )

    return redirect('pass', pass_id=p.id)


def pass_detail(request, pass_id):
    p = get_object_or_404(Pass, id=pass_id)
    return render(request, 'pass.html', {
        'pass_obj': p,
        'staff': p.staff
    })
