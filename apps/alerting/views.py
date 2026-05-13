from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsSupervisor, IsOperator
from apps.core.responses import success_response, error_response
from .models import AlertRule, Alert, NotificationChannel
from .serializers import AlertRuleSerializer, AlertSerializer, NotificationChannelSerializer
from .filters import AlertFilter

class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save()
        return success_response({'is_active': rule.is_active}, "Règle activée/désactivée")

class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Alert.objects.select_related('olt', 'ont', 'rule', 'acknowledged_by')
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = AlertFilter
    ordering = ['-first_seen']

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        if alert.status != 'active':
            return error_response("Seules les alertes actives peuvent être acquittées", 400)
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return success_response(None, "Alerte acquittée")

    @action(detail=False, methods=['post'])
    def bulk_acknowledge(self, request):
        ids = request.data.get('ids', [])
        count = Alert.objects.filter(id__in=ids, status='active').update(
            status='acknowledged',
            acknowledged_by=request.user,
            acknowledged_at=timezone.now()
        )
        return success_response({'count': count}, f"{count} alertes acquittées")

class NotificationChannelViewSet(viewsets.ModelViewSet):
    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        channel = self.get_object()
        from .tasks import send_alert_notification
        send_alert_notification.delay(
            channel_id=channel.id,
            alert_id=None,
            message=f"[TEST] Ceci est un message de test d'IntelliOLT sur {channel.name}"
        )
        return success_response(None, "Test de notification envoyé")
