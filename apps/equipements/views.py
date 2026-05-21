# apps/equipements/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from apps.core.permissions import (
    IsAdmin, IsSupervisor, IsOperator, IsViewer,
    CanViewOLT, CanManageOLT,
    CanViewONT, CanManageONT,
)
from apps.core.responses import success_response, created_response, error_response
from apps.core.pagination import StandardPagination
from apps.core.utils import get_client_ip
from apps.users.models import UserActivity

from .models import (
    Vendor, Gouvernorat, Delegation, Site, Rack, DeviceType,
    OLT, Board, NetworkInterface, IPAddress, VLAN, GponPort,
    Splitter, SplitterPort, Customer, ONT, OpticalPath,
    FiberCable, FiberCore, FibreLink, PowerSupply, FanModule,
    ConfigurationBackup, EquipmentHistory
)
from .serializers import (
    VendorSerializer, GouvernoratSerializer, DelegationSerializer,
    SiteSerializer, RackSerializer, DeviceTypeSerializer,
    OLTListSerializer, OLTDetailSerializer, OLTCreateUpdateSerializer,
    BoardSerializer, NetworkInterfaceSerializer, IPAddressSerializer,
    VLNSerializer, GponPortSerializer, SplitterSerializer,
    SplitterPortSerializer, CustomerSerializer,
    ONTListSerializer, ONTDetailSerializer, ONTCreateUpdateSerializer,
    OpticalPathSerializer, FiberCableSerializer, FiberCoreSerializer,
    FibreLinkSerializer, PowerSupplySerializer, FanModuleSerializer,
    ConfigurationBackupSerializer, EquipmentHistorySerializer
)
from .filters import (
    VendorFilter, GouvernoratFilter, DelegationFilter,
    SiteFilter, RackFilter, DeviceTypeFilter,
    OLTFilter, BoardFilter, NetworkInterfaceFilter,
    IPAddressFilter, VLANFilter, GponPortFilter,
    SplitterFilter, SplitterPortFilter, CustomerFilter,
    ONTFilter, OpticalPathFilter, FiberCableFilter,
    FiberCoreFilter, FibreLinkFilter, PowerSupplyFilter,
    FanModuleFilter, ConfigurationBackupFilter, EquipmentHistoryFilter
)


# ============================================================================
# MIXIN DE BASE POUR LES PERMISSIONS (héritage plus propre)
# ============================================================================

class BaseViewSet(viewsets.ModelViewSet):
    """ViewSet de base avec pagination et filtres"""
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]


class ReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet lecture seule"""
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]


# ============================================================================
# VENDOR
# ============================================================================

class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = VendorFilter
    search_fields = ['name', 'code']
    ordering = ['name']


# ============================================================================
# GOUVERNORAT & DÉLÉGATION
# ============================================================================

class GouvernoratViewSet(ReadOnlyViewSet):
    queryset = Gouvernorat.objects.all()
    serializer_class = GouvernoratSerializer
    permission_classes = [IsAuthenticated, IsViewer]
    filterset_class = GouvernoratFilter
    search_fields = ['nom', 'code']
    ordering = ['nom']


class DelegationViewSet(ReadOnlyViewSet):
    queryset = Delegation.objects.select_related('gouvernorat')
    serializer_class = DelegationSerializer
    permission_classes = [IsAuthenticated, IsViewer]
    filterset_class = DelegationFilter
    search_fields = ['nom', 'code']
    ordering = ['gouvernorat', 'nom']


# ============================================================================
# SITE
# ============================================================================

class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.select_related('gouvernorat', 'delegation')
    serializer_class = SiteSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SiteFilter
    search_fields = ['name', 'code', 'city']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated(), IsOperator()]

    def perform_create(self, serializer):
        serializer.save()
        self._log('create', serializer.instance)

    def perform_update(self, serializer):
        serializer.save()
        self._log('update', serializer.instance)

    def perform_destroy(self, instance):
        self._log('delete', instance)
        instance.delete()

    def _log(self, action, obj):
        UserActivity.objects.create(
            user=self.request.user,
            action=action,
            description=f"{action} site {obj.code} - {obj.name}",
            resource_type='site',
            resource_id=str(obj.id),
            resource_name=obj.name,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )


# ============================================================================
# RACK
# ============================================================================

class RackViewSet(viewsets.ModelViewSet):
    queryset = Rack.objects.select_related('site')
    serializer_class = RackSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RackFilter
    search_fields = ['name', 'code']
    ordering = ['site', 'name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated(), IsOperator()]

    def perform_create(self, serializer):
        serializer.save()
        self._log('create', serializer.instance)

    def perform_update(self, serializer):
        serializer.save()
        self._log('update', serializer.instance)

    def perform_destroy(self, instance):
        self._log('delete', instance)
        instance.delete()

    def _log(self, action, obj):
        UserActivity.objects.create(
            user=self.request.user,
            action=action,
            description=f"{action} rack {obj.code}",
            resource_type='rack',
            resource_id=str(obj.id),
            resource_name=obj.name,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )


# ============================================================================
# DEVICE TYPE
# ============================================================================

class DeviceTypeViewSet(viewsets.ModelViewSet):
    queryset = DeviceType.objects.select_related('vendor')
    serializer_class = DeviceTypeSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DeviceTypeFilter
    search_fields = ['model', 'part_number']
    ordering = ['vendor', 'model']

    def perform_create(self, serializer):
        serializer.save()
        self._log('create', serializer.instance)

    def perform_update(self, serializer):
        serializer.save()
        self._log('update', serializer.instance)

    def perform_destroy(self, instance):
        self._log('delete', instance)
        instance.delete()

    def _log(self, action, obj):
        UserActivity.objects.create(
            user=self.request.user,
            action=action,
            description=f"{action} device type {obj.model}",
            resource_type='device_type',
            resource_id=str(obj.id),
            resource_name=obj.model,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )


# ============================================================================
# OLT
# ============================================================================

class OLTViewSet(viewsets.ModelViewSet):
    queryset = OLT.objects.select_related(
        'vendor', 'device_type', 'site', 'rack', 'gouvernorat', 'delegation', 'created_by'
    ).annotate(ont_count=Count('onts', filter=Q(onts__status='online', onts__deleted_at__isnull=True)))
    permission_classes = [IsAuthenticated, CanViewOLT]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OLTFilter
    search_fields = ['hostname', 'ip_address', 'serial_number']
    ordering = ['hostname']

    def get_serializer_class(self):
        if self.action == 'list':
            return OLTListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return OLTCreateUpdateSerializer
        return OLTDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageOLT()]
        return [IsAuthenticated(), CanViewOLT()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        self._log('create', serializer.instance)

    def perform_update(self, serializer):
        serializer.save()
        self._log('update', serializer.instance)

    def perform_destroy(self, instance):
        self._log('delete', instance)
        instance.delete()

    def _log(self, action, obj):
        UserActivity.objects.create(
            user=self.request.user,
            action=action,
            description=f"{action} OLT {obj.hostname}",
            resource_type='olt',
            resource_id=str(obj.id),
            resource_name=obj.hostname,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Statistiques globales des OLT"""
        qs = self.get_queryset()
        total = qs.count()
        by_status = dict(qs.values_list('status').annotate(c=Count('id')))
        by_vendor = dict(qs.values_list('vendor__name').annotate(c=Count('id')))
        by_site = dict(qs.values_list('site__name').annotate(c=Count('id')))
        total_capacity = qs.aggregate(total=Sum('max_pon_ports'))['total'] or 0
        data = {
            'total_olts': total,
            'par_statut': by_status,
            'par_fabricant': by_vendor,
            'par_site': by_site,
            'total_ports_pon': total_capacity,
        }
        return success_response(data, "Statistiques OLT")


# ============================================================================
# BOARD
# ============================================================================

