from django.db import models
from django.contrib.postgres.indexes import BrinIndex
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import BaseModel, SoftDeleteModel
from apps.equipements.models import OLT, NetworkInterface, GponPort, ONT, Vendor, DeviceType


class SnmpOID(models.Model):
    """Catalogue des OIDs SNMP à collecter."""
    class DataType(models.TextChoices):
        INTEGER = "integer", "Entier"
        COUNTER = "counter", "Compteur"
        GAUGE = "gauge", "Jauge"
        TIMETICKS = "timeticks", "TimeTicks"
        STRING = "string", "Chaîne"
        IP_ADDRESS = "ip_address", "Adresse IP"
        OID = "oid", "OID"

    name = models.CharField(max_length=100, unique=True)
    oid = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, blank=True)
    data_type = models.CharField(max_length=20, choices=DataType.choices, default=DataType.INTEGER)
    scale_factor = models.FloatField(default=1.0, help_text="Multiplicateur appliqué à la valeur brute.")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "snmp_oids"
        ordering = ["name"]
        indexes = [models.Index(fields=["oid"])]

    def __str__(self):
        return f"{self.name} ({self.oid})"


class PollingProfile(models.Model):
    """Profil de polling (timeout, retries, bulk size)."""
    name = models.CharField(max_length=100, unique=True)
    timeout_seconds = models.FloatField(default=2.0, validators=[MinValueValidator(0.5)])
    retries = models.IntegerField(default=2, validators=[MinValueValidator(0), MaxValueValidator(10)])
    bulk_max_repetitions = models.IntegerField(default=10, help_text="Nombre max d'OIDs par requête GETBULK")
    is_default = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "snmp_polling_profiles"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DeviceProfile(models.Model):
    """Profil d'équipement : associe un fabricant/type à une liste d'OIDs."""
    name = models.CharField(max_length=100, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="device_profiles")
    device_type = models.ForeignKey(DeviceType, on_delete=models.CASCADE, related_name="device_profiles")
    sys_object_id = models.CharField(max_length=200, blank=True, help_text="SysObjectID SNMP pour identification auto")
    polling_profile = models.ForeignKey(PollingProfile, on_delete=models.PROTECT, related_name="device_profiles")
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "snmp_device_profiles"
        ordering = ["vendor", "name"]

    def __str__(self):
        return f"{self.vendor.name} - {self.device_type.model} ({self.name})"


class ProfileOID(models.Model):
    """OID appartenant à un profil d'équipement."""
    profile = models.ForeignKey(DeviceProfile, on_delete=models.CASCADE, related_name="profile_oids")
    oid = models.ForeignKey(SnmpOID, on_delete=models.CASCADE, related_name="profile_oids")
    is_critical = models.BooleanField(default=False, help_text="Si True, la collecte de cet OID est obligatoire")
    order = models.IntegerField(default=0, help_text="Ordre de collecte")

    class Meta:
        db_table = "snmp_profile_oids"
        ordering = ["profile", "order"]
        unique_together = ["profile", "oid"]

    def __str__(self):
        return f"{self.profile.name} - {self.oid.name}"


class MetricHistory(BaseModel):
    """Stockage des métriques SNMP avec contexte."""
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name="metrics")
    oid = models.ForeignKey(SnmpOID, on_delete=models.CASCADE)
    interface = models.ForeignKey(NetworkInterface, on_delete=models.CASCADE, null=True, blank=True)
    ont = models.ForeignKey(ONT, on_delete=models.CASCADE, null=True, blank=True)
    gpon_port = models.ForeignKey(GponPort, on_delete=models.CASCADE, null=True, blank=True)

    raw_value = models.TextField(blank=True)
    numeric_value = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "metric_history"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["olt", "oid", "-timestamp"]),
            models.Index(fields=["oid", "-timestamp"]),
            models.Index(fields=["interface", "-timestamp"]),
            models.Index(fields=["ont", "-timestamp"]),
            BrinIndex(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.olt.hostname} / {self.oid.name} = {self.numeric_value} @ {self.timestamp:%H:%M:%S}"


