# apps/equipements/models.py
"""
Modèles pour l'application 'equipements' – Gestion de l'infrastructure FTTH
Inclut : fabricants, gouvernorats/délégations, sites, baies, types d'équipements,
OLT, cartes, interfaces réseau, IP, VLAN, splitters, ONT, clients,
chemins optiques, liens fibre, alimentations, ventilateurs,
sauvegardes de configuration, historique, câbles fibres.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from apps.core.models import SoftDeleteModel, BaseModel
from apps.users.models import User


# ----------------------------------------------------------------------
# 1. Fabricant (Vendor)
# ----------------------------------------------------------------------

class Vendor(BaseModel):
    """Fabricant d'équipement (Huawei, Nokia, ZTE, etc.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    website = models.URLField(blank=True, verbose_name="Site web")
    support_email = models.EmailField(blank=True, verbose_name="Email support")
    support_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone support")
    logo_url = models.URLField(blank=True, verbose_name="URL du logo")

    class Meta:
        db_table = 'equipements_vendors'
        ordering = ['name']
        verbose_name = "Fabricant"
        verbose_name_plural = "Fabricants"

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------
# 2. Gouvernorat (Tunisie)
# ----------------------------------------------------------------------

class Gouvernorat(BaseModel):
    """Gouvernorat tunisien (ex: Tunis, Sfax, Sousse)"""
    code = models.CharField(max_length=2, unique=True, verbose_name="Code (2 chiffres)")
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom du gouvernorat")

    class Meta:
        db_table = 'equipements_gouvernorats'
        ordering = ['nom']
        verbose_name = "Gouvernorat"
        verbose_name_plural = "Gouvernorats"

    def __str__(self):
        return self.nom


# ----------------------------------------------------------------------
# 3. Délégation (Tunisie)
# ----------------------------------------------------------------------

class Delegation(BaseModel):
    """Délégation (sous-gouvernorat) – ex: Tunis Centre, Sfax Sud"""
    gouvernorat = models.ForeignKey(Gouvernorat, on_delete=models.PROTECT, related_name='delegations', verbose_name="Gouvernorat")
    code = models.CharField(max_length=4, verbose_name="Code de la délégation (ex: 01, 02)")
    nom = models.CharField(max_length=100, verbose_name="Nom de la délégation")

    class Meta:
        db_table = 'equipements_delegations'
        constraints = [
            models.UniqueConstraint(fields=['gouvernorat', 'code'], name='unique_delegation_code')
        ]
        ordering = ['gouvernorat', 'nom']
        verbose_name = "Délégation"
        verbose_name_plural = "Délégations"

    def __str__(self):
        return f"{self.nom} ({self.gouvernorat.nom})"


# ----------------------------------------------------------------------
# 4. Site géographique
# ----------------------------------------------------------------------

