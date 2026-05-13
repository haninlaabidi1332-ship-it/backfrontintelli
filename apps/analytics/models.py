from django.db import models
from apps.core.models import BaseModel
from apps.equipements.models import OLT

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
