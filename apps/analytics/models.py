from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from apps.core.models import BaseModel
from apps.equipements.models import OLT, NetworkInterface, FibreLink, Site

class KPIHistory(BaseModel):
    """Agrégation horaire/journalière des KPIs."""
    class Period(models.TextChoices):
        HOUR = 'hour', 'Horaire'
        DAY = 'day', 'Journalier'
        WEEK = 'week', 'Hebdomadaire'
        MONTH = 'month', 'Mensuel'

    period = models.CharField(max_length=10, choices=Period.choices, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, null=True, blank=True)

    # Métriques globales
    total_olts = models.IntegerField(default=0)
    active_olts = models.IntegerField(default=0)
    total_onts = models.IntegerField(default=0)
    online_onts = models.IntegerField(default=0)
    avg_cpu_usage = models.FloatField(null=True, blank=True)
    avg_memory_usage = models.FloatField(null=True, blank=True)
    avg_temperature = models.FloatField(null=True, blank=True)
    avg_rx_power = models.FloatField(null=True, blank=True)
    snmp_success_rate = models.FloatField(default=100.0)
    bfd_up_sessions = models.IntegerField(default=0)
    bfd_total_sessions = models.IntegerField(default=0)
    anomaly_count = models.IntegerField(default=0)
    alert_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'analytics_kpi_history'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['period', 'timestamp']),
            models.Index(fields=['olt', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.period} KPI @ {self.timestamp}"


class Report(BaseModel):
    """Rapport généré (PDF, Excel)."""
    class ReportType(models.TextChoices):
        DAILY = 'daily', 'Rapport quotidien'
        WEEKLY = 'weekly', 'Rapport hebdomadaire'
        MONTHLY = 'monthly', 'Rapport mensuel'
        CUSTOM = 'custom', 'Personnalisé'

    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        GENERATING = 'generating', 'Génération en cours'
        READY = 'ready', 'Prêt'
        FAILED = 'failed', 'Échec'

    class Format(models.TextChoices):
        PDF = 'pdf', 'PDF'
        EXCEL = 'xlsx', 'Excel'

    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=10, choices=ReportType.choices)
    format = models.CharField(max_length=10, choices=Format.choices, default=Format.PDF)
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    file = models.FileField(upload_to='reports/%Y/%m/%d/', null=True, blank=True)
    parameters = models.JSONField(default=dict, help_text="Filtres additionnels (olts, sites, etc.)")
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'analytics_reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class DashboardWidget(BaseModel):
    """Widget personnalisable pour tableaux de bord utilisateur."""
    class WidgetType(models.TextChoices):
        LINE_CHART = 'line_chart', 'Graphique linéaire'
        BAR_CHART = 'bar_chart', 'Graphique à barres'
        PIE_CHART = 'pie_chart', 'Camembert'
        GAUGE = 'gauge', 'Jauge'
        METRIC = 'metric', 'Indicateur simple'
        TABLE = 'table', 'Tableau de données'
        MAP = 'map', 'Carte géographique'

    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WidgetType.choices)
    config = models.JSONField(default=dict, help_text="Couleurs, axes, métriques, etc.")
    width = models.IntegerField(default=6, help_text="Colonnes (sur 12)")
    height = models.IntegerField(default=300, help_text="Hauteur en pixels")
    order = models.IntegerField(default=0)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='dashboard_widgets')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'analytics_dashboard_widgets'
        ordering = ['user', 'order']
        unique_together = [['user', 'order']]

    def __str__(self):
        return f"{self.name} (User: {self.user.email})"


# ============================================================================
# 4. APPAREIL RÉSEAU (NetworkDevice) – Pour SSH/SNMP
# ============================================================================

