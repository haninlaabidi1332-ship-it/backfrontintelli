"""
IntelliOLT - URLs principales de l'API
Version intégrant toutes les applications : core, users, equipements, snmp_collector, 
bfd_monitor, alerting, ai_engine, analytics, eve_ng
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Administration
    path('admin/', admin.site.urls),

    # Authentification JWT
    path('api/auth/jwt/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/jwt/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Documentation API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Applications existantes
    path('api/users/', include('apps.users.urls')),
    path('api/equipements/', include('apps.equipements.urls')),
    path('api/snmp/', include('apps.snmp_collector.urls')),      # métriques SNMP
    path('api/bfd/', include('apps.bfd_monitor.urls')),          # sessions BFD
    path('api/alerting/', include('apps.alerting.urls')),        # alertes et règles
    path('api/ai/', include('apps.ai_engine.urls')),             # anomalies, prédictions
    path('api/analytics/', include('apps.analytics.urls')),      # KPIs, rapports
    path('api/eve-ng/', include('apps.eve_ng.urls')),            # labs virtuel
]

# Débogage et fichiers statiques en mode DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