class PollJob(SoftDeleteModel):
    """Suivi avancé des cycles de collecte SNMP."""
    class State(models.TextChoices):
        PENDING = "pending", "En attente"
        RUNNING = "running", "En cours"
        SUCCESS = "success", "Succès"
        PARTIAL = "partial", "Partiel"
        FAILED = "failed", "Échec"

    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name="poll_jobs")
    profile = models.ForeignKey(PollingProfile, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.CharField(max_length=10, choices=State.choices, default=State.PENDING, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    metrics_collected = models.IntegerField(default=0)
    metrics_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    lock_key = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "poll_jobs"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["olt", "-created_at"]), models.Index(fields=["state"])]

    @property
    def duration_ms(self):
        if self.started_at and self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds() * 1000)
        return None

    def __str__(self):
        return f"{self.olt.hostname} - {self.state} @ {self.created_at}"


class SnmpErrorLog(BaseModel):
    """Journal des erreurs SNMP."""
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name="snmp_errors")
    oid = models.ForeignKey(SnmpOID, on_delete=models.SET_NULL, null=True, blank=True)
    error_type = models.CharField(max_length=50, choices=[
        ("timeout", "Timeout"),
        ("no_such_name", "No Such Name"),
        ("auth_failure", "Authentication Failure"),
        ("parse_error", "Parse Error"),
        ("other", "Other"),
    ])
    error_message = models.TextField()
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved = models.BooleanField(default=False)

    class Meta:
        db_table = "snmp_error_logs"
        ordering = ["-occurred_at"]
        indexes = [models.Index(fields=["olt", "occurred_at"])]

    def __str__(self):
        return f"{self.olt.hostname} - {self.error_type} @ {self.occurred_at}"


class SnmpThresholdRule(models.Model):
    """Règle d'alerte basée sur une valeur SNMP seuil."""
    SEVERITY_CHOICES = [("warning", "Warning"), ("critical", "Critical")]
    OPERATOR_CHOICES = [(">", ">"), ("<", "<"), (">=", ">="), ("<=", "<="), ("=", "="), ("!=", "!=")]

    name = models.CharField(max_length=100)
    oid = models.ForeignKey(SnmpOID, on_delete=models.CASCADE, related_name="threshold_rules")
    operator = models.CharField(max_length=2, choices=OPERATOR_CHOICES)
    threshold = models.FloatField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="warning")
    message = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    cooldown_minutes = models.IntegerField(default=10, help_text="Délai avant de ré-émettre la même alerte")

    class Meta:
        db_table = "snmp_threshold_rules"
        ordering = ["severity", "name"]

    def __str__(self):
        return f"{self.name}: {self.oid.name} {self.operator} {self.threshold} ({self.severity})"


class SnmpAlert(BaseModel):
    """Alerte déclenchée par une règle de seuil."""
    STATUS_CHOICES = [("active", "Active"), ("acknowledged", "Acquittée"), ("resolved", "Résolue")]

    rule = models.ForeignKey(SnmpThresholdRule, on_delete=models.CASCADE, related_name="alerts")
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE)
    metric = models.ForeignKey(MetricHistory, on_delete=models.CASCADE, null=True, blank=True)
    value = models.FloatField()
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=SnmpThresholdRule.SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", db_index=True)
    first_seen = models.DateTimeField(auto_now_add=True, db_index=True)
    last_seen = models.DateTimeField(auto_now=True)
    acknowledged_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "snmp_alerts"
        ordering = ["-first_seen"]
        indexes = [models.Index(fields=["olt", "status"]), models.Index(fields=["severity"])]

    def __str__(self):
        return f"{self.severity}: {self.rule.name} on {self.olt.hostname} = {self.value}"