class Site(BaseModel):
    """
    Site géographique (datacenter, POP, centrale télécom).
    Localisé en Tunisie par gouvernorat/délégation.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    address = models.TextField(blank=True, verbose_name="Adresse")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    code_postal = models.CharField(max_length=10, blank=True, verbose_name="Code postal")
    gouvernorat = models.ForeignKey(Gouvernorat, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Gouvernorat")
    delegation = models.ForeignKey(Delegation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Délégation")
    contact_name = models.CharField(max_length=100, blank=True, verbose_name="Contact")
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone contact")
    latitude = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name="Latitude"
    )
    longitude = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        verbose_name="Longitude"
    )

    class Meta:
        db_table = 'equipements_sites'
        ordering = ['name']
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['code_postal']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


# ----------------------------------------------------------------------
# 5. Rack (baie technique)
# ----------------------------------------------------------------------

class Rack(BaseModel):
    """Baie technique physique dans un site."""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='racks', verbose_name="Site")
    name = models.CharField(max_length=100, verbose_name="Nom de la baie")
    code = models.CharField(max_length=50, unique=True, verbose_name="Code baie")
    total_units = models.IntegerField(default=42, verbose_name="Hauteur totale (U)")
    room = models.CharField(max_length=100, blank=True, verbose_name="Salle")
    row = models.CharField(max_length=50, blank=True, verbose_name="Rangée")
    position = models.CharField(max_length=50, blank=True, verbose_name="Position")

    class Meta:
        db_table = 'equipements_racks'
        ordering = ['site', 'name']
        verbose_name = "Baie"
        verbose_name_plural = "Baies"

    def __str__(self):
        return f"{self.code} - {self.name} ({self.site.code})"


# ----------------------------------------------------------------------
# 6. Type d'équipement (DeviceType)
# ----------------------------------------------------------------------

class DeviceType(BaseModel):
    """Modèle générique d'un équipement (ex: MA5600T, SmartAX EA5800)."""
    class DeviceClass(models.TextChoices):
        OLT = 'olt', 'OLT (Optical Line Terminal)'
        ONT = 'ont', 'ONT (Optical Network Terminal)'
        ROUTER = 'router', 'Routeur'
        SWITCH = 'switch', 'Switch'
        FIREWALL = 'firewall', 'Firewall'
        SERVER = 'server', 'Serveur'
        OTHER = 'other', 'Autre'

    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='device_types', verbose_name="Fabricant")
    model = models.CharField(max_length=100, verbose_name="Modèle")
    device_class = models.CharField(max_length=20, choices=DeviceClass.choices, default=DeviceClass.OLT, verbose_name="Classe d'équipement")
    part_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro de pièce")
    u_height = models.IntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(50)], verbose_name="Hauteur (U)")
    power_consumption_w = models.IntegerField(null=True, blank=True, verbose_name="Consommation électrique (W)")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        db_table = 'equipements_device_types'
        constraints = [
            models.UniqueConstraint(fields=['vendor', 'model'], name='unique_vendor_model')
        ]
        ordering = ['vendor', 'model']
        verbose_name = "Type d'équipement"
        verbose_name_plural = "Types d'équipement"

    def __str__(self):
        return f"{self.vendor.code} {self.model}"


# ----------------------------------------------------------------------
# 7. OLT (Optical Line Terminal)
# ----------------------------------------------------------------------

