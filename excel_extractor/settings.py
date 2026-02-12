"""
Django settings for excel_extractor project.
"""

import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ============ DEBUG TOTAL - TEMPORAL ============
DEBUG = True  # FORZADO A TRUE
SECRET_KEY = 'django-insecure-debug-key-7_&y#o%h#g#_c!b6z^w8m)0+7o8xr5i@%$k!*&p)q+@v#h$4s@9'

# ============ HOSTS - PERMITIR TODO ============
ALLOWED_HOSTS = ['*']  # TEMPORAL - permite cualquier host

# ============ CSRF - DESACTIVADO TEMPORALMENTE ============
CSRF_TRUSTED_ORIGINS = ['http://*', 'https://*']
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SAMESITE = None

# ============ PROXY ============
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ============ APLICACIONES ============
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'extractor',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # Activado pero relajado
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'excel_extractor.urls'

# ============ TEMPLATES - CONFIGURACIÓN ROBUSTA ============
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Path global
        ],
        'APP_DIRS': True,  # Esto busca en extractor/templates/
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            # DEBUG DE TEMPLATES
            'debug': True,
        },
    },
]

WSGI_APPLICATION = 'excel_extractor.wsgi.application'

# ============ BASE DE DATOS ============
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=False  # TEMPORAL - desactivar SSL
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============ LOGGING - VER TODO ============
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.template': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'extractor': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# ============ VALIDACIÓN ============
AUTH_PASSWORD_VALIDATORS = []  # TEMPORAL - sin validaciones

# ============ INTERNACIONALIZACIÓN ============
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# ============ ARCHIVOS ESTÁTICOS ============
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# BÚSQUEDA DE ARCHIVOS ESTÁTICOS
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

if not STATICFILES_DIRS[0].exists():
    STATICFILES_DIRS = []  # No fallar si no existe

# ============ MEDIA FILES ============
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============ DEFAULT AUTO FIELD ============
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============ SEGURIDAD - DESACTIVADA PARA DEBUG ============
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
X_FRAME_OPTIONS = 'ALLOWALL'