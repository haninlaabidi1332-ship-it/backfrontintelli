# apps/equipements/filters.py
import django_filters
from django_filters import rest_framework as filters
from .models import (
    Vendor, Gouvernorat, Delegation, Site, Rack, DeviceType,
    OLT, Board, NetworkInterface, IPAddress, VLAN, GponPort,
    Splitter, SplitterPort, Customer, ONT, OpticalPath,
    FiberCable, FiberCore, FibreLink, PowerSupply, FanModule,
    ConfigurationBackup, EquipmentHistory
)
from apps.users.models import User


# ============================================================================
# FABRICANT (Vendor)
# ============================================================================

class VendorFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    code = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Vendor
        fields = ['name', 'code']


# ============================================================================
# GOUVERNORAT & DÉLÉGATION
# ============================================================================

class GouvernoratFilter(filters.FilterSet):
    nom = filters.CharFilter(lookup_expr='icontains')
    code = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Gouvernorat
        fields = ['code', 'nom']


class DelegationFilter(filters.FilterSet):
    nom = filters.CharFilter(lookup_expr='icontains')
    gouvernorat = filters.ModelChoiceFilter(queryset=Gouvernorat.objects.all())

    class Meta:
        model = Delegation
        fields = ['gouvernorat', 'nom']


# ============================================================================
# SITE
# ============================================================================

class SiteFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    code = filters.CharFilter(lookup_expr='icontains')
    city = filters.CharFilter(lookup_expr='icontains')
    code_postal = filters.CharFilter(lookup_expr='icontains')
    gouvernorat = filters.ModelChoiceFilter(queryset=Gouvernorat.objects.all())
    delegation = filters.ModelChoiceFilter(queryset=Delegation.objects.all())
    has_gps = filters.BooleanFilter(method='filter_has_gps')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    def filter_has_gps(self, queryset, name, value):
        if value:
            return queryset.filter(latitude__isnull=False, longitude__isnull=False)
        return queryset.filter(latitude__isnull=True)

    class Meta:
        model = Site
        fields = ['name', 'code', 'city', 'code_postal', 'gouvernorat', 'delegation']


# ============================================================================
# BAIE (Rack)
# ============================================================================

class RackFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    code = filters.CharFilter(lookup_expr='icontains')
    site = filters.ModelChoiceFilter(queryset=Site.objects.all())
    total_units_min = filters.NumberFilter(field_name='total_units', lookup_expr='gte')
    total_units_max = filters.NumberFilter(field_name='total_units', lookup_expr='lte')

    class Meta:
        model = Rack
        fields = ['site', 'code']


# ============================================================================
# TYPE D'ÉQUIPEMENT (DeviceType)
# ============================================================================

class DeviceTypeFilter(filters.FilterSet):
    model = filters.CharFilter(lookup_expr='icontains')
    vendor = filters.ModelChoiceFilter(queryset=Vendor.objects.all())
    device_class = filters.ChoiceFilter(choices=DeviceType.DeviceClass.choices)
    u_height_min = filters.NumberFilter(field_name='u_height', lookup_expr='gte')
    u_height_max = filters.NumberFilter(field_name='u_height', lookup_expr='lte')

    class Meta:
        model = DeviceType
        fields = ['vendor', 'model', 'device_class']


# ============================================================================
# OLT
# ============================================================================

class OLTFilter(filters.FilterSet):
    hostname = filters.CharFilter(lookup_expr='icontains')
    ip_address = filters.CharFilter(lookup_expr='icontains')
    vendor = filters.ModelChoiceFilter(queryset=Vendor.objects.all())
    device_type = filters.ModelChoiceFilter(queryset=DeviceType.objects.all())
    site = filters.ModelChoiceFilter(queryset=Site.objects.all())
    rack = filters.ModelChoiceFilter(queryset=Rack.objects.all())
    gouvernorat = filters.ModelChoiceFilter(queryset=Gouvernorat.objects.all())
    delegation = filters.ModelChoiceFilter(queryset=Delegation.objects.all())
    status = filters.ChoiceFilter(choices=OLT.Status.choices)
    snmp_version = filters.ChoiceFilter(choices=OLT.SNMPVersion.choices)
    has_gps = filters.BooleanFilter(method='filter_has_gps')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    last_polled_after = filters.DateTimeFilter(field_name='last_polled_at', lookup_expr='gte')
    last_polled_before = filters.DateTimeFilter(field_name='last_polled_at', lookup_expr='lte')
    max_pon_ports_min = filters.NumberFilter(field_name='max_pon_ports', lookup_expr='gte')
    max_pon_ports_max = filters.NumberFilter(field_name='max_pon_ports', lookup_expr='lte')

    def filter_has_gps(self, queryset, name, value):
        if value:
            return queryset.filter(latitude__isnull=False, longitude__isnull=False)
        return queryset.filter(latitude__isnull=True)

    class Meta:
        model = OLT
        fields = [
            'hostname', 'ip_address', 'vendor', 'device_type', 'site', 'rack',
            'gouvernorat', 'delegation', 'status', 'snmp_version'
        ]