class OLT(SoftDeleteModel):
    """Équipement central GPON/XGS-PON."""
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Actif'
        INACTIVE = 'inactive', 'Inactif'
        MAINTENANCE = 'maintenance', 'Maintenance'
        DEGRADED = 'degraded', 'Dégradé'

    class SNMPVersion(models.TextChoices):
        V1 = '1', 'SNMPv1'
        V2C = '2c', 'SNMPv2c'
        V3 = '3', 'SNMPv3'

    # Identification
    hostname = models.CharField(max_length=100, unique=True, db_index=True, verbose_name="Nom d'hôte")
    ip_address = models.GenericIPAddressField(unique=True, db_index=True, verbose_name="Adresse IP")
    management_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP de gestion")

    # SNMP (les secrets seront chiffrés – voir méthode ci-dessous)
    snmp_community = models.CharField(max_length=100, default='public', verbose_name="Communauté SNMP")
    snmp_version = models.CharField(max_length=3, choices=SNMPVersion.choices, default=SNMPVersion.V2C, verbose_name="Version SNMP")
    snmp_port = models.IntegerField(default=161, validators=[MinValueValidator(1), MaxValueValidator(65535)], verbose_name="Port SNMP")
    snmp_v3_username = models.CharField(max_length=100, blank=True, verbose_name="Utilisateur SNMPv3")
    snmp_v3_auth_key = models.CharField(max_length=200, blank=True, verbose_name="Clé d'authentification")
    snmp_v3_priv_key = models.CharField(max_length=200, blank=True, verbose_name="Clé de confidentialité")
    snmp_v3_auth_protocol = models.CharField(max_length=20, blank=True, choices=[('MD5', 'MD5'), ('SHA', 'SHA')], verbose_name="Protocole d'authentification")
    snmp_v3_priv_protocol = models.CharField(max_length=20, blank=True, choices=[('DES', 'DES'), ('AES', 'AES')], verbose_name="Protocole de confidentialité")

    # Produit
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='olts', verbose_name="Fabricant")
    device_type = models.ForeignKey(DeviceType, on_delete=models.PROTECT, related_name='olts', verbose_name="Type d'équipement")
    serial_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro de série")
    firmware_version = models.CharField(max_length=50, blank=True, verbose_name="Version firmware")
    hardware_version = models.CharField(max_length=50, blank=True, verbose_name="Version matérielle")

    # Cycle de vie (inventaire)
    asset_tag = models.CharField(max_length=100, unique=True, blank=True, verbose_name="Tag actif")
    purchase_date = models.DateField(null=True, blank=True, verbose_name="Date d'achat")
    warranty_end = models.DateField(null=True, blank=True, verbose_name="Fin de garantie")
    end_of_support = models.DateField(null=True, blank=True, verbose_name="Fin de support fabricant")
    maintenance_contract = models.CharField(max_length=100, blank=True, verbose_name="Contrat de maintenance")

    # Localisation (intégrée)
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name='olts', verbose_name="Site")
    rack = models.ForeignKey(Rack, on_delete=models.SET_NULL, null=True, blank=True, related_name='olts', verbose_name="Baie")
    rack_unit = models.IntegerField(null=True, blank=True, verbose_name="Unité de rack")
    address = models.TextField(blank=True, verbose_name="Adresse complète")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    region = models.CharField(max_length=100, blank=True, verbose_name="Région")
    code_postal = models.CharField(max_length=10, blank=True, verbose_name="Code postal")
    gouvernorat = models.ForeignKey(Gouvernorat, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Gouvernorat")
    delegation = models.ForeignKey(Delegation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Délégation")
    latitude = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)], verbose_name="Latitude")
    longitude = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)], verbose_name="Longitude")

    # Capacité
    max_pon_ports = models.IntegerField(default=16, verbose_name="Nombre max de ports PON")
    max_onts_per_port = models.IntegerField(default=64, verbose_name="ONT max par port PON")

    # État
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True, verbose_name="Statut")
    last_polled_at = models.DateTimeField(null=True, blank=True, verbose_name="Dernier poll SNMP")
    uptime_seconds = models.BigIntegerField(null=True, blank=True, verbose_name="Uptime (secondes)")
    description = models.TextField(blank=True, verbose_name="Description")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créé par")

    class Meta:
        db_table = 'equipements_olts'
        ordering = ['hostname']
        verbose_name = "OLT"
        verbose_name_plural = "OLTs"
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['status']),
            models.Index(fields=['site']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.hostname} ({self.ip_address})"

    @property
    def total_capacity(self):
        return self.max_pon_ports * self.max_onts_per_port

    def clean(self):
        # Validation des règles métier
        if self.rack and self.rack_unit:
            if self.rack_unit < 1 or self.rack_unit > self.rack.total_units:
                raise ValidationError({'rack_unit': f"L'unité doit être comprise entre 1 et {self.rack.total_units}."})


# ----------------------------------------------------------------------
# 8. Carte (Board) – OLT modulaire
# ----------------------------------------------------------------------

class Board(BaseModel):
    """Carte enfichable dans un OLT (contrôle, GPON, uplink, alimentation)."""
    class BoardType(models.TextChoices):
        CONTROL = 'control', 'Carte de contrôle'
        GPON = 'gpon', 'Carte GPON'
        UPLINK = 'uplink', 'Carte uplink'
        POWER = 'power', 'Module d’alimentation'

    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='boards', verbose_name="OLT")
    slot_number = models.IntegerField(verbose_name="Numéro de slot", validators=[MinValueValidator(1)])
    board_type = models.CharField(max_length=20, choices=BoardType.choices, verbose_name="Type")
    model = models.CharField(max_length=100, verbose_name="Modèle")
    serial_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro de série")
    status = models.CharField(max_length=20, choices=OLT.Status.choices, default=OLT.Status.ACTIVE, verbose_name="Statut")
    firmware_version = models.CharField(max_length=50, blank=True, verbose_name="Version firmware")

    class Meta:
        db_table = 'equipements_boards'
        constraints = [
            models.UniqueConstraint(fields=['olt', 'slot_number'], name='unique_board_slot')
        ]
        ordering = ['olt', 'slot_number']
        verbose_name = "Carte"
        verbose_name_plural = "Cartes"

    def __str__(self):
        return f"{self.olt.hostname} - Slot {self.slot_number} ({self.get_board_type_display()})"


