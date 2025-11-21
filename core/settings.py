from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ SEGURIDAD CRÍTICA CORREGIDA
import secrets
import sys

# SECRET KEY SEGURO
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if 'test' in sys.argv:
        SECRET_KEY = 'django-insecure-test-only'
    else:
        # Generar secret key seguro si no existe
        SECRET_KEY = 'django-insecure-' + secrets.token_urlsafe(50)
        print("WARNING: Using generated SECRET_KEY. Set DJANGO_SECRET_KEY environment variable for production!")

# CONFIGURACIÓN SEGURA POR AMBIENTE
if 'test' in sys.argv:
    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
elif os.getenv('DJANGO_ENV') == 'production':
    DEBUG = False
    ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]
    if not ALLOWED_HOSTS:
        raise ValueError("ALLOWED_HOSTS must be set in production environment")
else:
    DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'yes')
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '127.0.0.1:8000']

# ========================
#  APLICACIONES
# ========================
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Import-Export para carga masiva
    'import_export',

    # Apps locales
    'projects',
    'tasks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ✅ CONFIGURACIONES DE SEGURIDAD
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ✅ CONFIGURACIÓN SEGURA DE SESIONES
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 hora

# ✅ CONFIGURACIÓN SEGURA DE CSRF
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_TRUSTED_ORIGINS = ALLOWED_HOSTS if not DEBUG else []

# ✅ CONFIGURACIÓN DE REFERRER POLICY
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'projects/templates'),  # ← AGREGAR ESTA LÍNEA
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'projects.context_processors.projects_nav',
            ],
        },
    },
]
WSGI_APPLICATION = 'core.wsgi.application'

# ========================
#  BASE DE DATOS - POSTGRESQL
# ========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'eyl_db',
        'USER': 'postgres',
        'PASSWORD': 'Admin123456',  # ⚠️ CAMBIA ESTA CONTRASEÑA POR LA QUE USASTE EN ESTA LAPTOP
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# ========================
#  VALIDACIÓN PASSWORD
# ========================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# ========================
#  INTERNACIONALIZACIÓN
# ========================
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# ========================
#  STATIC & MEDIA
# ========================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ✅ LOGGING DE SEGURIDAD
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
        'standard': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'security',
        },
        'general_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'standard',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'projects': {
            'handlers': ['general_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['general_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# ✅ CREAR DIRECTORIO DE LOGS SI NO EXISTE
logs_dir = BASE_DIR / 'logs'
if not logs_dir.exists():
    os.makedirs(logs_dir, exist_ok=True)

# ========================
#  CONFIGURACIÓN POPPLER & TESSERACT
# ========================

# Ruta de Poppler - CORREGIR PARA ESTA LAPTOP
POPPLER_PATH = r'C:\Users\zareth.oliva\Desktop\poppler-25.07.0\Library\bin'

# Ruta de Tesseract
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Verificar que las rutas existen
import os
if os.path.exists(POPPLER_PATH):
    print(f"[OK] Poppler encontrado en: {POPPLER_PATH}")
else:
    print(f"[WARN] Poppler no encontrado - PDFs escaneados no podran procesarse")
    print(f"   Verificar ruta: {POPPLER_PATH}")

if os.path.exists(TESSERACT_CMD):
    print(f"[OK] Tesseract configurado")
else:
    print(f"[WARN] Tesseract no encontrado - OCR no funcionara")