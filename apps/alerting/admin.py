from django.contrib import admin
from .models import AlertRule, Alert, NotificationChannel, NotificationHistory

def register_admin():
    @admin.register(AlertRule)
    class AlertRuleAdmin(admin.ModelAdmin):
        list_display = ['name', 'source_type', 'is_active', 'cooldown_minutes']
        list_filter = ['source_type', 'is_active']

    @admin.register(Alert)
    class AlertAdmin(admin.ModelAdmin):
        list_display = ['severity', 'olt', 'ont', 'message_short', 'status', 'first_seen']
        list_filter = ['severity', 'status']
        raw_id_fields = ['olt', 'ont', 'rule', 'acknowledged_by']
        date_hierarchy = 'first_seen'
        def message_short(self, obj):
            return obj.message[:50]

    @admin.register(NotificationChannel)
    class NotificationChannelAdmin(admin.ModelAdmin):
        list_display = ['name', 'channel_type', 'is_active']

    @admin.register(NotificationHistory)
    class NotificationHistoryAdmin(admin.ModelAdmin):
        list_display = ['alert', 'channel', 'success', 'sent_at']
        list_filter = ['success']