# ----------------------------------------------------------------------
# 9. Interface réseau (NetworkInterface)
# ----------------------------------------------------------------------

class NetworkInterface(BaseModel):
    """Interface réseau (physique ou logique) d'un OLT, rattachée à une carte."""
    class InterfaceType(models.TextChoices):
        ETHERNET = 'ethernet', 'Ethernet'
        GPON = 'gpon', 'GPON'
        XGSPON = 'xgspon', 'XGS-PON'
        SFP = 'sfp', 'SFP'
        LOOPBACK = 'loopback', 'Loopback'

    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='network_interfaces', verbose_name="OLT")
    board = models.ForeignKey(Board, on_delete=models.SET_NULL, null=True, blank=True, related_name='interfaces', verbose_name="Carte mère")
    name = models.CharField(max_length=100, verbose_name="Nom de l’interface (ex: eth0, 1/1/1)")
    interface_type = models.CharField(max_length=20, choices=InterfaceType.choices, verbose_name="Type")
    admin_status = models.BooleanField(default=True, verbose_name="Statut admin (up/down)")
    oper_status = models.BooleanField(default=True, verbose_name="Statut opérationnel")
    mac_address = models.CharField(
        max_length=17, blank=True,
        validators=[RegexValidator(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', message="Format MAC invalide (ex: AA:BB:CC:DD:EE:FF)")],
        verbose_name="Adresse MAC"
    )
    speed_mbps = models.IntegerField(null=True, blank=True, verbose_name="Vitesse (Mbps)")
    mtu = models.IntegerField(default=1500, verbose_name="MTU")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        db_table = 'equipements_network_interfaces'
        constraints = [
            models.UniqueConstraint(fields=['olt', 'name'], name='unique_interface_name')
        ]
        ordering = ['olt', 'name']
        verbose_name = "Interface réseau"
        verbose_name_plural = "Interfaces réseau"

    def __str__(self):
        return f"{self.olt.hostname}:{self.name}"

    def clean(self):
        if self.board and self.board.olt != self.olt:
            raise ValidationError("La carte n'appartient pas à cet OLT.")


# ----------------------------------------------------------------------
# 10. Adresse IP (IPAddress)
# ----------------------------------------------------------------------

class IPAddress(BaseModel):
    """Adresse IP attachée à une interface réseau."""
    interface = models.ForeignKey(NetworkInterface, on_delete=models.CASCADE, related_name='ip_addresses', verbose_name="Interface")
    ip_address = models.GenericIPAddressField(verbose_name="Adresse IP")
    subnet_mask = models.IntegerField(verbose_name="Masque (CIDR)", validators=[MinValueValidator(1), MaxValueValidator(128)])
    gateway = models.GenericIPAddressField(null=True, blank=True, verbose_name="Passerelle")
    is_primary = models.BooleanField(default=False, verbose_name="Adresse principale")
    vrf = models.CharField(max_length=100, blank=True, verbose_name="VRF (optionnel)")

    class Meta:
        db_table = 'equipements_ip_addresses'
        constraints = [
            models.UniqueConstraint(fields=['interface', 'ip_address'], name='unique_interface_ip')
        ]
        verbose_name = "Adresse IP"
        verbose_name_plural = "Adresses IP"

    def __str__(self):
        return f"{self.ip_address}/{self.subnet_mask} ({self.interface.name})"


# ----------------------------------------------------------------------
# 11. VLAN
# ----------------------------------------------------------------------

class VLAN(BaseModel):
    """VLAN logique dans le réseau."""
    vlan_id = models.IntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(4094)], verbose_name="VLAN ID")
    name = models.CharField(max_length=100, verbose_name="Nom du VLAN")
    description = models.TextField(blank=True, verbose_name="Description")
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name='vlans', verbose_name="Site")
    interfaces = models.ManyToManyField(NetworkInterface, related_name='vlans', blank=True, verbose_name="Interfaces associées")

    class Meta:
        db_table = 'equipements_vlans'
        ordering = ['vlan_id']
        verbose_name = "VLAN"
        verbose_name_plural = "VLANs"

    def __str__(self):
        return f"VLAN {self.vlan_id} - {self.name}"