# ============================================================================
# CARTE (Board)
# ============================================================================

class BoardFilter(filters.FilterSet):
    olt = filters.ModelChoiceFilter(queryset=OLT.objects.all())
    board_type = filters.ChoiceFilter(choices=Board.BoardType.choices)
    status = filters.ChoiceFilter(choices=OLT.Status.choices)
    slot_number = filters.NumberFilter()

    class Meta:
        model = Board
        fields = ['olt', 'board_type', 'status', 'slot_number']


# ============================================================================
# INTERFACE RÉSEAU (NetworkInterface)
# ============================================================================

class NetworkInterfaceFilter(filters.FilterSet):
    olt = filters.ModelChoiceFilter(queryset=OLT.objects.all())
    board = filters.ModelChoiceFilter(queryset=Board.objects.all())
    name = filters.CharFilter(lookup_expr='icontains')
    interface_type = filters.ChoiceFilter(choices=NetworkInterface.InterfaceType.choices)
    admin_status = filters.BooleanFilter()
    oper_status = filters.BooleanFilter()
    speed_mbps_min = filters.NumberFilter(field_name='speed_mbps', lookup_expr='gte')
    speed_mbps_max = filters.NumberFilter(field_name='speed_mbps', lookup_expr='lte')
    has_mac = filters.BooleanFilter(method='filter_has_mac')

    def filter_has_mac(self, queryset, name, value):
        if value:
            return queryset.exclude(mac_address='')
        return queryset.filter(mac_address='')

    class Meta:
        model = NetworkInterface
        fields = ['olt', 'board', 'name', 'interface_type', 'admin_status', 'oper_status']


# ============================================================================
# ADRESSE IP
# ============================================================================

class IPAddressFilter(filters.FilterSet):
    interface = filters.ModelChoiceFilter(queryset=NetworkInterface.objects.all())
    ip_address = filters.CharFilter(lookup_expr='icontains')
    subnet_mask = filters.NumberFilter()
    is_primary = filters.BooleanFilter()
    vrf = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = IPAddress
        fields = ['interface', 'ip_address', 'is_primary', 'vrf']


# ============================================================================
# VLAN
# ============================================================================

class VLANFilter(filters.FilterSet):
    vlan_id = filters.NumberFilter()
    vlan_id_min = filters.NumberFilter(field_name='vlan_id', lookup_expr='gte')
    vlan_id_max = filters.NumberFilter(field_name='vlan_id', lookup_expr='lte')
    name = filters.CharFilter(lookup_expr='icontains')
    site = filters.ModelChoiceFilter(queryset=Site.objects.all())

    class Meta:
        model = VLAN
        fields = ['vlan_id', 'name', 'site']


# ============================================================================
# PORT GPON
# ============================================================================

class GponPortFilter(filters.FilterSet):
    olt = filters.ModelChoiceFilter(queryset=OLT.objects.all())
    port_index = filters.NumberFilter()
    enabled = filters.BooleanFilter()
    ont_count_min = filters.NumberFilter(field_name='ont_count', lookup_expr='gte')
    ont_count_max = filters.NumberFilter(field_name='ont_count', lookup_expr='lte')

    class Meta:
        model = GponPort
        fields = ['olt', 'port_index', 'enabled']


# ============================================================================
# SPLITTER (passif)
# ============================================================================

class SplitterFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    site = filters.ModelChoiceFilter(queryset=Site.objects.all())
    ratio = filters.CharFilter(lookup_expr='icontains')
    level = filters.NumberFilter()
    has_gps = filters.BooleanFilter(method='filter_has_gps')
    level_min = filters.NumberFilter(field_name='level', lookup_expr='gte')
    level_max = filters.NumberFilter(field_name='level', lookup_expr='lte')

    def filter_has_gps(self, queryset, name, value):
        if value:
            return queryset.filter(latitude__isnull=False, longitude__isnull=False)
        return queryset.filter(latitude__isnull=True)

    class Meta:
        model = Splitter
        fields = ['name', 'site', 'ratio', 'level']