class NetworkDevice(BaseModel):
    """Appareil réseau (OLT, Switch, Router) avec accès SSH/SNMP pour collecte de données."""
    
    class DeviceType(models.TextChoices):
        OLT = 'olt', 'OLT'
        SWITCH = 'switch', 'Switch'
        ROUTER = 'router', 'Routeur'
        FIREWALL = 'firewall', 'Firewall'
    
    class AuthMethod(models.TextChoices):
        SSH_PASSWORD = 'ssh_password', 'SSH Mot de passe'
        SSH_KEY = 'ssh_key', 'SSH Clé'
        SNMP = 'snmp', 'SNMP'

    # Identification
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du dispositif")
    device_type = models.CharField(max_length=20, choices=DeviceType.choices, verbose_name="Type")
    ip_address = models.GenericIPAddressField(db_index=True, verbose_name="Adresse IP")
    hostname = models.CharField(max_length=100, blank=True, verbose_name="Nom d'hôte")
    
    # Localisation
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name='network_devices', verbose_name="Site")
    
    # Connexion SSH/SNMP
    auth_method = models.CharField(max_length=20, choices=AuthMethod.choices, default=AuthMethod.SSH_PASSWORD, verbose_name="Méthode")
    ssh_username = models.CharField(max_length=100, blank=True, verbose_name="Utilisateur SSH")
    ssh_password = models.CharField(max_length=200, blank=True, verbose_name="Mot de passe SSH (chiffré)")
    ssh_port = models.IntegerField(default=22, validators=[MinValueValidator(1), MaxValueValidator(65535)], verbose_name="Port SSH")
    ssh_key = models.TextField(blank=True, verbose_name="Clé privée SSH (optionnel)")
    
    # SNMP (si utilisé)
    snmp_community = models.CharField(max_length=100, blank=True, default='public', verbose_name="Communauté SNMP")
    snmp_port = models.IntegerField(default=161, validators=[MinValueValidator(1), MaxValueValidator(65535)], verbose_name="Port SNMP")
    
    # État
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Actif")
    is_reachable = models.BooleanField(default=False, verbose_name="Accessible")
    last_connection_at = models.DateTimeField(null=True, blank=True, verbose_name="Dernière connexion")
    connection_error = models.TextField(blank=True, verbose_name="Erreur de connexion")

    class Meta:
        db_table = 'analytics_network_devices'
        ordering = ['site', 'name']
        verbose_name = "Appareil réseau"
        verbose_name_plural = "Appareils réseau"
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['site', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.ip_address})"


# ============================================================================
# 5. LIEN DE TOPOLOGIE (TopologyLink)
# ============================================================================

class TopologyLink(BaseModel):
    """Connexion entre deux appareils réseau (représente la topologie du réseau)."""
    
    class LinkType(models.TextChoices):
        BACKBONE = 'backbone', 'Backbone'
        DISTRIBUTION = 'distribution', 'Distribution'
        ACCESS = 'access', 'Accès'
        INTERNAL = 'internal', 'Interne'

    source_device = models.ForeignKey(
        NetworkDevice, on_delete=models.CASCADE, related_name='links_from',
        verbose_name="Appareil source"
    )
    source_interface = models.CharField(max_length=50, verbose_name="Interface source")
    
    destination_device = models.ForeignKey(
        NetworkDevice, on_delete=models.CASCADE, related_name='links_to',
        verbose_name="Appareil destination"
    )
    destination_interface = models.CharField(max_length=50, verbose_name="Interface destination")
    
    link_type = models.CharField(max_length=20, choices=LinkType.choices, default=LinkType.BACKBONE, verbose_name="Type")
    bandwidth_mbps = models.FloatField(validators=[MinValueValidator(0)], verbose_name="Bande passante (Mbps)")
    
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Actif")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        db_table = 'analytics_topology_links'
        ordering = ['source_device', 'destination_device']
        verbose_name = "Lien de topologie"
        verbose_name_plural = "Liens de topologie"
        constraints = [
            models.UniqueConstraint(
                fields=['source_device', 'source_interface', 'destination_device', 'destination_interface'],
                name='unique_topology_link'
            )
        ]

    def __str__(self):
        return f"{self.source_device.name}:{self.source_interface} → {self.destination_device.name}:{self.destination_interface}"


# ============================================================================
# 6. SNAPSHOT DE MÉTRIQUES SSH (SSHMetricsSnapshot)
# ============================================================================