# ----------------------------------------------------------------------
# 12. Port GPON (GponPort)
# ----------------------------------------------------------------------

class GponPort(SoftDeleteModel):
    """Port PON (GPON/XGS-PON) sur une OLT."""
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='gpon_ports', verbose_name="OLT")
    port_index = models.IntegerField(verbose_name="Index du port", validators=[MinValueValidator(1)])
    port_name = models.CharField(max_length=50, blank=True, verbose_name="Nom du port")
    enabled = models.BooleanField(default=True, verbose_name="Actif")
    ont_count = models.IntegerField(default=0, verbose_name="Nombre d'ONT")
    rx_power_min_dbm = models.FloatField(default=-28.0, help_text="dBm", verbose_name="Puissance RX minimale (dBm)")
    rx_power_max_dbm = models.FloatField(default=-8.0, help_text="dBm", verbose_name="Puissance RX maximale (dBm)")

    class Meta:
        db_table = 'equipements_gpon_ports'
        constraints = [
            models.UniqueConstraint(fields=['olt', 'port_index'], name='unique_gpon_port')
        ]
        ordering = ['olt', 'port_index']
        verbose_name = "Port PON"
        verbose_name_plural = "Ports PON"

    def __str__(self):
        return f"{self.olt.hostname} - {self.port_name or self.port_index}"


# ----------------------------------------------------------------------
# 13. Splitter (diviseur optique passif)
# ----------------------------------------------------------------------

class Splitter(BaseModel):
    """Splitter optique passif (1:8, 1:16, 1:32, etc.)."""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='splitters', verbose_name="Site")
    name = models.CharField(max_length=100, verbose_name="Nom du splitter")
    ratio = models.CharField(max_length=20, verbose_name="Rapport (ex: 1:8, 1:16, 1:32)")
    level = models.IntegerField(verbose_name="Niveau hiérarchique (1 = premier splitter)", validators=[MinValueValidator(1)])
    latitude = models.FloatField(null=True, blank=True, verbose_name="Latitude", validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.FloatField(null=True, blank=True, verbose_name="Longitude", validators=[MinValueValidator(-180), MaxValueValidator(180)])
    rack = models.ForeignKey(Rack, on_delete=models.SET_NULL, null=True, blank=True, related_name='splitters', verbose_name="Baie (optionnel)")

    class Meta:
        db_table = 'equipements_splitters'
        ordering = ['site', 'level', 'name']
        verbose_name = "Splitter"
        verbose_name_plural = "Splitters"

    def __str__(self):
        return f"{self.name} ({self.ratio}) - {self.site.code}"


# ----------------------------------------------------------------------
# 14. SplitterPort (port d'entrée/sortie d'un splitter)
# ----------------------------------------------------------------------

class SplitterPort(BaseModel):
    """Port physique d'un splitter (entrée ou sortie)."""
    DIRECTION_CHOICES = [('input', 'Entrée'), ('output', 'Sortie')]

    splitter = models.ForeignKey(Splitter, on_delete=models.CASCADE, related_name='ports', verbose_name="Splitter")
    port_number = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Numéro de port")
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, verbose_name="Sens")
    is_used = models.BooleanField(default=False, verbose_name="Utilisé")
    connected_ont = models.ForeignKey('ONT', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="ONT connecté")

    class Meta:
        db_table = 'equipements_splitter_ports'
        constraints = [
            models.UniqueConstraint(fields=['splitter', 'port_number'], name='unique_splitter_port')
        ]
        ordering = ['splitter', 'port_number']
        verbose_name = "Port de splitter"
        verbose_name_plural = "Ports de splitter"

    def __str__(self):
        return f"{self.splitter.name} - {self.direction} #{self.port_number}"


# ----------------------------------------------------------------------
# 15. Client (Customer)
# ----------------------------------------------------------------------

