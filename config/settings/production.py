"""
Production settings for IntelliOLT – AI-Powered Fiber Network Supervision Platform.
Overrides base.py for production deployment.
"""

from .base import *  # noqa

DEBUG = False

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000   # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

# Logging - enhanced for production (errors only, with rotation)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file_error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/error.log",  # noqa
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "file_info": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/info.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["file_error", "console"],
        "level": "ERROR",
    },
    "loggers": {
        "django": {
            "handlers": ["file_error"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {  # Custom apps logging
            "handlers": ["file_info", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Cache: use Redis in production (already defined in base.py, ensure Redis is configured)
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.redis.RedisCache",
#         "LOCATION": env("REDIS_URL"),
#         "KEY_PREFIX": "intelliolt_prod",
#         "TIMEOUT": 300,
#     }
# }

# Static files storage for production (Whitenoise already set in base)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Email backend for production (use SMTP with TLS)
# Ensure EMAIL_* variables are set in .env
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True

# CSRF trusted origins (add your production domain)
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "https://intelliolt.com",
    "https://www.intelliolt.com",
])

# Security: set ALLOWED_HOSTS strictly in .env for production
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Session engine (use db for production, or cache if Redis is robust)
SESSION_ENGINE = "django.contrib.sessions.backends.db"