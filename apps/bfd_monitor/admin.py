from django.contrib import admin
from .models import (
    BFDSession, BFDStateHistory, BFDPollingSchedule,
    BFDThresholdRule, BFDActiveAlert
)

def register_admin():
    @admin.register(BFDSession)
    class BFDSessionAdmin(admin.ModelAdmin):
        list_display = ['name', 'link', 'olt', 'state', 'is_up', 'loss_rate_pct', 'up_count', 'down_count']
        list_filter = ['state', 'is_enabled', 'is_monitored']
        search_fields = ['name', 'link__name', 'olt__hostname', 'peer_ip']
        raw_id_fields = ['link', 'olt', 'interface_a', 'interface_b']
        readonly_fields = ['last_update', 'uptime_seconds', 'last_state_change',
                           'up_count', 'down_count', 'flap_count', 'last_up_at', 'last_down_at']

    @admin.register(BFDStateHistory)
    class BFDStateHistoryAdmin(admin.ModelAdmin):
        list_display = ['session', 'previous_state', 'new_state', 'timestamp', 'triggered_alert']
        list_filter = ['previous_state', 'new_state', 'triggered_alert']
        raw_id_fields = ['session']
        date_hierarchy = 'timestamp'

    @admin.register(BFDPollingSchedule)
    class BFDPollingScheduleAdmin(admin.ModelAdmin):
        list_display = ['olt', 'poll_interval_seconds', 'is_active', 'last_polled_at']
        list_filter = ['is_active']
        raw_id_fields = ['olt']

    @admin.register(BFDThresholdRule)
    class BFDThresholdRuleAdmin(admin.ModelAdmin):
        list_display = ['name', 'metric', 'operator', 'threshold', 'severity', 'is_active']
        list_filter = ['metric', 'severity', 'is_active']

    @admin.register(BFDActiveAlert)
    class BFDActiveAlertAdmin(admin.ModelAdmin):
        list_display = ['rule', 'session', 'severity', 'status', 'first_seen']
        list_filter = ['severity', 'status']
        raw_id_fields = ['rule', 'session', 'acknowledged_by']
