from django.contrib import admin
from .models import EquipmentUpload


@admin.register(EquipmentUpload)
class EquipmentUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'filename', 'created_at')
    readonly_fields = ('filename', 'created_at', 'summary', 'data')