class Customer(BaseModel):
    """Client final abonné au service FTTH."""
    customer_id = models.CharField(max_length=50, unique=True, verbose_name="ID client")
    full_name = models.CharField(max_length=255, verbose_name="Nom complet")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    address = models.TextField(blank=True, verbose_name="Adresse")

    class Meta:
        db_table = 'equipements_customers'
        ordering = ['customer_id']
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self):
        return f"{self.customer_id} - {self.full_name}"


# ----------------------------------------------------------------------
# 16. ONT (Optical Network Terminal)
# ----------------------------------------------------------------------

class ONT(SoftDeleteModel):
    """Terminal optique chez l'abonné."""
    class Status(models.TextChoices):
        ONLINE = 'online', 'En ligne'
        OFFLINE = 'offline', 'Hors ligne'
        LOS = 'los', 'LOS (Loss of Signal)'
        DEGRADED = 'degraded', 'Dégradé'
        UNKNOWN = 'unknown', 'Inconnu'

    class ServiceType(models.TextChoices):
        RESIDENTIAL = 'residential', 'Résidentiel'
        BUSINESS = 'business', 'Entreprise'
        WHOLESALE = 'wholesale', 'Wholesale'

    serial_number = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="Numéro de série")
    mac_address = models.CharField(
        max_length=17, unique=True,
        validators=[RegexValidator(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', message="Format MAC invalide")],
        verbose_name="Adresse MAC"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")

    # Rattachement réseau (sans circularité)
    olt = models.ForeignKey(OLT, on_delete=models.PROTECT, related_name='onts', verbose_name="OLT")
    gpon_port = models.ForeignKey(GponPort, on_delete=models.SET_NULL, null=True, blank=True, related_name='onts', verbose_name="Port GPON")
    ont_index = models.IntegerField(null=True, blank=True, help_text="Index sur le port GPON", verbose_name="Index ONT")

    # Optique
    rx_power = models.FloatField(null=True, blank=True, help_text="dBm – puissance reçue", verbose_name="Puissance RX (dBm)")
    tx_power = models.FloatField(null=True, blank=True, help_text="dBm – puissance émise", verbose_name="Puissance TX (dBm)")
    distance_km = models.FloatField(null=True, blank=True, verbose_name="Distance (km)")
    attenuation_db = models.FloatField(null=True, blank=True, verbose_name="Atténuation (dB)")

    # Matériel
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fabricant")
    model = models.CharField(max_length=100, blank=True, verbose_name="Modèle")
    firmware_version = models.CharField(max_length=50, blank=True, verbose_name="Version firmware")

    # État
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNKNOWN, db_index=True, verbose_name="Statut")
    last_seen_at = models.DateTimeField(null=True, blank=True, verbose_name="Dernière apparition")

    # Client
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='onts', verbose_name="Client")
    service_type = models.CharField(max_length=20, choices=ServiceType.choices, default=ServiceType.RESIDENTIAL, verbose_name="Type de service")

    # Localisation (adresse client)
    address = models.TextField(blank=True, verbose_name="Adresse client")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    latitude = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)], verbose_name="Latitude")
    longitude = models.FloatField(null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)], verbose_name="Longitude")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créé par")

    class Meta:
        db_table = 'equipements_onts'
        ordering = ['olt', 'serial_number']
        verbose_name = "ONT"
        verbose_name_plural = "ONTs"
        indexes = [
            models.Index(fields=['olt', 'status']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['customer']),
        ]

    def __str__(self):
        return f"{self.serial_number} ({self.olt.hostname})"

    @property
    def is_online(self):
        return self.status == self.Status.ONLINE

    @property
    def rx_power_critical(self):
        if self.rx_power is None or not self.gpon_port:
            return False
        return self.rx_power < self.gpon_port.rx_power_min_dbm or self.rx_power > self.gpon_port.rx_power_max_dbm

    def clean(self):
        if self.gpon_port and self.gpon_port.olt != self.olt:
            raise ValidationError("Le port GPON n'appartient pas à cet OLT.")


# ----------------------------------------------------------------------
# 17. Chemin optique (OpticalPath)
# ----------------------------------------------------------------------

