"""
Django settings for excel_extractor project.
"""

import os
from pathlib import Path
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

from dotenv import load_dotenv
load_dotenv()

AUTH_USER_MODEL = 'extractor.Usuario'

# ============ VARIABLES DE ENTORNO ============
# Definir DEBUG primero
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# SECRET_KEY
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-7_&y#o%h#g#_c!b6z^w8m)0+7o8xr5i@%$k!*&p)q+@v#h$4s@9'
    else:
        raise ValueError("❌ SECRET_KEY no configurada en variables de entorno")

# ============ HOSTS Y CSRF CONFIG ============
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app',
    '.up.railway.app',
]

RAILWAY_PUBLIC_DOMAIN = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)

env_hosts = os.environ.get('ALLOWED_HOSTS')
if env_hosts:
    ALLOWED_HOSTS.extend(env_hosts.split(','))

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.railway.app',
    'https://*.up.railway.app',
]

if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append('https://' + RAILWAY_PUBLIC_DOMAIN)

# ============ PROXY CONFIG ============
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ============ COOKIES SEGURAS ============
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SAMESITE = 'Lax'

# ============ HEADERS DE SEGURIDAD BÁSICOS ============
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ============ CONFIGURACIÓN DE AUTENTICACIÓN ============
LOGIN_URL = 'extractor:login'
LOGIN_REDIRECT_URL = 'extractor:upload_excel'
LOGOUT_REDIRECT_URL = 'extractor:login'

# ============ APLICACIONES ============
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'compressor',
    'extractor',
    'ia_agent',
    'cloudinary',
    'cloudinary_storage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'excel_extractor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'extractor/templates'),
            os.path.join(BASE_DIR, 'templates'),            
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
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
            ssl_require=True
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============ VALIDACIÓN ============
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============ INTERNACIONALIZACIÓN ============
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# ============ ARCHIVOS ESTÁTICOS - MODIFICADO ============
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 🔴 IMPORTANTE: Agregar todas las carpetas donde están tus archivos estáticos
if DEBUG:
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),              # Carpeta static raíz
        os.path.join(BASE_DIR, 'extractor', 'static'), # JS de extractor
        os.path.join(BASE_DIR, 'ia_agent', 'static'),  # JS de ia_agent
    ]

# ============ MEDIA FILES ============
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JIRA_CONFIG = {
    'URL': 'https://buroidentidaddigital.atlassian.net',
    'PROJECT_KEY': 'QA01',
    'EMAIL': os.environ.get('JIRA_EMAIL', ''),
    'API_TOKEN': os.environ.get('JIRA_API_TOKEN', ''),
    'ISSUE_TYPE': 'Task',
}

print("=== VERIFICANDO VARIABLES JIRA ===")
print(f"JIRA_EMAIL: {os.environ.get('JIRA_EMAIL', 'NO CONFIGURADO')}")
print(f"JIRA_API_TOKEN: {'CONFIGURADO' if os.environ.get('JIRA_API_TOKEN') else 'NO CONFIGURADO'}")
print("================================")

SOLICITUD_COOLDOWN_MINUTOS = 5  
SOLICITUD_COOLDOWN_SEGUNDOS = SOLICITUD_COOLDOWN_MINUTOS * 60

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET'],
    secure=True
)

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ============ CONFIGURACIONES DE SEGURIDAD ADICIONALES ============
SESSION_COOKIE_AGE = 1800  # 30 minutos
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

MAX_UPLOAD_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
DATA_UPLOAD_MAX_NUMBER_FILES = 10

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '[%(asctime)s] %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'formatter': 'security',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}


COMPRESS_ENABLED = not DEBUG  # Solo en producción
COMPRESS_OFFLINE = not DEBUG   # Compilar offline en producción
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',  # Minifica JS
]
COMPRESS_CSS_FILTERS = [
    'compressor.filters.cssmin.CSSMinFilter',  # Minifica CSS
]
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_OUTPUT_DIR = 'CACHE'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',  # 🔴 Agregar esto
]

# Crear directorio de logs
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)