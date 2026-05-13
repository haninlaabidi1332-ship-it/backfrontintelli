from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel
from apps.equipements.models import OLT, ONT
from apps.snmp_collector.models import SnmpOID, SnmpThresholdRule
from apps.bfd_monitor.models import BFDThresholdRule
from apps.ai_engine.models import AnomalyDetection

class AlertRule(BaseModel):
    """Règle multi‑source avec déduplication et cooldown."""
    class SourceType(models.TextChoices):
        SNMP = 'snmp', 'SNMP'
        BFD = 'bfd', 'BFD'
        AI = 'ai', 'IA'
        CUSTOM = 'custom', 'Personnalisé'

    name = models.CharField(max_length=100, unique=True)
    source_type = models.CharField(max_length=10, choices=SourceType.choices)
    snmp_rule = models.ForeignKey(SnmpThresholdRule, on_delete=models.CASCADE, null=True, blank=True)
    bfd_rule = models.ForeignKey(BFDThresholdRule, on_delete=models.CASCADE, null=True, blank=True)
    ai_severity_min = models.CharField(max_length=20, blank=True, help_text="Severité minimale IA (low/medium/high/critical)")
    is_active = models.BooleanField(default=True)
    cooldown_minutes = models.IntegerField(default=10, validators=[MinValueValidator(1)])
    message_template = models.TextField(help_text="Template avec variables {olt}, {value}, {severity}, {source}")
    deduplication_window_minutes = models.IntegerField(default=5, help_text="Fenêtre de déduplication (0 = désactivée)")

    class Meta:
        db_table = 'alerting_rules'

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"

class Alert(BaseModel):
    """Alerte générée (dédupliquée)."""
    class Severity(models.TextChoices):
        INFO = 'info', 'Information'
        WARNING = 'warning', 'Avertissement'
        MAJOR = 'major', 'Majeure'
        CRITICAL = 'critical', 'Critique'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ACKNOWLEDGED = 'acknowledged', 'Acquittée'
        RESOLVED = 'resolved', 'Résolue'

    rule = models.ForeignKey(AlertRule, on_delete=models.SET_NULL, null=True, blank=True)
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, null=True, blank=True)
    ont = models.ForeignKey(ONT, on_delete=models.CASCADE, null=True, blank=True)
    source_id = models.CharField(max_length=100, blank=True, db_index=True, help_text="ID dans la source (ex: snmp_alert_id)")
    severity = models.CharField(max_length=10, choices=Severity.choices, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    message = models.TextField()
    value = models.FloatField(null=True, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True, db_index=True)
    last_seen = models.DateTimeField(auto_now=True)
    acknowledged_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'alerting_alerts'
        ordering = ['-first_seen']
        indexes = [
            models.Index(fields=['olt', 'status']),
            models.Index(fields=['severity']),
            models.Index(fields=['source_id', 'rule']),
        ]

    def __str__(self):
        return f"{self.severity}: {self.message[:50]}"

class NotificationChannel(BaseModel):
    """Canal de notification (email, Slack, Teams, webhook)."""
    class ChannelType(models.TextChoices):
        EMAIL = 'email', 'Email'
        SLACK = 'slack', 'Slack'
        TEAMS = 'teams', 'Microsoft Teams'
        WEBHOOK = 'webhook', 'Webhook'

    name = models.CharField(max_length=100, unique=True)
    channel_type = models.CharField(max_length=10, choices=ChannelType.choices)
    configuration = models.JSONField(default=dict, help_text="{'url': '...', 'recipients': [...], 'headers': {...}}")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'alerting_notification_channels'

    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"

class NotificationHistory(BaseModel):
    """Historique des notifications envoyées."""
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='notifications')
    channel = models.ForeignKey(NotificationChannel, on_delete=models.SET_NULL, null=True)
    success = models.BooleanField(default=True)
    response = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'alerting_notification_history'
        ordering = ['-sent_at']