# ============================================================================
# PORT DE SPLITTER
# ============================================================================

class SplitterPortFilter(filters.FilterSet):
    splitter = filters.ModelChoiceFilter(queryset=Splitter.objects.all())
    direction = filters.ChoiceFilter(choices=SplitterPort.DIRECTION_CHOICES)
    is_used = filters.BooleanFilter()
    connected_ont = filters.ModelChoiceFilter(queryset=ONT.objects.all())
    port_number = filters.NumberFilter()

    class Meta:
        model = SplitterPort
        fields = ['splitter', 'direction', 'is_used', 'connected_ont', 'port_number']


# ============================================================================
# CLIENT (Customer)
# ============================================================================

class CustomerFilter(filters.FilterSet):
    customer_id = filters.CharFilter(lookup_expr='icontains')
    full_name = filters.CharFilter(lookup_expr='icontains')
    email = filters.CharFilter(lookup_expr='icontains')
    phone = filters.CharFilter(lookup_expr='icontains')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Customer
        fields = ['customer_id', 'full_name', 'email']


# ============================================================================
# ONT
# ============================================================================

class ONTFilter(filters.FilterSet):
    serial_number = filters.CharFilter(lookup_expr='icontains')
    mac_address = filters.CharFilter(lookup_expr='icontains')
    olt = filters.ModelChoiceFilter(queryset=OLT.objects.all())
    gpon_port = filters.ModelChoiceFilter(queryset=GponPort.objects.all())
    status = filters.ChoiceFilter(choices=ONT.Status.choices)
    service_type = filters.ChoiceFilter(choices=ONT.ServiceType.choices)
    customer = filters.ModelChoiceFilter(queryset=Customer.objects.all())
    online = filters.BooleanFilter(method='filter_online')
    has_gps = filters.BooleanFilter(method='filter_has_gps')
    last_seen_after = filters.DateTimeFilter(field_name='last_seen_at', lookup_expr='gte')
    last_seen_before = filters.DateTimeFilter(field_name='last_seen_at', lookup_expr='lte')
    rx_power_min = filters.NumberFilter(field_name='rx_power', lookup_expr='gte')
    rx_power_max = filters.NumberFilter(field_name='rx_power', lookup_expr='lte')
    tx_power_min = filters.NumberFilter(field_name='tx_power', lookup_expr='gte')
    tx_power_max = filters.NumberFilter(field_name='tx_power', lookup_expr='lte')

    def filter_online(self, queryset, name, value):
        if value:
            return queryset.filter(status='online')
        return queryset.exclude(status='online')

    def filter_has_gps(self, queryset, name, value):
        if value:
            return queryset.filter(latitude__isnull=False, longitude__isnull=False)
        return queryset.filter(latitude__isnull=True)

    class Meta:
        model = ONT
        fields = [
            'serial_number', 'mac_address', 'olt', 'gpon_port', 'status',
            'service_type', 'customer', 'online'
        ]


# ============================================================================
# CHEMIN OPTIQUE (OpticalPath)
# ============================================================================

class OpticalPathFilter(filters.FilterSet):
    olt = filters.ModelChoiceFilter(queryset=OLT.objects.all())
    splitter = filters.ModelChoiceFilter(queryset=Splitter.objects.all())
    ont = filters.ModelChoiceFilter(queryset=ONT.objects.all())
    is_active = filters.BooleanFilter()
    fiber_length_min = filters.NumberFilter(field_name='fiber_length_km', lookup_expr='gte')
    fiber_length_max = filters.NumberFilter(field_name='fiber_length_km', lookup_expr='lte')
    total_loss_min = filters.NumberFilter(field_name='total_loss_db', lookup_expr='gte')
    total_loss_max = filters.NumberFilter(field_name='total_loss_db', lookup_expr='lte')

    class Meta:
        model = OpticalPath
        fields = ['olt', 'splitter', 'ont', 'is_active']


# ============================================================================
# CÂBLE FIBRE (FiberCable)
# ============================================================================

class FiberCableFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    cable_type = filters.ChoiceFilter(choices=FiberCable.CableType.choices)
    fiber_count_min = filters.NumberFilter(field_name='fiber_count', lookup_expr='gte')
    fiber_count_max = filters.NumberFilter(field_name='fiber_count', lookup_expr='lte')
    length_min = filters.NumberFilter(field_name='length_km', lookup_expr='gte')
    length_max = filters.NumberFilter(field_name='length_km', lookup_expr='lte')

    class Meta:
        model = FiberCable
        fields = ['name', 'cable_type']


