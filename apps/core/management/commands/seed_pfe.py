from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

# Import de tes modèles
from apps.equipements.models import Vendor, Gouvernorat, Site, DeviceType, OLT
from apps.analytics.models import KPIHistory
from apps.bfd_monitor.models import BFDSession

class Command(BaseCommand):
    help = 'Remplissage automatique de la base de données'

    def handle(self, *args, **options):
        self.stdout.write("⏳ Début de l'opération...")
        
        # 1. On crée les bases
        v, _ = Vendor.objects.get_or_create(name="Huawei")
        g, _ = Gouvernorat.objects.get_or_create(nom="Tunis", code="21")
        s, _ = Site.objects.get_or_create(name="Ariana Central", gouvernorat=g)
        dt, _ = DeviceType.objects.get_or_create(model="MA5800", vendor=v)
        
        # 2. On crée l'OLT (On a ajouté vendor=v ici !)
        olt, _ = OLT.objects.get_or_create(
            hostname="OLT-ARI-01",
            defaults={
                'vendor': v,  # <-- C'était ça le problème !
                'site': s, 
                'device_type': dt, 
                'status': 'active', 
                'ip_address': '10.10.10.1'
            }
        )

        # 3. On génère 7 jours de KPIs
        now = timezone.now()
        for i in range(7):
            KPIHistory.objects.get_or_create(
                olt=olt, 
                period='day', 
                timestamp=now - timedelta(days=i),
                defaults={
                    'total_onts': 100, 
                    'online_onts': random.randint(85, 98),
                    'avg_cpu_usage': random.uniform(10, 30)
                }
            )

        self.stdout.write(self.style.SUCCESS("✅ C'est fini ! OLT créé et KPIs générés."))
        