from datetime import timedelta
from django.db.models import Count, Avg
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsSupervisor, IsOperator, CanViewAnomaly, CanManageMLModel
from apps.core.responses import success_response, error_response

from .models import MLModel, AnomalyDetection, Prediction, TrainingJob, InferenceLog
from .serializers import (
    MLModelSerializer, AnomalyDetectionSerializer, PredictionSerializer,
    TrainingJobSerializer, InferenceLogSerializer
)
from .filters import AnomalyDetectionFilter
from .tasks import train_model, detect_anomalies_for_olt, predict_metric


class MLModelViewSet(viewsets.ModelViewSet):
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
    permission_classes = [IsAuthenticated, CanManageMLModel]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'], url_path='train')
    def train(self, request, pk=None):
        model = self.get_object()
        data_start = request.data.get('data_start')
        data_end = request.data.get('data_end')
        if not data_start or not data_end:
            return error_response("data_start et data_end sont requis", status_code=400)
        train_model.delay(model.id, data_start, data_end)
        return success_response(None, f"Entraînement du modèle {model.name} déclenché")

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        model = self.get_object()
        # Désactiver les autres modèles du même type si nécessaire
        MLModel.objects.filter(model_type=model.model_type, is_active=True).update(is_active=False)
        model.is_active = True
        model.save()
        return success_response({'is_active': True}, f"Modèle {model.name} activé")

    @action(detail=False, methods=['get'], url_path='active')
    def active_model(self, request):
        model_type = request.query_params.get('type')
        if model_type:
            model = MLModel.objects.filter(model_type=model_type, is_active=True).first()
        else:
            model = MLModel.objects.filter(is_active=True).first()
        if model:
            serializer = MLModelSerializer(model)
            return success_response(serializer.data, "Modèle actif récupéré")
        return error_response("Aucun modèle actif trouvé", status_code=404)


class AnomalyDetectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnomalyDetection.objects.select_related('olt', 'ont', 'interface', 'oid', 'model')
    serializer_class = AnomalyDetectionSerializer
    permission_classes = [IsAuthenticated, CanViewAnomaly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AnomalyDetectionFilter
    ordering = ['-detected_at']

    @action(detail=False, methods=['post'], url_path='run')
    def run_detection(self, request):
        olt_id = request.data.get('olt')
        if not olt_id:
            return error_response("Paramètre 'olt' requis", status_code=400)
        detect_anomalies_for_olt.delay(olt_id)
        return success_response(None, f"Détection d'anomalies déclenchée pour l'OLT {olt_id}")

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        anomaly = self.get_object()
        anomaly.resolved = True
        anomaly.resolved_at = timezone.now()
        anomaly.save()
        return success_response(None, "Anomalie marquée comme résolue")


class PredictionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Prediction.objects.select_related('olt', 'ont', 'model')
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['olt', 'metric_name']
    ordering = ['-prediction_time']

    @action(detail=False, methods=['post'], url_path='forecast')
    def forecast(self, request):
        olt_id = request.data.get('olt')
        metric_name = request.data.get('metric_name')
        horizon_hours = int(request.data.get('horizon_hours', 24))
        if not olt_id or not metric_name:
            return error_response("olt et metric_name requis", status_code=400)
        predict_metric.delay(olt_id, metric_name, horizon_hours)
        return success_response(None, f"Prédiction déclenchée pour {metric_name}")


class TrainingJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingJob.objects.select_related('model')
    serializer_class = TrainingJobSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    ordering = ['-started_at']


class InferenceLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InferenceLog.objects.select_related('model')
    serializer_class = InferenceLogSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    ordering = ['-timestamp']
