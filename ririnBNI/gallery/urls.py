from django.urls import path
from . import views

urlpatterns = [
    # API untuk nasabah
    path('api/nasabah/profil/', views.api_nasabah_profil),
    path('api/pinjaman/', views.api_nasabah_pinjaman),
    path('api/riwayat/', views.api_nasabah_riwayat),
    path('api/bayar/', views.api_nasabah_bayar),
    
    # API untuk administrator
    path('api/administrator/nasabah/', views.api_administrator_nasabah),
    path('api/administrator/all-extra-tables/', views.api_administrator_all_extra_tables),  # <-- API BARU
    path('api/administrator/pinjaman/', views.api_administrator_pinjaman),
    path('api/administrator/dashboard/', views.api_administrator_dashboard),
    path('api/administrator/nasabah/tambah/', views.api_administrator_tambah_nasabah),
    path('api/administrator/nasabah/ubah-role/', views.api_administrator_ubah_role),
    path('api/administrator/nasabah/tambah-lengkap/', views.api_administrator_tambah_nasabah_lengkap),
    path('api/administrator/nasabah/ubah-role/', views.api_administrator_ubah_role),
    path('api/administrator/nasabah/hapus/', views.api_administrator_hapus_nasabah),
    path('api/administrator/nasabah/update/', views.api_administrator_update_nasabah),  # <-- TAMBAHKAN INI
    # Tambahkan di dalam urlpatterns
    path('api/administrator/tipe-pinjaman-stats/', views.api_administrator_tipe_pinjaman_stats, name='api_tipe_pinjaman_stats'),
    path('api/administrator/nasabah/update-limit/', views.api_administrator_update_limit, name='update_limit'),
    
    # Halaman views
    path('', views.daftar_nasabah, name='daftar_nasabah'),
    path('data_nasabah/', views.daftar_nasabah, name='data_nasabah'),
    path('nasabah/login/', views.login_nasabah, name='login_nasabah'),
    path('nasabah/dashboard/', views.dashboard_nasabah, name='dashboard_nasabah'),
    path('administrator/login/', views.login_administrator, name='login_administrator'),
    path('administrator/dashboard/', views.dashboard_administrator, name='dashboard_administrator'),
]