from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', views.admin_redirect, name='admin-redirect'),
    path('create-pass/', views.create_pass_page, name='create_pass_page'),
    path('create-pass/submit/', views.create_pass, name='create_pass'),
    path('api/staff/<str:staff_code>/', views.get_staff_info, name='get_staff_info'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('booth-files/', views.booth_files, name='booth_files'),
    path('api/booth/<str:location>/<str:booth_id>/staff/', views.booth_staff_list, name='booth_staff_list'),
    path('api/booth/<str:location>/<str:booth_id>/add-staff/', views.booth_add_staff, name='booth_add_staff'),
    path('api/booth/delete-staff/<uuid:staff_id>/', views.booth_delete_staff, name='booth_delete_staff'),
    path('api/staff/<uuid:staff_id>/upload-photo/', views.upload_staff_photo, name='upload_staff_photo'),
     path('save-printed/', views.save_printed, name='save_printed'),
    path('toggle-printed/<uuid:staff_id>/', views.toggle_printed, name='toggle_printed'),
    path('staff/<uuid:staff_id>/edit/', views.edit_staff, name='edit_staff'),
    path('download-qr/<uuid:staff_id>/', views.download_qr, name='download_qr'),
    path('scan/', views.scan_qr, name='scan'),
    path('verify/<str:staff_code>/', views.verify_staff, name='verify'),
    path('verify-pass/<str:pass_id>/', views.verify_pass, name='verify_pass'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
]
