"""
Development settings for IntelliOLT – AI-Powered Fiber Network Supervision Platform.
Overrides base.py for local development.
"""

from .base import *  # noqa

DEBUG = True

# Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa
INTERNAL_IPS = ["127.0.0.1"]

# Database: you can use SQLite for faster local dev (optional)
# By default, it inherits PostgreSQL from base.py.
# Uncomment the block below to use SQLite instead.
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

# Logging configuration for development
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
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose" if DEBUG else "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps": {  # Log all custom apps
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Optional: Disable SSL/security for local development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Email backend for development (print to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Cache backend for development (local memory)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Celery backend: use in-memory for dev (no Redis required)
# If you want to test Celery locally with Redis, keep base.py settings.
# Otherwise, uncomment below to run tasks synchronously:
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_BROKER_URL = "memory://"