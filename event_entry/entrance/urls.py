from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', views.admin_redirect, name='admin-redirect'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('scan/', views.scan_qr, name='scan'),

    # 🔑 QR USES STAFF CODE
    path('verify/<str:staff_code>/', views.verify_pass, name='verify'),

    path('pass/<uuid:pass_id>/', views.pass_detail, name='pass'),
]
