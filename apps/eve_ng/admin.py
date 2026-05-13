from django.contrib import admin
from .models import EveNgLab, EveNgDevice, EveNgLabExecution

def register_admin():
    @admin.register(EveNgLab)
    class EveNgLabAdmin(admin.ModelAdmin):
        list_display = ['name', 'lab_path', 'is_active']
        list_filter = ['is_active']

    @admin.register(EveNgDevice)
    class EveNgDeviceAdmin(admin.ModelAdmin):
        list_display = ['lab', 'name', 'node_id', 'olt']
        raw_id_fields = ['lab', 'olt', 'vendor', 'device_type']

    @admin.register(EveNgLabExecution)
    class EveNgLabExecutionAdmin(admin.ModelAdmin):
        list_display = ['lab', 'started_at', 'status']
        list_filter = ['status']
