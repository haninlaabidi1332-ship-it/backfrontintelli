from django.db import models
from apps.core.models import BaseModel
from apps.equipements.models import OLT, Vendor, DeviceType

class EveNgLab(BaseModel):
    """Laboratoire EVE-NG (version Community)."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    lab_path = models.CharField(max_length=500, help_text="Chemin complet du lab dans EVE-NG (ex: /opt/unetlab/labs/mylab.unl)")
    eve_ng_url = models.CharField(max_length=200, blank=True, help_text="URL spécifique (sinon config globale)")
    is_active = models.BooleanField(default=True)
    last_started_at = models.DateTimeField(null=True, blank=True)
    last_stopped_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'eve_ng_labs'

    def __str__(self):
        return self.name

class EveNgDevice(BaseModel):
    """Nœud virtuel dans un lab."""
    lab = models.ForeignKey(EveNgLab, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=100)
    node_id = models.IntegerField(help_text="ID attribué par EVE-NG")
    olt = models.ForeignKey(OLT, on_delete=models.SET_NULL, null=True, blank=True, help_text="OLT réel associé (optionnel)")
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    device_type = models.ForeignKey(DeviceType, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.CharField(max_length=100, blank=True)
    cpu = models.IntegerField(default=1)
    ram = models.IntegerField(default=1024, help_text="RAM en MB")
    configuration = models.JSONField(default=dict, help_text="Configuration spécifique au nœud")

    class Meta:
        db_table = 'eve_ng_devices'

    def __str__(self):
        return f"{self.lab.name}: {self.name}"

class EveNgLabExecution(BaseModel):
    """Historique d'exécution."""
    lab = models.ForeignKey(EveNgLab, on_delete=models.CASCADE, related_name='executions')
    started_at = models.DateTimeField(auto_now_add=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('running', 'Running'), ('stopped', 'Stopped')])
    logs = models.TextField(blank=True)

    class Meta:
        db_table = 'eve_ng_lab_executions'
        ordering = ['-started_at']