class OpticalPath(BaseModel):
    """Liaison logique complète OLT → splitter → ONT."""
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='optical_paths', verbose_name="OLT")
    splitter = models.ForeignKey(Splitter, on_delete=models.CASCADE, related_name='optical_paths', verbose_name="Splitter")
    ont = models.ForeignKey(ONT, on_delete=models.CASCADE, related_name='optical_paths', verbose_name="ONT")
    fiber_length_km = models.FloatField(validators=[MinValueValidator(0)], verbose_name="Longueur fibre (km)")
    total_loss_db = models.FloatField(validators=[MinValueValidator(0)], verbose_name="Affaiblissement total (dB)")
    is_active = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'equipements_optical_paths'
        constraints = [
            models.UniqueConstraint(fields=['olt', 'splitter', 'ont'], name='unique_optical_path')
        ]
        verbose_name = "Chemin optique"
        verbose_name_plural = "Chemins optiques"

    def __str__(self):
        return f"{self.olt.hostname} → {self.splitter.name} → {self.ont.serial_number}"


# ----------------------------------------------------------------------
# 18. Câble fibre (FiberCable)
# ----------------------------------------------------------------------

class FiberCable(BaseModel):
    """Câble fibre optique contenant plusieurs brins."""
    class CableType(models.TextChoices):
        ARMORED = 'armored', 'Armé'
        DIELECTRIC = 'dielectric', 'Diélectrique'

    name = models.CharField(max_length=100, verbose_name="Nom du câble")
    fiber_count = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Nombre de fibres")
    length_km = models.FloatField(validators=[MinValueValidator(0)], verbose_name="Longueur (km)")
    cable_type = models.CharField(max_length=20, choices=CableType.choices, default=CableType.DIELECTRIC, verbose_name="Type")

    class Meta:
        db_table = 'equipements_fiber_cables'
        ordering = ['name']
        verbose_name = "Câble fibre"
        verbose_name_plural = "Câbles fibre"

    def __str__(self):
        return f"{self.name} ({self.fiber_count} fibres)"


# ----------------------------------------------------------------------
# 19. Brin de fibre (FiberCore)
# ----------------------------------------------------------------------

class FiberCore(BaseModel):
    """Brin de fibre individuel à l'intérieur d'un câble."""
    cable = models.ForeignKey(FiberCable, on_delete=models.CASCADE, related_name='cores', verbose_name="Câble")
    core_number = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Numéro de brin")
    connected_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Connecté à")

    class Meta:
        db_table = 'equipements_fiber_cores'
        constraints = [
            models.UniqueConstraint(fields=['cable', 'core_number'], name='unique_fiber_core')
        ]
        ordering = ['cable', 'core_number']
        verbose_name = "Brin de fibre"
        verbose_name_plural = "Brins de fibre"

    def __str__(self):
        return f"{self.cable.name} - Brin {self.core_number}"


# ----------------------------------------------------------------------
# 20. Lien fibre (FibreLink) – inter-OLT (avec interfaces)
# ----------------------------------------------------------------------

class FibreLink(SoftDeleteModel):
    """Lien fibre optique entre deux interfaces d'OLT (ou entre OLT)."""
    class LinkType(models.TextChoices):
        BACKBONE = 'backbone', 'Backbone'
        DISTRIBUTION = 'distribution', 'Distribution'
        ACCESS = 'access', 'Accès'

    name = models.CharField(max_length=100, verbose_name="Nom")
    interface_a = models.ForeignKey(NetworkInterface, on_delete=models.PROTECT, related_name='links_as_a', verbose_name="Interface A")
    interface_b = models.ForeignKey(NetworkInterface, on_delete=models.PROTECT, related_name='links_as_b', verbose_name="Interface B")
    link_type = models.CharField(max_length=20, choices=LinkType.choices, default=LinkType.BACKBONE, verbose_name="Type de lien")
    bandwidth_mbps = models.FloatField(validators=[MinValueValidator(0)], verbose_name="Bande passante (Mbps)")
    utilization_pct = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Utilisation (%)")
    attenuation_db = models.FloatField(null=True, blank=True, verbose_name="Atténuation (dB)")
    length_km = models.FloatField(null=True, blank=True, verbose_name="Longueur (km)")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    last_updated_at = models.DateTimeField(null=True, blank=True, verbose_name="Dernière mise à jour")

    class Meta:
        db_table = 'equipements_fibre_links'
        ordering = ['name']
        verbose_name = "Lien fibre"
        verbose_name_plural = "Liens fibre"

    def __str__(self):
        return f"{self.name} : {self.interface_a.olt.hostname} ↔ {self.interface_b.olt.hostname}"

    @property
    def is_congested(self):
        return self.utilization_pct > 80

    def clean(self):
        if self.interface_a.olt == self.interface_b.olt:
            raise ValidationError("Les deux interfaces ne peuvent pas appartenir au même OLT.")
        if self.interface_a == self.interface_b:
            raise ValidationError("Les interfaces source et destination doivent être différentes.")