class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.select_related('olt')
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = BoardFilter
    ordering = ['olt', 'slot_number']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageOLT()]
        return [IsAuthenticated(), IsOperator()]

    def perform_create(self, serializer):
        serializer.save()
        self._log('create', serializer.instance)

    def perform_update(self, serializer):
        serializer.save()
        self._log('update', serializer.instance)

    def perform_destroy(self, instance):
        self._log('delete', instance)
        instance.delete()

    def _log(self, action, obj):
        UserActivity.objects.create(
            user=self.request.user,
            action=action,
            description=f"{action} board slot {obj.slot_number} on {obj.olt.hostname}",
            resource_type='board',
            resource_id=str(obj.id),
            resource_name=obj.model,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )


# ============================================================================
# NETWORK INTERFACE
# ============================================================================

class NetworkInterfaceViewSet(viewsets.ModelViewSet):
    queryset = NetworkInterface.objects.select_related('olt', 'board')
    serializer_class = NetworkInterfaceSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = NetworkInterfaceFilter
    search_fields = ['name']
    ordering = ['olt', 'name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageOLT()]
        return [IsAuthenticated(), IsOperator()]

    def perform_create(self, serializer):
        serializer.save()
        self._log('create', serializer.instance)

    def perform_update(self, serializer):
        serializer.save()
        self._log('update', serializer.instance)

    def perform_destroy(self, instance):
        self._log('delete', instance)
        instance.delete()

    def _log(self, action, obj):
        UserActivity.objects.create(
            user=self.request.user,
            action=action,
            description=f"{action} interface {obj.name} on {obj.olt.hostname}",
            resource_type='interface',
            resource_id=str(obj.id),
            resource_name=obj.name,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )


# ============================================================================
# IP ADDRESS
# ============================================================================

class IPAddressViewSet(viewsets.ModelViewSet):
    queryset = IPAddress.objects.select_related('interface__olt')
    serializer_class = IPAddressSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = IPAddressFilter
    ordering = ['interface', 'ip_address']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageOLT()]
        return [IsAuthenticated(), IsOperator()]


# ============================================================================
# VLAN
# ============================================================================

class VLANViewSet(viewsets.ModelViewSet):
    queryset = VLAN.objects.select_related('site').prefetch_related('interfaces')
    serializer_class = VLNSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = VLANFilter
    search_fields = ['name']
    ordering = ['vlan_id']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated(), IsOperator()]


# ============================================================================
# GPON PORT
# ============================================================================

class GponPortViewSet(viewsets.ModelViewSet):
    queryset = GponPort.objects.select_related('olt')
    serializer_class = GponPortSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = GponPortFilter
    ordering = ['olt', 'port_index']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageOLT()]
        return [IsAuthenticated(), IsOperator()]


# ============================================================================
# SPLITTER
# ============================================================================

class SplitterViewSet(viewsets.ModelViewSet):
    queryset = Splitter.objects.select_related('site', 'rack')
    serializer_class = SplitterSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = SplitterFilter
    search_fields = ['name']
    ordering = ['site', 'level', 'name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated(), IsOperator()]


# ============================================================================
# SPLITTER PORT
# ============================================================================

class SplitterPortViewSet(viewsets.ModelViewSet):
    queryset = SplitterPort.objects.select_related('splitter', 'connected_ont')
    serializer_class = SplitterPortSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = SplitterPortFilter
    ordering = ['splitter', 'port_number']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageONT()]
        return [IsAuthenticated(), IsOperator()]


# ============================================================================
# CUSTOMER
# ============================================================================

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = CustomerFilter
    search_fields = ['customer_id', 'full_name', 'email', 'phone']
    ordering = ['customer_id']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated(), IsOperator()]


# ============================================================================
# ONT
# ============================================================================

