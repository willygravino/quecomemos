# settings.py
from pathlib import Path
import dj_database_url
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Seguridad / modo ---
SECRET_KEY = os.environ.get('SECRET_KEY', '!!!-dev-only-!!!')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Dominio público que Railway expone, si existe:
RAILWAY_PUBLIC_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()

# Hosts permitidos: por env o defaults razonables
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    ",".join(filter(None, [
        "localhost",
        "127.0.0.1",
        ".up.railway.app",  # por si no tenés RAILWAY_PUBLIC_DOMAIN
        RAILWAY_PUBLIC_DOMAIN,
    ]))
).split(",")

# CSRF: desde Django 4+ necesita esquema+host exacto
# Si Railway pone un dominio público, lo agregamos.
CSRF_TRUSTED_ORIGINS = []
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")

# Si querés forzar siempre *.up.railway.app (útil cuando el subdom cambia):
# OJO: Django no permite comodines en CSRF_TRUSTED_ORIGINS, debe ser host exacto.
# Podés setearlo por env cuando despliegues.
# CSRF_TRUSTED_ORIGINS += [ "https://tu-subdominio.up.railway.app" ]

# Evitá fijar CSRF_COOKIE_DOMAIN a mano salvo que lo necesites por un multi-subdominio
# CSRF_COOKIE_DOMAIN = '.railway.app'  # <-- mejor comentar si no es imprescindible

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'AdminVideos',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise debe ir inmediatamente después de SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# ❌ Elimina esta línea que tenías al final:
# MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'nuestrotubo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Si tenés templates en BASE_DIR / "templates", descomentá:
        # 'DIRS': [BASE_DIR / "templates"],
        'DIRS': [],
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

WSGI_APPLICATION = 'nuestrotubo.wsgi.application'

# --- Base de datos (SSL + pool) ---
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'postgres://guillermo:@localhost:5432/quecomemos_local'),
        conn_max_age=600,
        ssl_require=True  # en Railway suele ser necesario
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
# ❌ REMOVE: USE_L10N = True  (Django 5 la elimina)
USE_TZ = True

# --- Archivos estáticos ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Storage recomendado para WhiteNoise (hash + compresión)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = str(Path(BASE_DIR) / 'media')
MEDIA_URL = '/media/'

LOGIN_URL = "login"
