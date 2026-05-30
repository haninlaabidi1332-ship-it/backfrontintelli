"""
Base settings for IntelliOLT – AI-Powered Fiber Network Supervision Platform.
"""

import os
from pathlib import Path
from datetime import timedelta
from celery.schedules import crontab
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY", default="django-insecure-42$a^d$1rh(zc%&7t7nk((1499w3+6n8008-3bjqc5c+j*!ic!")
DEBUG = env("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
SIMULATION_MODE = env.bool("SIMULATION_MODE", default=False)

# Application definition
DJANGO_APPS = [
    "jazzmin",  # must be before django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'import_export',
    'django_extensions',
    'channels',
    'django_celery_beat',
    'django_celery_results',
    'drf_spectacular',
]

LOCAL_APPS = [
    'apps.core',
    'apps.users',
    'apps.equipements',      # OLT, ONT, liens fibre
    'apps.snmp_collector',   # SNMP polling, métriques
    'apps.bfd_monitor',      # Sessions BFD
    'apps.ai_engine',        # Anomalies, prédictions
    'apps.alerting',         # Règles, alertes, notifications
    'apps.analytics',        # KPIs, dashboards
    'apps.eve_ng',           # Intégration EVE-NG (optionnel)
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database – PostgreSQL standard (pas de PostGIS)
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": env("DB_NAME", default="intelliolt_db"),
        "USER": env("DB_USER", default="intelliolt_admin"),
        "PASSWORD": env("DB_PASSWORD", default="123456"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    },
}

# Cache with Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
        'KEY_PREFIX': 'intelliolt',
        'TIMEOUT': 300,
    },
}

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.users.authentication.EmailAuthBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Tunis"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "10/minute",
    },
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "ALLOWED_VERSIONS": ['v1', 'v2'],
    "DEFAULT_VERSION": 'v2',
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("ACCESS_TOKEN_LIFETIME_MINUTES", default=60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("REFRESH_TOKEN_LIFETIME_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    # Commenté car le sérialiseur n'existe pas → utilisation du défaut
    # 'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.CustomTokenObtainSerializer',
}

# CORS
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
])
CORS_ALLOW_CREDENTIALS = True

# Channels / WebSockets
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {"hosts": [('127.0.0.1', 6379)]},
    },
}
if DEBUG:
    CHANNEL_LAYERS = {
        'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'},
    }

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', True)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'IntelliOLT <noreply@intelliolt.tn>')

# Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'django-db')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 20 * 60

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Tâches planifiées (à adapter selon vos apps)
CELERY_BEAT_SCHEDULE = {
    # SNMP polling — every 60 s
    'collect-snmp-every-60s': {
        'task': 'snmp.collect_all_olts',
        'schedule': 60.0,
    },
    # BFD polling — every 30 s
    'check-bfd-every-30s': {
        'task': 'bfd.poll_all_sessions',
        'schedule': 30.0,
    },
    # AI anomaly detection — every 5 min
    'run-anomaly-detection-every-5m': {
        'task': 'ai.detect_all_anomalies',
        'schedule': 300.0,
    },
    # Alert rule evaluation — every 60 s
    'evaluate-alert-rules-every-minute': {
        'task': 'alerting.evaluate_all_rules',
        'schedule': 60.0,
    },
    # KPI aggregation
    'aggregate-kpi-hourly': {
        'task': 'analytics.aggregate_kpi',
        'schedule': 3600.0,
        'kwargs': {'period': 'hour'},
    },
    'aggregate-kpi-daily': {
        'task': 'analytics.aggregate_kpi',
        'schedule': crontab(hour=1, minute=0),
        'kwargs': {'period': 'day'},
    },
    # Network traffic collection — every 5 min
    'collect-network-traffic-every-5m': {
        'task': 'analytics.collect_all_network_traffic',
        'schedule': 300.0,
    },
    # Analytics anomaly flagging — every 10 min
    'detect-analytics-anomalies-every-10m': {
        'task': 'analytics.detect_anomalies',
        'schedule': 600.0,
    },
    # Purge MetricHistory older than 90 days — daily at 02:00
    'purge-old-metrics-daily': {
        'task': 'snmp.purge_old_metrics',
        'schedule': crontab(hour=2, minute=0),
    },
}

# API Documentation
SPECTACULAR_SETTINGS = {
    "TITLE": "IntelliOLT API",
    "DESCRIPTION": "API d'IntelliOLT – Supervision OLT avec IA",
    "VERSION": "2.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}

# Jazzmin
try:
    from .jazzmin_settings import *
except ImportError:
    JAZZMIN_SETTINGS = {
        "site_title": "IntelliOLT Admin",
        "site_header": "IntelliOLT",
        "site_brand": "IntelliOLT",
        "welcome_sign": "Bienvenue sur IntelliOLT",
        "copyright": "IntelliOLT",
    }

# Fichiers
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Sécurité
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400
SESSION_SAVE_EVERY_REQUEST = True

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
])

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
BACKEND_URL = env("BACKEND_URL", default="http://localhost:8000")

SITE_NAME = "IntelliOLT - Supervision OLT avec IA"
SITE_DESCRIPTION = "Plateforme intelligente de supervision d'équipements OLT"
CONTACT_EMAIL = env("CONTACT_EMAIL", default="contact@intelliolt.tn")
SUPPORT_EMAIL = env("SUPPORT_EMAIL", default="support@intelliolt.tn")

# AI / Ollama (local LLM — primary, offline)
OLLAMA_HOST = env("OLLAMA_HOST", default="http://localhost:11434")
OLLAMA_MODEL = env("OLLAMA_MODEL", default="llama3.2:3b")

# AI / Grok (xAI cloud — fallback, optional)
GROK_API_KEY = env("GROK_API_KEY", default="")
GROK_API_ENDPOINT = env("GROK_API_ENDPOINT", default="https://api.x.ai/v1/chat/completions")
GROK_MODEL = env("GROK_MODEL", default="grok-4.20-reasoning")
GROK_TIMEOUT = int(env("GROK_TIMEOUT", default=30))

# EVE-NG (optionnel)
EVE_NG_URL = os.environ.get('EVE_NG_URL', 'http://localhost/api')
EVE_NG_USER = os.environ.get('EVE_NG_USER', 'admin')
EVE_NG_PASS = os.environ.get('EVE_NG_PASS', 'eve')