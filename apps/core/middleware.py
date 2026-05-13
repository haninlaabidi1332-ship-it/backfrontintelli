# apps/core/middleware.py
"""
Middlewares pour IntelliOLT – AI-Powered Fiber Network Supervision Platform
"""
import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("request")


class RequestLoggingMiddleware:
    """Log all incoming requests with duration."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = (time.time() - start) * 1000
        logger.info(
            "%s %s %s %.2fms",
            request.method,
            request.path,
            response.status_code,
            duration,
        )
        return response


class QueryPerformanceMiddleware(MiddlewareMixin):
    """
    Middleware pour monitorer les performances des requêtes
    """
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = (time.time() - request.start_time) * 1000
            
            # Log des requêtes lentes
            if duration > 1000:  # Plus d'1 seconde
                logger.warning(
                    f"Requête lente: {request.method} {request.path} - {duration:.2f}ms"
                )
            
            # Ajouter le temps d'exécution dans les headers
            response['X-Query-Time-Ms'] = int(duration)
        
        return response


class APIRateLimitMiddleware(MiddlewareMixin):
    """
    Middleware pour la limitation de débit API (à implémenter avec Redis)
    """
    
    def process_request(self, request):
        # À implémenter avec Redis pour IntelliOLT
        pass


class IntelliOLTResponseMiddleware(MiddlewareMixin):
    """
    Middleware pour enrichir les réponses API IntelliOLT
    """
    
    def process_response(self, request, response):
        if response.status_code == 200 and response.get('Content-Type') == 'application/json':
            # Ajouter des métadonnées IntelliOLT
            try:
                data = json.loads(response.content)
                if isinstance(data, dict) and 'data' in data:
                    data['_meta'] = {
                        'timestamp': time.time(),
                        'version': '1.0.0',
                        'platform': 'IntelliOLT - AI-Powered Fiber Network Supervision Platform'
                    }
                    response.content = json.dumps(data)
            except:
                pass
        
        return response