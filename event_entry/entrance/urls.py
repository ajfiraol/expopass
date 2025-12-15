from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', views.admin_redirect, name='admin-redirect'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('scan/', views.scan_qr, name='scan'),
    path('verify/<str:staff_code>/', views.verify_staff, name='verify'),
]
