from datetime import timedelta
from django.db.models import Count, Avg
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsSupervisor, IsOperator, CanViewBFDSession, CanManageBFDSession
from apps.core.responses import success_response, error_response

from .models import BFDSession, BFDStateHistory, BFDPollingSchedule, BFDThresholdRule, BFDActiveAlert
from .serializers import (
    BFDSessionSerializer, BFDStateHistorySerializer, BFDPollingScheduleSerializer,
    BFDThresholdRuleSerializer, BFDActiveAlertSerializer
)
from .filters import BFDSessionFilter, BFDActiveAlertFilter
from .tasks import poll_bfd_session


class BFDSessionViewSet(viewsets.ModelViewSet):
    queryset = BFDSession.objects.select_related('link', 'olt', 'interface_a__olt', 'interface_b__olt')
    serializer_class = BFDSessionSerializer
    permission_classes = [IsAuthenticated, CanViewBFDSession]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BFDSessionFilter
    search_fields = ['name', 'peer_ip', 'description']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageBFDSession()]
        return [IsAuthenticated(), CanViewBFDSession()]

    @action(detail=True, methods=['post'], url_path='poll')
    def poll_now(self, request, pk=None):
        session = self.get_object()
        poll_bfd_session.delay(str(session.id))
        return success_response(None, f"Collecte BFD déclenchée pour {session.name}")

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        qs = self.get_queryset()
        total = qs.count()
        up = qs.filter(state='up').count()
        down = qs.filter(state='down').count()
        init = qs.filter(state='init').count()
        admin_down = qs.filter(state='admin_down').count()
        avg_flap = qs.aggregate(avg=Avg('flap_count'))['avg'] or 0
        data = {
            'total_sessions': total,
            'up': up,
            'down': down,
            'init': init,
            'admin_down': admin_down,
            'average_flap_count': round(avg_flap, 2),
        }
        return success_response(data, "Résumé BFD")


class BFDStateHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BFDStateHistory.objects.select_related('session')
    serializer_class = BFDStateHistorySerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ['-timestamp']
    filterset_fields = ['session', 'new_state', 'triggered_alert']


class BFDPollingScheduleViewSet(viewsets.ModelViewSet):
    queryset = BFDPollingSchedule.objects.select_related('olt')
    serializer_class = BFDPollingScheduleSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'olt']


class BFDThresholdRuleViewSet(viewsets.ModelViewSet):
    queryset = BFDThresholdRule.objects.all()
    serializer_class = BFDThresholdRuleSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated(), IsOperator()]
        return [IsAuthenticated(), IsSupervisor()]

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle(self, request, pk=None):
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save(update_fields=['is_active'])
        return success_response({'is_active': rule.is_active}, "Statut modifié")


class BFDActiveAlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BFDActiveAlert.objects.select_related('rule', 'session', 'acknowledged_by')
    serializer_class = BFDActiveAlertSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BFDActiveAlertFilter
    ordering = ['-first_seen']

    @action(detail=True, methods=['post'], url_path='acknowledge')
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        if alert.status != 'active':
            return error_response("Seules les alertes actives peuvent être acquittées.", status_code=400)
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return success_response(BFDActiveAlertSerializer(alert).data, "Alerte acquittée")