# ----------------------------------------------------------------------
# 21. Alimentation (PowerSupply)
# ----------------------------------------------------------------------

class PowerSupply(BaseModel):
    """Module d'alimentation (PSU) redondant d'un OLT."""
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='power_supplies', verbose_name="OLT")
    slot = models.CharField(max_length=20, verbose_name="Slot / Emplacement")
    status = models.CharField(max_length=20, choices=OLT.Status.choices, default=OLT.Status.ACTIVE, verbose_name="Statut")
    power_watts = models.IntegerField(null=True, blank=True, verbose_name="Puissance (W)")

    class Meta:
        db_table = 'equipements_power_supplies'
        ordering = ['olt', 'slot']
        verbose_name = "Alimentation"
        verbose_name_plural = "Alimentations"

    def __str__(self):
        return f"{self.olt.hostname} - Alim {self.slot}"


# ----------------------------------------------------------------------
# 22. Module de ventilation (FanModule)
# ----------------------------------------------------------------------

class FanModule(BaseModel):
    """Module de ventilation (ventilateur) d'un OLT."""
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='fan_modules', verbose_name="OLT")
    name = models.CharField(max_length=100, verbose_name="Nom du module")
    speed_rpm = models.IntegerField(null=True, blank=True, verbose_name="Vitesse (RPM)")
    status = models.CharField(max_length=20, choices=OLT.Status.choices, default=OLT.Status.ACTIVE, verbose_name="Statut")

    class Meta:
        db_table = 'equipements_fan_modules'
        verbose_name = "Module de ventilation"
        verbose_name_plural = "Modules de ventilation"

    def __str__(self):
        return f"{self.olt.hostname} - Ventilo {self.name}"


# ----------------------------------------------------------------------
# 23. Sauvegarde de configuration (ConfigurationBackup)
# ----------------------------------------------------------------------

class ConfigurationBackup(BaseModel):
    """Sauvegarde de la configuration texte d'un OLT."""
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='backups', verbose_name="OLT")
    filename = models.CharField(max_length=255, verbose_name="Nom du fichier")
    config_text = models.TextField(verbose_name="Contenu de la configuration")
    backup_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de sauvegarde")

    class Meta:
        db_table = 'equipements_config_backups'
        ordering = ['-backup_date']
        verbose_name = "Sauvegarde de configuration"
        verbose_name_plural = "Sauvegardes de configuration"

    def __str__(self):
        return f"{self.olt.hostname} - {self.filename}"


# ----------------------------------------------------------------------
# 24. Historique des équipements (EquipmentHistory)
# ----------------------------------------------------------------------

class EquipmentHistory(BaseModel):
    """Journal des modifications sur un OLT (traçabilité)."""
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='history', verbose_name="OLT")
    field_name = models.CharField(max_length=100, verbose_name="Champ modifié")
    old_value = models.TextField(blank=True, verbose_name="Ancienne valeur")
    new_value = models.TextField(blank=True, verbose_name="Nouvelle valeur")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Modifié par")
    change_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de modification")

    class Meta:
        db_table = 'equipements_history'
        ordering = ['-change_date']
        verbose_name = "Historique"
        verbose_name_plural = "Historiques"

    def __str__(self):
        return f"{self.olt.hostname} - {self.field_name} modifié le {self.change_date}"
