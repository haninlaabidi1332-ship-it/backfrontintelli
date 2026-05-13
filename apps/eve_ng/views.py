from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, CanManageLab
from apps.core.responses import success_response, error_response
from .models import EveNgLab, EveNgDevice, EveNgLabExecution
from .serializers import EveNgLabSerializer, EveNgDeviceSerializer, EveNgLabExecutionSerializer
from .tasks import start_lab_async, stop_lab_async, sync_device_config

class EveNgLabViewSet(viewsets.ModelViewSet):
    queryset = EveNgLab.objects.all()
    serializer_class = EveNgLabSerializer
    permission_classes = [IsAuthenticated, CanManageLab]
    pagination_class = StandardPagination

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        lab = self.get_object()
        start_lab_async.delay(lab.id)
        return success_response(None, f"Lab {lab.name} démarré en arrière-plan")

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        lab = self.get_object()
        stop_lab_async.delay(lab.id)
        return success_response(None, f"Lab {lab.name} arrêté en arrière-plan")

    @action(detail=True, methods=['get'], url_path='status')
    def status(self, request, pk=None):
        lab = self.get_object()
        # On peut récupérer l'exécution en cours
        exec_obj = lab.executions.filter(status='running').first()
        return success_response({
            'running': exec_obj is not None,
            'execution_id': exec_obj.id if exec_obj else None,
            'last_started': lab.last_started_at,
            'last_stopped': lab.last_stopped_at
        }, "Statut du lab")

class EveNgDeviceViewSet(viewsets.ModelViewSet):
    queryset = EveNgDevice.objects.select_related('lab', 'olt', 'vendor', 'device_type')
    serializer_class = EveNgDeviceSerializer
    permission_classes = [IsAuthenticated, CanManageLab]

    @action(detail=True, methods=['post'], url_path='sync')
    def sync(self, request, pk=None):
        device = self.get_object()
        sync_device_config.delay(device.id)
        return success_response(None, f"Synchronisation de {device.name} déclenchée")
