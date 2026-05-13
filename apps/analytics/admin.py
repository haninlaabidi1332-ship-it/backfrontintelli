from django.contrib import admin
from .models import KPIHistory, Report, DashboardWidget

def register_admin():
    @admin.register(KPIHistory)
    class KPIHistoryAdmin(admin.ModelAdmin):
        list_display = ['timestamp', 'period', 'total_olts', 'online_onts', 'avg_cpu_usage']
        list_filter = ['period']
        date_hierarchy = 'timestamp'

    @admin.register(Report)
    class ReportAdmin(admin.ModelAdmin):
        list_display = ['name', 'report_type', 'format', 'status', 'generated_at']
        list_filter = ['report_type', 'status', 'format']
        readonly_fields = ['generated_at', 'file']

    @admin.register(DashboardWidget)
    class DashboardWidgetAdmin(admin.ModelAdmin):
        list_display = ['name', 'user', 'widget_type', 'order']
        list_filter = ['widget_type']
