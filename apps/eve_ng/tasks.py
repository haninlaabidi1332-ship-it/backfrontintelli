import logging
import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .models import EveNgLab, EveNgDevice, EveNgLabExecution

logger = logging.getLogger(__name__)

def get_eve_ng_session():
    """Authentification auprès d'EVE-NG Community et retour de session."""
    session = requests.Session()
    url = getattr(settings, 'EVE_NG_URL', 'http://localhost')
    user = getattr(settings, 'EVE_NG_USER', 'admin')
    password = getattr(settings, 'EVE_NG_PASS', 'eve')
    # EVE-NG Community API : /api/auth/login
    login_url = f"{url}/api/auth/login"
    try:
        resp = session.post(login_url, json={'username': user, 'password': password}, timeout=10)
        if resp.status_code == 200:
            token = resp.json().get('data', {}).get('token')
            if token:
                session.headers.update({'Authorization': f'Bearer {token}'})
        else:
            logger.error(f"Échec login EVE-NG: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.exception("Erreur connexion EVE-NG")
    return session

@shared_task(name='eve_ng.start_lab')
def start_lab_async(lab_id):
    try:
        lab = EveNgLab.objects.get(id=lab_id)
        session = get_eve_ng_session()
        # URL de démarrage : /api/labs/{lab_path}/start
        start_url = f"{lab.eve_ng_url or settings.EVE_NG_URL}/api/labs/{lab.lab_path}/start"
        resp = session.get(start_url, timeout=30)  # ou POST selon version
        if resp.status_code in (200, 201):
            lab.last_started_at = timezone.now()
            lab.save()
            EveNgLabExecution.objects.create(lab=lab, status='running')
            logger.info(f"Lab {lab.name} démarré avec succès")
        else:
            logger.error(f"Échec démarrage lab {lab.name}: {resp.text}")
    except Exception as e:
        logger.exception(f"Erreur démarrage lab {lab_id}")

@shared_task(name='eve_ng.stop_lab')
def stop_lab_async(lab_id):
    try:
        lab = EveNgLab.objects.get(id=lab_id)
        session = get_eve_ng_session()
        stop_url = f"{lab.eve_ng_url or settings.EVE_NG_URL}/api/labs/{lab.lab_path}/stop"
        resp = session.get(stop_url, timeout=30)
        if resp.status_code in (200, 201):
            lab.last_stopped_at = timezone.now()
            lab.save()
            # Mettre à jour l'exécution la plus récente
            exec_obj = lab.executions.filter(status='running').last()
            if exec_obj:
                exec_obj.status = 'stopped'
                exec_obj.stopped_at = timezone.now()
                exec_obj.save()
            logger.info(f"Lab {lab.name} arrêté")
        else:
            logger.error(f"Échec arrêt lab {lab.name}: {resp.text}")
    except Exception as e:
        logger.exception(f"Erreur arrêt lab {lab_id}")

@shared_task(name='eve_ng.sync_device_config')
def sync_device_config(device_id):
    """
    Synchronise la configuration d'un OLT réel (SNMP, SSH) vers le nœud virtuel EVE-NG.
    À implémenter selon votre méthode (export config, API EVE-NG, etc.)
    """
    try:
        device = EveNgDevice.objects.select_related('olt', 'lab').get(id=device_id)
        if not device.olt:
            logger.warning(f"Device {device.name} sans OLT associé")
            return
        # Exemple : récupérer la config via SNMP ou SSH
        # config_text = fetch_device_config(device.olt)
        # Pousser vers EVE-NG via API
        logger.info(f"Synchronisation config de {device.olt.hostname} vers {device.name}")
    except Exception as e:
        logger.exception(f"Erreur sync device {device_id}")