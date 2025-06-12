from django.urls import path
from Inventoryapp import views

urlpatterns = [

    # URL for user login page
    path('', views.login_view, name='login'),

    # URL for main menu/dashboard page
    path('main/', views.main_view, name='main'),

    # URL for user registration page (currently not in use, backup for future)
    path('register/', views.register_view, name='register'),

    # URL for owner name input page
    path('owner/', views.owner_view, name='owner'),

    # URL for inventory capture page
    path('inventory/', views.inventory_view, name='inventory'),

    # URL to handle user logout
    path('logout/', views.logout_view, name='logout'),

    # Backup URL for downloading inventory data (used for testing)
    path('download_inventory/', views.DownloadInventory, name="download_inventory"),

    # Backup URL for downloading Excel file (used for testing)
    path('download_excel/', views.download_excel_view, name='download_excel'),

    # Backup URL to manually generate ASN number in NextupNumber table (used for testing)
    path('nextup/', views.nextup_number_view, name='nextup-number'),

    # Testing URL to download inventory as Excel with ASN logic
    path('download-inventory/', views.download_inventory_view, name='download-inventory'),

    # URL to generate ASN number and download inventory Excel (actual flow)
    path('generate-asn-download/', views.generate_asn_and_download, name='generate_asn_download'),
]
