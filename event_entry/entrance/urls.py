from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', views.admin_redirect, name='admin-redirect'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('save-printed/', views.save_printed, name='save_printed'),
    path('toggle-printed/<uuid:staff_id>/', views.toggle_printed, name='toggle_printed'),
    path('staff/<uuid:staff_id>/edit/', views.edit_staff, name='edit_staff'),
    path('download-qr/<uuid:staff_id>/', views.download_qr, name='download_qr'),
    path('scan/', views.scan_qr, name='scan'),
    path('verify/<str:staff_code>/', views.verify_staff, name='verify'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
] 
