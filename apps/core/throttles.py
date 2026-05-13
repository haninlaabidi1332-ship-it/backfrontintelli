# apps/core/throttles.py
"""
Limitation de débit (throttling) pour IntelliOLT – AI-Powered Fiber Network Supervision Platform
"""
from rest_framework.throttling import UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """
    Limitation pour les pics de requêtes (ex: 100 requêtes par minute).
    Utilisé pour les endpoints API critiques (collecte SNMP, alertes, etc.).
    """
    scope = "burst"
    rate = "100/min"


class SustainedRateThrottle(UserRateThrottle):
    """
    Limitation pour le débit soutenu (ex: 1000 requêtes par heure).
    Utilisé pour les endpoints API standards.
    """
    scope = "sustained"
    rate = "1000/hour"