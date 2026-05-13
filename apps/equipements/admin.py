# apps/equipements/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from .models import (
    Vendor, Gouvernorat, Delegation, Site, Rack, DeviceType,
    OLT, Board, NetworkInterface, IPAddress, VLAN, GponPort,
    Splitter, SplitterPort, Customer, ONT, OpticalPath,
    FiberCable, FiberCore, FibreLink, PowerSupply, FanModule,
    ConfigurationBackup, EquipmentHistory
)


# ============================================================================
# FABRICANT (Vendor)
# ============================================================================

@admin.register(Vendor)
class VendorAdmin(ImportExportModelAdmin):
    list_display = ['name', 'code', 'website', 'support_phone', 'support_email']
    search_fields = ['name', 'code']
    ordering = ['name']
    fieldsets = (
        ('Informations générales', {'fields': ('name', 'code', 'website')}),
        ('Support', {'fields': ('support_email', 'support_phone', 'logo_url')}),
    )


# ============================================================================
# GOUVERNORAT & DÉLÉGATION
# ============================================================================

@admin.register(Gouvernorat)
class GouvernoratAdmin(ImportExportModelAdmin):
    list_display = ['code', 'nom']
    search_fields = ['code', 'nom']
    ordering = ['nom']


@admin.register(Delegation)
class DelegationAdmin(ImportExportModelAdmin):
    list_display = ['nom', 'gouvernorat', 'code']
    list_filter = ['gouvernorat']
    search_fields = ['nom', 'code']
    ordering = ['gouvernorat', 'nom']


# ============================================================================
# SITE
# ============================================================================

@admin.register(Site)
class SiteAdmin(ImportExportModelAdmin):
    list_display = ['code', 'name', 'city', 'gouvernorat', 'contact_name']
    list_filter = ['gouvernorat', 'delegation']
    search_fields = ['name', 'code', 'city', 'address']
    raw_id_fields = ['gouvernorat', 'delegation']
    fieldsets = (
        ('Identité', {'fields': ('name', 'code', 'address', 'city', 'code_postal')}),
        ('Localisation administrative', {'fields': ('gouvernorat', 'delegation')}),
        ('Coordonnées GPS', {'fields': ('latitude', 'longitude')}),
        ('Contact', {'fields': ('contact_name', 'contact_phone')}),
    )


# ============================================================================
# BAIE (Rack)
# ============================================================================

@admin.register(Rack)
class RackAdmin(ImportExportModelAdmin):
    list_display = ['code', 'name', 'site', 'total_units']
    list_filter = ['site']
    search_fields = ['name', 'code']
    raw_id_fields = ['site']
    fieldsets = (
        ('Identification', {'fields': ('code', 'name', 'site')}),
        ('Dimensions', {'fields': ('total_units', 'room', 'row', 'position')}),
    )


# ============================================================================
# TYPE D'ÉQUIPEMENT (DeviceType)
# ============================================================================

@admin.register(DeviceType)
class DeviceTypeAdmin(ImportExportModelAdmin):
    list_display = ['model', 'vendor', 'device_class', 'u_height']
    list_filter = ['vendor', 'device_class']
    search_fields = ['model', 'part_number']
    raw_id_fields = ['vendor']
    fieldsets = (
        ('Modèle', {'fields': ('vendor', 'model', 'device_class', 'part_number')}),
        ('Caractéristiques', {'fields': ('u_height', 'power_consumption_w', 'description')}),
    )


# ============================================================================
# OLT
# ============================================================================

@admin.register(OLT)
class OLTAdmin(ImportExportModelAdmin):
    list_display = ['hostname', 'ip_address', 'vendor', 'site', 'status', 'last_polled_at']
    list_filter = ['vendor', 'site', 'status', 'snmp_version']
    search_fields = ['hostname', 'ip_address', 'serial_number']
    raw_id_fields = ['vendor', 'device_type', 'site', 'rack', 'gouvernorat', 'delegation', 'created_by']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    fieldsets = (
        ('Identification', {'fields': ('hostname', 'ip_address', 'management_ip', 'serial_number')}),
        ('SNMP', {'fields': ('snmp_version', 'snmp_community', 'snmp_port',
                             'snmp_v3_username', 'snmp_v3_auth_key', 'snmp_v3_priv_key',
                             'snmp_v3_auth_protocol', 'snmp_v3_priv_protocol')}),
        ('Matériel', {'fields': ('vendor', 'device_type', 'firmware_version', 'hardware_version')}),
        ('Cycle de vie', {'fields': ('asset_tag', 'purchase_date', 'warranty_end', 'end_of_support', 'maintenance_contract')}),
        ('Localisation', {'fields': ('site', 'rack', 'rack_unit', 'address', 'city', 'region', 'code_postal',
                                     'gouvernorat', 'delegation', 'latitude', 'longitude')}),
        ('Capacité', {'fields': ('max_pon_ports', 'max_onts_per_port')}),
        ('État', {'fields': ('status', 'last_polled_at', 'uptime_seconds', 'description')}),
        ('Métadonnées', {'fields': ('created_by', 'created_at', 'updated_at', 'deleted_at'), 'classes': ('collapse',)}),
    )