class SSHMetricsSnapshot(BaseModel):
    """
    Snapshot de métriques collectées via SSH d'un appareil réseau.
    Données brutes avant agrégation dans KPIHistory.
    """
    
    # Appareil source
    device = models.ForeignKey(
        NetworkDevice, on_delete=models.CASCADE, related_name='ssh_metrics',
        verbose_name="Appareil"
    )
    timestamp = models.DateTimeField(db_index=True, verbose_name="Horodatage")
    
    # CPU & Mémoire
    cpu_usage_pct = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Utilisation CPU (%)"
    )
    memory_usage_pct = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Utilisation mémoire (%)"
    )
    memory_available_mb = models.IntegerField(null=True, blank=True, verbose_name="Mémoire disponible (MB)")
    
    # Thermique
    temperature_c = models.FloatField(null=True, blank=True, verbose_name="Température (°C)")
    temperature_threshold_c = models.FloatField(null=True, blank=True, verbose_name="Seuil température (°C)")
    
    # Optique (pour OLT)
    optical_rx_power_dbm = models.FloatField(null=True, blank=True, verbose_name="Puissance RX (dBm)")
    optical_tx_power_dbm = models.FloatField(null=True, blank=True, verbose_name="Puissance TX (dBm)")
    
    # État du système
    uptime_seconds = models.BigIntegerField(null=True, blank=True, verbose_name="Uptime (secondes)")
    process_count = models.IntegerField(null=True, blank=True, verbose_name="Nombre de processus")
    
    # Interface réseau
    active_connections = models.IntegerField(null=True, blank=True, verbose_name="Connexions actives")
    
    # Métadonnées
    is_anomaly = models.BooleanField(default=False, db_index=True, verbose_name="Anomalie détectée")
    collection_duration_ms = models.IntegerField(null=True, blank=True, verbose_name="Durée collecte (ms)")

    class Meta:
        db_table = 'analytics_ssh_metrics_snapshots'
        ordering = ['-timestamp']
        verbose_name = "Snapshot métriques SSH"
        verbose_name_plural = "Snapshots métriques SSH"
        indexes = [
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['timestamp', 'is_anomaly']),
        ]

    def __str__(self):
        return f"{self.device.name} @ {self.timestamp} - CPU: {self.cpu_usage_pct}%"


# ============================================================================
# 7. TRAFIC RÉSEAU (NetworkTraffic)
# ============================================================================

class NetworkTraffic(BaseModel):
    """
    Métriques de trafic brutes collectées par interface ou lien.
    Données source pour les graphiques de trafic.
    """
    
    # Source - Interface OU Lien
    interface = models.ForeignKey(
        NetworkInterface, on_delete=models.CASCADE, null=True, blank=True,
        related_name='traffic_metrics', verbose_name="Interface"
    )
    fiber_link = models.ForeignKey(
        FibreLink, on_delete=models.CASCADE, null=True, blank=True,
        related_name='traffic_metrics', verbose_name="Lien fibre"
    )
    
    timestamp = models.DateTimeField(db_index=True, verbose_name="Horodatage")
    
    # Trafic entrant/sortant (en bytes)
    bytes_in = models.BigIntegerField(default=0, verbose_name="Bytes reçus")
    bytes_out = models.BigIntegerField(default=0, verbose_name="Bytes envoyés")
    
    # Paquets
    packets_in = models.BigIntegerField(default=0, verbose_name="Paquets reçus")
    packets_out = models.BigIntegerField(default=0, verbose_name="Paquets envoyés")
    
    # Erreurs
    errors_in = models.IntegerField(default=0, verbose_name="Erreurs réception")
    errors_out = models.IntegerField(default=0, verbose_name="Erreurs émission")
    dropped_packets = models.IntegerField(default=0, verbose_name="Paquets perdus")
    
    # Débit calculé
    throughput_mbps = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Débit (Mbps)"
    )
    utilization_pct = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Utilisation (%)"
    )
    
    # Détection d'anomalie
    is_congested = models.BooleanField(default=False, verbose_name="Congestionné")
    is_anomaly = models.BooleanField(default=False, db_index=True, verbose_name="Anomalie")

    class Meta:
        db_table = 'analytics_network_traffic'
        ordering = ['-timestamp']
        verbose_name = "Trafic réseau"
        verbose_name_plural = "Trafic réseau"
        indexes = [
            models.Index(fields=['timestamp', 'is_anomaly']),
            models.Index(fields=['interface', '-timestamp']),
            models.Index(fields=['fiber_link', '-timestamp']),
        ]

    def __str__(self):
        source = self.interface.name if self.interface else self.fiber_link.name
        return f"{source} @ {self.timestamp} - {self.throughput_mbps:.2f} Mbps"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.interface and not self.fiber_link:
            raise ValidationError("Une interface OU un lien fibre doit être spécifié.")
        if self.interface and self.fiber_link:
            raise ValidationError("Spécifier soit une interface, soit un lien fibre, pas les deux.")
