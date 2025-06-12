from django.contrib import admin
from .models import InventoryCapture, UserMaster, NextupNumber, DownloadInventory
from .forms import UserMasterForm

# Show password as dots in admin
class UserMasterAdmin(admin.ModelAdmin):
    form = UserMasterForm

# Register all models
admin.site.register(InventoryCapture)
admin.site.register(UserMaster, UserMasterAdmin)
admin.site.register(NextupNumber)
admin.site.register(DownloadInventory)