# ============================================================================
# CARTE (Board)
# ============================================================================

@admin.register(Board)
class BoardAdmin(ImportExportModelAdmin):
    list_display = ['olt', 'slot_number', 'board_type', 'model', 'status']
    list_filter = ['board_type', 'status', 'olt']
    search_fields = ['model', 'serial_number']
    raw_id_fields = ['olt']
    fieldsets = (
        ('Carte', {'fields': ('olt', 'slot_number', 'board_type', 'model', 'serial_number')}),
        ('État', {'fields': ('status', 'firmware_version')}),
    )


# ============================================================================
# INTERFACE RÉSEAU
# ============================================================================

@admin.register(NetworkInterface)
class NetworkInterfaceAdmin(ImportExportModelAdmin):
    list_display = ['name', 'olt', 'interface_type', 'admin_status', 'oper_status']
    list_filter = ['interface_type', 'admin_status', 'oper_status']
    search_fields = ['name', 'mac_address', 'description']
    raw_id_fields = ['olt', 'board']
    fieldsets = (
        ('Interface', {'fields': ('olt', 'board', 'name', 'interface_type', 'description')}),
        ('Statut', {'fields': ('admin_status', 'oper_status', 'mac_address', 'speed_mbps', 'mtu')}),
    )


# ============================================================================
# ADRESSE IP
# ============================================================================

@admin.register(IPAddress)
class IPAddressAdmin(ImportExportModelAdmin):
    list_display = ['ip_address', 'subnet_mask', 'interface', 'is_primary']
    list_filter = ['is_primary', 'vrf']
    search_fields = ['ip_address', 'gateway']
    raw_id_fields = ['interface']
    fieldsets = (
        ('Adresse', {'fields': ('interface', 'ip_address', 'subnet_mask', 'gateway')}),
        ('Attributs', {'fields': ('is_primary', 'vrf')}),
    )


# ============================================================================
# VLAN
# ============================================================================

@admin.register(VLAN)
class VLANAdmin(ImportExportModelAdmin):
    list_display = ['vlan_id', 'name', 'site']
    list_filter = ['site']
    search_fields = ['vlan_id', 'name', 'description']
    raw_id_fields = ['site']
    filter_horizontal = ['interfaces']
    fieldsets = (
        ('VLAN', {'fields': ('vlan_id', 'name', 'description', 'site')}),
        ('Interfaces', {'fields': ('interfaces',)}),
    )


# ============================================================================
# PORT GPON
# ============================================================================

@admin.register(GponPort)
class GponPortAdmin(ImportExportModelAdmin):
    list_display = ['olt', 'port_index', 'port_name', 'enabled', 'ont_count']
    list_filter = ['enabled']
    search_fields = ['port_name']
    raw_id_fields = ['olt']
    fieldsets = (
        ('Port', {'fields': ('olt', 'port_index', 'port_name', 'enabled')}),
        ('Optique', {'fields': ('rx_power_min_dbm', 'rx_power_max_dbm', 'ont_count')}),
    )


# ============================================================================
# SPLITTER
# ============================================================================

@admin.register(Splitter)
class SplitterAdmin(ImportExportModelAdmin):
    list_display = ['name', 'site', 'ratio', 'level']
    list_filter = ['site', 'ratio']
    search_fields = ['name']
    raw_id_fields = ['site', 'rack']
    fieldsets = (
        ('Splitter', {'fields': ('name', 'site', 'rack', 'ratio', 'level')}),
        ('Coordonnées', {'fields': ('latitude', 'longitude')}),
    )


# ============================================================================
# PORT DE SPLITTER
# ============================================================================

@admin.register(SplitterPort)
class SplitterPortAdmin(ImportExportModelAdmin):
    list_display = ['splitter', 'port_number', 'direction', 'is_used', 'connected_ont']
    list_filter = ['direction', 'is_used']
    raw_id_fields = ['splitter', 'connected_ont']
    fieldsets = (
        ('Port', {'fields': ('splitter', 'port_number', 'direction', 'is_used')}),
        ('Connexion', {'fields': ('connected_ont',)}),
    )


# ============================================================================
# CLIENT
# ============================================================================

@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):
    list_display = ['customer_id', 'full_name', 'email', 'phone']
    search_fields = ['customer_id', 'full_name', 'email', 'phone']
    fieldsets = (
        ('Client', {'fields': ('customer_id', 'full_name')}),
        ('Contact', {'fields': ('email', 'phone', 'address')}),
    )


# ============================================================================
# ONT
# ============================================================================

