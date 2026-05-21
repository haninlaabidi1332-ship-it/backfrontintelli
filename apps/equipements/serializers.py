# apps/equipements/serializers.py
from rest_framework import serializers
from django.core.validators import ValidationError
from .models import (
    Vendor, Gouvernorat, Delegation, Site, Rack, DeviceType,
    OLT, Board, NetworkInterface, IPAddress, VLAN, GponPort,
    Splitter, SplitterPort, Customer, ONT, OpticalPath,
    FiberCable, FiberCore, FibreLink, PowerSupply, FanModule,
    ConfigurationBackup, EquipmentHistory
)
from apps.users.serializers import UserMinimalSerializer


# ============================================================================
# VENDOR
# ============================================================================

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'code', 'website', 'support_email', 'support_phone', 'logo_url']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# GOUVERNORAT & DÉLÉGATION
# ============================================================================

class GouvernoratSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gouvernorat
        fields = ['id', 'code', 'nom']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DelegationSerializer(serializers.ModelSerializer):
    gouvernorat_nom = serializers.CharField(source='gouvernorat.nom', read_only=True)

    class Meta:
        model = Delegation
        fields = ['id', 'code', 'nom', 'gouvernorat', 'gouvernorat_nom']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# SITE
# ============================================================================

class SiteSerializer(serializers.ModelSerializer):
    gouvernorat_nom = serializers.CharField(source='gouvernorat.nom', read_only=True)
    delegation_nom = serializers.CharField(source='delegation.nom', read_only=True)

    class Meta:
        model = Site
        fields = [
            'id', 'name', 'code', 'address', 'city', 'code_postal',
            'gouvernorat', 'gouvernorat_nom', 'delegation', 'delegation_nom',
            'contact_name', 'contact_phone', 'latitude', 'longitude'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# RACK
# ============================================================================

class RackSerializer(serializers.ModelSerializer):
    site_code = serializers.CharField(source='site.code', read_only=True)

    class Meta:
        model = Rack
        fields = ['id', 'site', 'site_code', 'name', 'code', 'total_units', 'room', 'row', 'position']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# DEVICE TYPE
# ============================================================================

class DeviceTypeSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_code = serializers.CharField(source='vendor.code', read_only=True)

    class Meta:
        model = DeviceType
        fields = [
            'id', 'vendor', 'vendor_name', 'vendor_code', 'model', 'device_class',
            'part_number', 'u_height', 'power_consumption_w', 'description'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# OLT
# ============================================================================

class OLTListSerializer(serializers.ModelSerializer):
    vendor_name    = serializers.CharField(source='vendor.name', read_only=True)
    site_name      = serializers.CharField(source='site.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # Annotated in OLTViewSet.get_queryset() — count of online ONTs for this OLT
    ont_count      = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = OLT
        fields = [
            'id', 'hostname', 'ip_address', 'vendor_name', 'site_name',
            'status', 'status_display', 'snmp_version', 'max_pon_ports',
            'last_polled_at', 'ont_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']


class OLTDetailSerializer(serializers.ModelSerializer):
    vendor_detail = VendorSerializer(source='vendor', read_only=True)
    device_type_detail = DeviceTypeSerializer(source='device_type', read_only=True)
    site_detail = SiteSerializer(source='site', read_only=True)
    rack_detail = RackSerializer(source='rack', read_only=True)
    gouvernorat_detail = GouvernoratSerializer(source='gouvernorat', read_only=True)
    delegation_detail = DelegationSerializer(source='delegation', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OLT
        fields = [
            'id', 'hostname', 'ip_address', 'management_ip',
            'snmp_community', 'snmp_version', 'snmp_port',
            'snmp_v3_username', 'snmp_v3_auth_key', 'snmp_v3_priv_key',
            'snmp_v3_auth_protocol', 'snmp_v3_priv_protocol',
            'vendor', 'vendor_detail', 'device_type', 'device_type_detail',
            'serial_number', 'firmware_version', 'hardware_version',
            'asset_tag', 'purchase_date', 'warranty_end', 'end_of_support', 'maintenance_contract',
            'site', 'site_detail', 'rack', 'rack_detail', 'rack_unit',
            'address', 'city', 'region', 'code_postal',
            'gouvernorat', 'gouvernorat_detail', 'delegation', 'delegation_detail',
            'latitude', 'longitude',
            'max_pon_ports', 'max_onts_per_port',
            'status', 'status_display', 'last_polled_at', 'uptime_seconds', 'description',
            'created_by', 'created_by_detail', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']


class OLTCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OLT
        fields = [
            'hostname', 'ip_address', 'management_ip',
            'snmp_community', 'snmp_version', 'snmp_port',
            'snmp_v3_username', 'snmp_v3_auth_key', 'snmp_v3_priv_key',
            'snmp_v3_auth_protocol', 'snmp_v3_priv_protocol',
            'vendor', 'device_type', 'serial_number', 'firmware_version', 'hardware_version',
            'asset_tag', 'purchase_date', 'warranty_end', 'end_of_support', 'maintenance_contract',
            'site', 'rack', 'rack_unit',
            'address', 'city', 'region', 'code_postal',
            'gouvernorat', 'delegation', 'latitude', 'longitude',
            'max_pon_ports', 'max_onts_per_port',
            'status', 'description'
        ]


# ============================================================================
# BOARD
# ============================================================================

class BoardSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)
    board_type_display = serializers.CharField(source='get_board_type_display', read_only=True)

    class Meta:
        model = Board
        fields = [
            'id', 'olt', 'olt_hostname', 'slot_number', 'board_type', 'board_type_display',
            'model', 'serial_number', 'status', 'firmware_version'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# NETWORK INTERFACE
# ============================================================================

class NetworkInterfaceSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)
    board_slot = serializers.CharField(source='board.slot_number', read_only=True)
    interface_type_display = serializers.CharField(source='get_interface_type_display', read_only=True)

    class Meta:
        model = NetworkInterface
        fields = [
            'id', 'olt', 'olt_hostname', 'board', 'board_slot', 'name', 'interface_type',
            'interface_type_display', 'admin_status', 'oper_status', 'mac_address',
            'speed_mbps', 'mtu', 'description'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# IP ADDRESS
# ============================================================================

class IPAddressSerializer(serializers.ModelSerializer):
    interface_name = serializers.CharField(source='interface.name', read_only=True)
    olt_hostname = serializers.CharField(source='interface.olt.hostname', read_only=True)

    class Meta:
        model = IPAddress
        fields = [
            'id', 'interface', 'interface_name', 'olt_hostname', 'ip_address',
            'subnet_mask', 'gateway', 'is_primary', 'vrf'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# VLAN
# ============================================================================

class VLNSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = VLAN
        fields = ['id', 'vlan_id', 'name', 'description', 'site', 'site_name']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# GPON PORT
# ============================================================================

class GponPortSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)

    class Meta:
        model = GponPort
        fields = [
            'id', 'olt', 'olt_hostname', 'port_index', 'port_name', 'enabled',
            'ont_count', 'rx_power_min_dbm', 'rx_power_max_dbm'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']


# ============================================================================
# SPLITTER
# ============================================================================

class SplitterSerializer(serializers.ModelSerializer):
    site_code = serializers.CharField(source='site.code', read_only=True)
    rack_code = serializers.CharField(source='rack.code', read_only=True)

    class Meta:
        model = Splitter
        fields = [
            'id', 'site', 'site_code', 'name', 'ratio', 'level',
            'latitude', 'longitude', 'rack', 'rack_code'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# SPLITTER PORT
# ============================================================================

class SplitterPortSerializer(serializers.ModelSerializer):
    splitter_name = serializers.CharField(source='splitter.name', read_only=True)
    direction_display = serializers.SerializerMethodField()

    class Meta:
        model = SplitterPort
        fields = [
            'id', 'splitter', 'splitter_name', 'port_number', 'direction',
            'direction_display', 'is_used', 'connected_ont'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_direction_display(self, obj):
        return dict(SplitterPort.DIRECTION_CHOICES).get(obj.direction, '')


# ============================================================================
# CUSTOMER
# ============================================================================

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'customer_id', 'full_name', 'email', 'phone', 'address']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# ONT
# ============================================================================

class ONTListSerializer(serializers.ModelSerializer):
    olt_hostname        = serializers.CharField(source='olt.hostname', read_only=True)
    gpon_port_name      = serializers.CharField(source='gpon_port.port_name', read_only=True)
    customer_id_display = serializers.CharField(source='customer.customer_id', read_only=True)
    status_display      = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ONT
        fields = [
            'id', 'serial_number', 'mac_address', 'ip_address',
            'olt_hostname', 'gpon_port_name', 'ont_index',
            'status', 'status_display',
            'rx_power', 'tx_power', 'distance_km',
            'service_type', 'last_seen_at',
            'customer_id_display',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']


class ONTDetailSerializer(serializers.ModelSerializer):
    olt_detail = OLTListSerializer(source='olt', read_only=True)
    gpon_port_detail = GponPortSerializer(source='gpon_port', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    customer_detail = CustomerSerializer(source='customer', read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ONT
        fields = [
            'id', 'serial_number', 'mac_address', 'ip_address',
            'olt', 'olt_detail', 'gpon_port', 'gpon_port_detail', 'ont_index',
            'rx_power', 'tx_power', 'distance_km', 'attenuation_db',
            'vendor', 'vendor_name', 'model', 'firmware_version',
            'status', 'status_display', 'last_seen_at',
            'customer', 'customer_detail', 'service_type',
            'address', 'city', 'latitude', 'longitude',
            'created_by', 'created_by_detail', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']


class ONTCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ONT
        fields = [
            'serial_number', 'mac_address', 'ip_address', 'olt', 'gpon_port', 'ont_index',
            'rx_power', 'tx_power', 'distance_km', 'attenuation_db',
            'vendor', 'model', 'firmware_version',
            'status', 'customer', 'service_type', 'address', 'city', 'latitude', 'longitude'
        ]


# ============================================================================
# OPTICAL PATH
# ============================================================================

class OpticalPathSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)
    splitter_name = serializers.CharField(source='splitter.name', read_only=True)
    ont_serial = serializers.CharField(source='ont.serial_number', read_only=True)

    class Meta:
        model = OpticalPath
        fields = [
            'id', 'olt', 'olt_hostname', 'splitter', 'splitter_name',
            'ont', 'ont_serial', 'fiber_length_km', 'total_loss_db', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# FIBER CABLE
# ============================================================================

class FiberCableSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiberCable
        fields = ['id', 'name', 'fiber_count', 'length_km', 'cable_type']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# FIBER CORE
# ============================================================================

class FiberCoreSerializer(serializers.ModelSerializer):
    cable_name = serializers.CharField(source='cable.name', read_only=True)
    connected_to_info = serializers.SerializerMethodField()

    class Meta:
        model = FiberCore
        fields = ['id', 'cable', 'cable_name', 'core_number', 'connected_to', 'connected_to_info']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_connected_to_info(self, obj):
        if obj.connected_to:
            return f"{obj.connected_to.cable.name} - Brin {obj.connected_to.core_number}"
        return None


# ============================================================================
# FIBRE LINK (inter-OLT)
# ============================================================================

class FibreLinkSerializer(serializers.ModelSerializer):
    olt_a_hostname = serializers.CharField(source='interface_a.olt.hostname', read_only=True)
    interface_a_name = serializers.CharField(source='interface_a.name', read_only=True)
    olt_b_hostname = serializers.CharField(source='interface_b.olt.hostname', read_only=True)
    interface_b_name = serializers.CharField(source='interface_b.name', read_only=True)
    link_type_display = serializers.CharField(source='get_link_type_display', read_only=True)

    class Meta:
        model = FibreLink
        fields = [
            'id', 'name', 'interface_a', 'olt_a_hostname', 'interface_a_name',
            'interface_b', 'olt_b_hostname', 'interface_b_name',
            'link_type', 'link_type_display', 'bandwidth_mbps', 'utilization_pct',
            'attenuation_db', 'length_km', 'is_active', 'last_updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']


# ============================================================================
# POWER SUPPLY
# ============================================================================

class PowerSupplySerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)

    class Meta:
        model = PowerSupply
        fields = ['id', 'olt', 'olt_hostname', 'slot', 'status', 'power_watts']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# FAN MODULE
# ============================================================================

class FanModuleSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)

    class Meta:
        model = FanModule
        fields = ['id', 'olt', 'olt_hostname', 'name', 'speed_rpm', 'status']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# CONFIGURATION BACKUP
# ============================================================================

class ConfigurationBackupSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)

    class Meta:
        model = ConfigurationBackup
        fields = ['id', 'olt', 'olt_hostname', 'filename', 'config_text', 'backup_date']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# EQUIPMENT HISTORY
# ============================================================================

class EquipmentHistorySerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)

    class Meta:
        model = EquipmentHistory
        fields = [
            'id', 'olt', 'olt_hostname', 'field_name', 'old_value', 'new_value',
            'changed_by', 'changed_by_name', 'change_date'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']