# ============================================================================
# BRIN DE FIBRE (FiberCore)
# ============================================================================

class FiberCoreFilter(filters.FilterSet):
    cable = filters.ModelChoiceFilter(queryset=FiberCable.objects.all())
    core_number = filters.NumberFilter()
    connected_to = filters.ModelChoiceFilter(queryset=FiberCore.objects.all())

    class Meta:
        model = FiberCore
        fields = ['cable', 'core_number', 'connected_to']


# ============================================================================
# LIEN FIBRE (FibreLink) – inter-OLT
# ============================================================================

class FibreLinkFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    interface_a = filters.ModelChoiceFilter(queryset=NetworkInterface.objects.all())
    interface_b = filters.ModelChoiceFilter(queryset=NetworkInterface.objects.all())
    link_type = filters.ChoiceFilter(choices=FibreLink.LinkType.choices)
    is_active = filters.BooleanFilter()
    olt_a = filters.ModelChoiceFilter(field_name='interface_a__olt', queryset=OLT.objects.all())
    olt_b = filters.ModelChoiceFilter(field_name='interface_b__olt', queryset=OLT.objects.all())
    bandwidth_min = filters.NumberFilter(field_name='bandwidth_mbps', lookup_expr='gte')
    bandwidth_max = filters.NumberFilter(field_name='bandwidth_mbps', lookup_expr='lte')
    utilization_min = filters.NumberFilter(field_name='utilization_pct', lookup_expr='gte')
    utilization_max = filters.NumberFilter(field_name='utilization_pct', lookup_expr='lte')
    length_min = filters.NumberFilter(field_name='length_km', lookup_expr='gte')
    length_max = filters.NumberFilter(field_name='length_km', lookup_expr='lte')

    class Meta:
        model = FibreLink
        fields = ['name', 'link_type', 'is_active', 'olt_a', 'olt_b']


# ============================================================================
# ALIMENTATION (PowerSupply)
# ============================================================================

class PowerSupplyFilter(filters.FilterSet):
    olt = filters.ModelChoiceFilter(queryset=OLT.objects.all())
    status = filters.ChoiceFilter(choices=OLT.Status.choices)
    power_watts_min = filters.NumberFilter(field_name='power_watts', lookup_expr='gte')
    power_watts_max = filters.NumberFilter(field_name='power_watts', lookup_expr='lte')

    class Meta:
        model = PowerSupply
        fields = ['olt', 'status']


# ============================================================================
# MODULE DE VENTILATION (FanModule)
# ============================================================================

class FanModuleFilter(filters.FilterSet):
    olt = filters.ModelChoiceFilter(queryset=OLT.objects.all())
    status = filters.ChoiceFilter(choices=OLT.Status.choices)
    speed_rpm_min = filters.NumberFilter(field_name='speed_rpm', lookup_expr='gte')
    speed_rpm_max = filters.NumberFilter(field_name='speed_rpm', lookup_expr='lte')

    class Meta:
        model = FanModule
        fields = ['olt', 'status']


# ============================================================================
# SAUVEGARDE DE CONFIGURATION (ConfigurationBackup)
# ============================================================================

class ConfigurationBackupFilter(filters.FilterSet):
    olt = filters.ModelChoiceFilter(queryset=OLT.objects.all())
    filename = filters.CharFilter(lookup_expr='icontains')
    backup_date_after = filters.DateTimeFilter(field_name='backup_date', lookup_expr='gte')
    backup_date_before = filters.DateTimeFilter(field_name='backup_date', lookup_expr='lte')

    class Meta:
        model = ConfigurationBackup
        fields = ['olt', 'filename']


# ============================================================================
# HISTORIQUE DES ÉQUIPEMENTS (EquipmentHistory)
# ============================================================================

class EquipmentHistoryFilter(filters.FilterSet):
    olt = filters.ModelChoiceFilter(queryset=OLT.objects.all())
    field_name = filters.CharFilter(lookup_expr='icontains')
    changed_by = filters.ModelChoiceFilter(queryset=User.objects.all())
    change_date_after = filters.DateTimeFilter(field_name='change_date', lookup_expr='gte')
    change_date_before = filters.DateTimeFilter(field_name='change_date', lookup_expr='lte')

    class Meta:
        model = EquipmentHistory
        fields = ['olt', 'field_name', 'changed_by']