@admin.register(ONT)
class ONTAdmin(ImportExportModelAdmin):
    list_display = ['serial_number', 'olt', 'status', 'customer', 'last_seen_at']
    list_filter = ['status', 'service_type', 'olt']
    search_fields = ['serial_number', 'mac_address', 'customer__full_name']
    raw_id_fields = ['olt', 'gpon_port', 'vendor', 'customer', 'created_by']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    fieldsets = (
        ('Identification', {'fields': ('serial_number', 'mac_address', 'ip_address')}),
        ('Rattachement', {'fields': ('olt', 'gpon_port', 'ont_index')}),
        ('Optique', {'fields': ('rx_power', 'tx_power', 'distance_km', 'attenuation_db')}),
        ('Matériel', {'fields': ('vendor', 'model', 'firmware_version')}),
        ('Client', {'fields': ('customer', 'service_type')}),
        ('Localisation', {'fields': ('address', 'city', 'latitude', 'longitude')}),
        ('État', {'fields': ('status', 'last_seen_at')}),
        ('Métadonnées', {'fields': ('created_by', 'created_at', 'updated_at', 'deleted_at'), 'classes': ('collapse',)}),
    )


# ============================================================================
# CHEMIN OPTIQUE
# ============================================================================

@admin.register(OpticalPath)
class OpticalPathAdmin(ImportExportModelAdmin):
    list_display = ['olt', 'splitter', 'ont', 'fiber_length_km', 'total_loss_db', 'is_active']
    list_filter = ['is_active']
    raw_id_fields = ['olt', 'splitter', 'ont']
    fieldsets = (
        ('Chemin', {'fields': ('olt', 'splitter', 'ont')}),
        ('Caractéristiques', {'fields': ('fiber_length_km', 'total_loss_db', 'is_active')}),
    )


# ============================================================================
# CÂBLE FIBRE
# ============================================================================

@admin.register(FiberCable)
class FiberCableAdmin(ImportExportModelAdmin):
    list_display = ['name', 'fiber_count', 'length_km', 'cable_type']
    list_filter = ['cable_type']
    search_fields = ['name']
    fieldsets = (
        ('Câble', {'fields': ('name', 'fiber_count', 'length_km', 'cable_type')}),
    )


# ============================================================================
# BRIN DE FIBRE
# ============================================================================

@admin.register(FiberCore)
class FiberCoreAdmin(ImportExportModelAdmin):
    list_display = ['cable', 'core_number', 'connected_to']
    search_fields = ['cable__name']
    raw_id_fields = ['cable', 'connected_to']
    fieldsets = (
        ('Brin', {'fields': ('cable', 'core_number', 'connected_to')}),
    )


# ============================================================================
# LIEN FIBRE
# ============================================================================

@admin.register(FibreLink)
class FibreLinkAdmin(ImportExportModelAdmin):
    list_display = ['name', 'interface_a', 'interface_b', 'link_type', 'is_active']
    list_filter = ['link_type', 'is_active']
    search_fields = ['name']
    raw_id_fields = ['interface_a', 'interface_b']
    fieldsets = (
        ('Lien', {'fields': ('name', 'interface_a', 'interface_b', 'link_type')}),
        ('Performance', {'fields': ('bandwidth_mbps', 'utilization_pct', 'attenuation_db', 'length_km')}),
        ('État', {'fields': ('is_active', 'last_updated_at')}),
    )


# ============================================================================
# ALIMENTATION (PowerSupply)
# ============================================================================

@admin.register(PowerSupply)
class PowerSupplyAdmin(ImportExportModelAdmin):
    list_display = ['olt', 'slot', 'status', 'power_watts']
    list_filter = ['status']
    raw_id_fields = ['olt']
    fieldsets = (
        ('Alimentation', {'fields': ('olt', 'slot', 'status', 'power_watts')}),
    )


# ============================================================================
# MODULE DE VENTILATION
# ============================================================================

@admin.register(FanModule)
class FanModuleAdmin(ImportExportModelAdmin):
    list_display = ['olt', 'name', 'speed_rpm', 'status']
    list_filter = ['status']
    raw_id_fields = ['olt']
    fieldsets = (
        ('Ventilateur', {'fields': ('olt', 'name', 'speed_rpm', 'status')}),
    )


# ============================================================================
# SAUVEGARDE DE CONFIGURATION
# ============================================================================

@admin.register(ConfigurationBackup)
class ConfigurationBackupAdmin(ImportExportModelAdmin):
    list_display = ['olt', 'filename', 'backup_date']
    list_filter = ['backup_date']
    search_fields = ['filename']
    raw_id_fields = ['olt']
    fieldsets = (
        ('Sauvegarde', {'fields': ('olt', 'filename', 'config_text', 'backup_date')}),
    )


# ============================================================================
# HISTORIQUE
# ============================================================================

@admin.register(EquipmentHistory)
class EquipmentHistoryAdmin(ImportExportModelAdmin):
    list_display = ['olt', 'field_name', 'changed_by', 'change_date']
    list_filter = ['change_date']
    search_fields = ['field_name', 'old_value', 'new_value']
    raw_id_fields = ['olt', 'changed_by']
    fieldsets = (
        ('Modification', {'fields': ('olt', 'field_name', 'old_value', 'new_value', 'changed_by', 'change_date')}),
    )
