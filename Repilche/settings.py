"""
Django settings for Repilche project.
ESETP N.° 724 - Trelew, Chubut, Argentina
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# BASE DIR y carga de variables de entorno
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# SEGURIDAD
# ---------------------------------------------------------------------------
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "SECRET_KEY must be set in the environment when DEBUG is False."
        )
    SECRET_KEY = "django-insecure-repilche-development-only-key"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1, repilche-backend.onrender.com").split(",")
    if h.strip()
]
if DEBUG and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# APLICACIONES
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  
    "django_filters",
    "drf_spectacular",
    # Locales
    "core",
    "api",
    "Repilche",  
]

# ---------------------------------------------------------------------------
# MIDDLEWARE
# CorsMiddleware debe ir primero, WhiteNoise justo después de Security
# ---------------------------------------------------------------------------
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
]

# ---------------------------------------------------------------------------
# URLS y TEMPLATES
# ---------------------------------------------------------------------------
ROOT_URLCONF = "Repilche.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Repilche.wsgi.application"

# ---------------------------------------------------------------------------
# BASE DE DATOS
# Lee DATABASE_URL del .env.
# - Con URL de Supabase  → PostgreSQL
# - Sin URL              → SQLite local (fallback para desarrollo rápido)
# ---------------------------------------------------------------------------
_db_url = os.getenv("DATABASE_URL")
_is_testing = "test" in sys.argv or os.getenv("USE_SQLITE", "").lower() in ("true", "1")

if _db_url and not _is_testing:
    DATABASES = {
        "default": dj_database_url.parse(
            _db_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------------
# USUARIO PERSONALIZADO  ← Ruta Crítica: debe definirse antes de migrar
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "core.CustomUser"

# ---------------------------------------------------------------------------
# VALIDACIÓN DE CONTRASEÑAS
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ---------------------------------------------------------------------------
# INTERNACIONALIZACIÓN
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# ARCHIVOS ESTÁTICOS Y MEDIA
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CORS — permite peticiones desde el frontend Vite en desarrollo y producción
# ---------------------------------------------------------------------------
from corsheaders.defaults import default_headers

_cors_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
_cors_defaults = [
    "https://repilche.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
CORS_ALLOWED_ORIGINS = list(
    dict.fromkeys(
        [o.strip() for o in _cors_env.split(",") if o.strip()] + _cors_defaults
    )
)
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = list(
    dict.fromkeys(
        list(default_headers) + [
            "authorization",
            "content-type",
            "accept",
        ]
    )
)

# ---------------------------------------------------------------------------
# DJANGO REST FRAMEWORK
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
}

# ---------------------------------------------------------------------------
# SIMPLE JWT
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# DRF-SPECTACULAR (OpenAPI / Swagger en /api/docs/)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "REPILCHE API",
    "DESCRIPTION": (
        "API REST de la plataforma Repilche — moda circular de segunda mano. "
        "ESETP N.° 724, Trelew, Chubut, Argentina."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE NEGOCIO — Cuenta oficial centralizada de custodia Repilche
# ---------------------------------------------------------------------------
REPILCHE_ALIAS_PAGO = os.getenv("REPILCHE_ALIAS_PAGO", "repilche.oficial.mp")
REPILCHE_TITULAR_PAGO = os.getenv("REPILCHE_TITULAR_PAGO", "Repilche Moda Circular")
REPILCHE_CBU_CVU = os.getenv("REPILCHE_CBU_CVU", "0000003100012345678901")
