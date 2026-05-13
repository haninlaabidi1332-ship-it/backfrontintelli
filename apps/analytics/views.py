from datetime import timedelta
from django.db.models import Avg, Sum, Count
from django.utils import timezone
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsSupervisor, IsOperator
from apps.core.responses import success_response, error_response
from .models import KPIHistory, Report, DashboardWidget
from .serializers import KPIHistorySerializer, ReportSerializer, DashboardWidgetSerializer
from .filters import KPIHistoryFilter
from .tasks import generate_report, aggregate_kpi

class KPIViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KPIHistory.objects.select_related('olt')
    serializer_class = KPIHistorySerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = KPIHistoryFilter

    @extend_schema(summary="KPIs temps réel (dernière agrégation horaire)")
    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        cache_key = f"analytics:kpi:current"
        data = cache.get(cache_key)
        if not data:
            latest = KPIHistory.objects.filter(period='hour').order_by('-timestamp').first()
            if not latest:
                return error_response("Aucune donnée KPI", status_code=404)
            data = KPIHistorySerializer(latest).data
            cache.set(cache_key, data, 300)  # 5 minutes
        return success_response(data, "KPIs actuels")

    @extend_schema(summary="Tendance sur N jours")
    @action(detail=False, methods=['get'], url_path='trend')
    def trend(self, request):
        days = int(request.query_params.get('days', 7))
        metric = request.query_params.get('metric', 'online_onts')
        since = timezone.now() - timedelta(days=days)
        qs = KPIHistory.objects.filter(period='day', timestamp__gte=since).order_by('timestamp')
        data = {
            'labels': [k.timestamp.strftime('%Y-%m-%d') for k in qs],
            'values': [getattr(k, metric, 0) for k in qs],
            'metric': metric
        }
        return success_response(data, f"Tendance {metric} sur {days} jours")

    @extend_schema(summary="Forcer l'agrégation manuelle des KPIs")
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsSupervisor])
    def force_aggregate(self, request):
        period = request.data.get('period', 'hour')
        aggregate_kpi.delay(period)
        return success_response(None, f"Agrégation {period} déclenchée")

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related('generated_by')
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination

    def perform_create(self, serializer):
        report = serializer.save(generated_by=self.request.user, status='pending')
        generate_report.delay(report.id)

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        report = self.get_object()
        if report.status != 'ready' or not report.file:
            return error_response("Rapport non disponible", status_code=404)
        from django.http import FileResponse
        response = FileResponse(report.file, as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{report.file.name}"'
        return response

class DashboardWidgetViewSet(viewsets.ModelViewSet):
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DashboardWidget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request):
        widget_ids = request.data.get('widget_ids', [])
        for idx, wid in enumerate(widget_ids):
            DashboardWidget.objects.filter(id=wid, user=request.user).update(order=idx)
        return success_response(None, "Ordre mis à jour")