class ONTViewSet(viewsets.ModelViewSet):
    queryset = ONT.objects.select_related(
        'olt', 'gpon_port', 'vendor', 'customer', 'created_by'
    )
    permission_classes = [IsAuthenticated, CanViewONT]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ONTFilter
    search_fields = ['serial_number', 'mac_address', 'customer__full_name']
    ordering = ['-last_seen_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ONTListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ONTCreateUpdateSerializer
        return ONTDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageONT()]
        return [IsAuthenticated(), CanViewONT()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        self._log('create', serializer.instance)

    def perform_update(self, serializer):
        serializer.save()
        self._log('update', serializer.instance)

    def perform_destroy(self, instance):
        self._log('delete', instance)
        instance.delete()

    def _log(self, action, obj):
        UserActivity.objects.create(
            user=self.request.user,
            action=action,
            description=f"{action} ONT {obj.serial_number}",
            resource_type='ont',
            resource_id=str(obj.id),
            resource_name=obj.serial_number,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Statistiques des ONT"""
        qs = self.get_queryset()
        data = {
            'total': qs.count(),
            'en_ligne': qs.filter(status='online').count(),
            'hors_ligne': qs.filter(status='offline').count(),
            'degrades': qs.filter(status='degraded').count(),
            'los': qs.filter(status='los').count(),
            'par_service': dict(qs.values_list('service_type').annotate(c=Count('id'))),
            'par_olt': dict(qs.values_list('olt__hostname').annotate(c=Count('id'))),
        }
        return success_response(data, "Statistiques ONT")


# ============================================================================
# OPTICAL PATH
# ============================================================================

class OpticalPathViewSet(viewsets.ModelViewSet):
    queryset = OpticalPath.objects.select_related('olt', 'splitter', 'ont')
    serializer_class = OpticalPathSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = OpticalPathFilter
    ordering = ['olt', 'splitter']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageONT()]
        return [IsAuthenticated(), IsOperator()]


# ============================================================================
# FIBER CABLE
# ============================================================================

class FiberCableViewSet(viewsets.ModelViewSet):
    queryset = FiberCable.objects.all()
    serializer_class = FiberCableSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = FiberCableFilter
    search_fields = ['name']
    ordering = ['name']


# ============================================================================
# FIBER CORE
# ============================================================================

class FiberCoreViewSet(viewsets.ModelViewSet):
    queryset = FiberCore.objects.select_related('cable', 'connected_to')
    serializer_class = FiberCoreSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = FiberCoreFilter
    ordering = ['cable', 'core_number']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsSupervisor()]


# ============================================================================
# FIBRE LINK (inter-OLT)
# ============================================================================

class FibreLinkViewSet(viewsets.ModelViewSet):
    queryset = FibreLink.objects.select_related('interface_a__olt', 'interface_b__olt')
    serializer_class = FibreLinkSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = FibreLinkFilter
    search_fields = ['name']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageOLT()]
        return [IsAuthenticated(), IsOperator()]

    @action(detail=False, methods=['get'], url_path='congested')
    def congested(self, request):
        """Liens fibre avec utilisation > 80%"""
        qs = self.get_queryset().filter(utilization_pct__gt=80)
        serializer = self.get_serializer(qs, many=True)
        return success_response(serializer.data, f"{qs.count()} liens congestés")


# ============================================================================
# POWER SUPPLY
# ============================================================================

class PowerSupplyViewSet(viewsets.ModelViewSet):
    queryset = PowerSupply.objects.select_related('olt')
    serializer_class = PowerSupplySerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = PowerSupplyFilter
    ordering = ['olt', 'slot']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageOLT()]
        return [IsAuthenticated(), IsSupervisor()]


# ============================================================================
# FAN MODULE
# ============================================================================

class FanModuleViewSet(viewsets.ModelViewSet):
    queryset = FanModule.objects.select_related('olt')
    serializer_class = FanModuleSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = FanModuleFilter
    ordering = ['olt', 'name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageOLT()]
        return [IsAuthenticated(), IsSupervisor()]


# ============================================================================
# CONFIGURATION BACKUP
# ============================================================================

class ConfigurationBackupViewSet(viewsets.ModelViewSet):
    queryset = ConfigurationBackup.objects.select_related('olt')
    serializer_class = ConfigurationBackupSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ConfigurationBackupFilter
    ordering = ['-backup_date']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageOLT()]
        return [IsAuthenticated(), IsSupervisor()]


# ============================================================================
# EQUIPMENT HISTORY
# ============================================================================

class EquipmentHistoryViewSet(ReadOnlyViewSet):
    queryset = EquipmentHistory.objects.select_related('olt', 'changed_by')
    serializer_class = EquipmentHistorySerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_class = EquipmentHistoryFilter
    ordering = ['-change_date']