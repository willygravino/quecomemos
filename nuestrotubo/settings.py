# settings.py
from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Seguridad / modo ---
SECRET_KEY = os.environ.get('SECRET_KEY', '!!!-dev-only-!!!')
# DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

DEBUG=True

# Dominio público que Railway suele exponer
RAILWAY_PUBLIC_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()

# Hosts permitidos
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    ",".join(filter(None, [
        "localhost",
        "127.0.0.1",
        ".up.railway.app",
        RAILWAY_PUBLIC_DOMAIN,
    ]))
).split(",")

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CSRF trusted origins (solo si tenemos el dominio exacto)
CSRF_TRUSTED_ORIGINS = []
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_PUBLIC_DOMAIN}")

# No fijar cookie domains a menos que sea necesario para multi-subdominios
# CSRF_COOKIE_DOMAIN = '.railway.app'
# SESSION_COOKIE_DOMAIN = '.railway.app'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'AdminVideos',
    # 'widget_tweaks',  # agrega si realmente lo usás en templates
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # justo después de SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# ⚠️ Elimina cualquier MIDDLEWARE.insert(...) extra

ROOT_URLCONF = 'nuestrotubo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Si usás carpeta templates/ a nivel proyecto, descomentá:
        # 'DIRS': [BASE_DIR / 'templates'],
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

# --- Base de datos ---
# Producción: Railway pasa DATABASE_URL (suele incluir sslmode=require)
# Local: podés usar ?sslmode=disable en tu DATABASE_URL local
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'postgres://guillermo:@localhost:5432/quecomemos_local'),
        conn_max_age=600
        # sin ssl_require=True aquí, dejamos que lo decida la URL (Railway suele ponerlo)
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'      # o 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'  # si preferís UTC, dejá 'UTC'
USE_I18N = True
USE_TZ = True

# --- Estáticos ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')



# WhiteNoise con manifest (recomendado). Requiere collectstatic.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = str(BASE_DIR / 'media')
MEDIA_URL = '/media/'

LOGIN_URL = "index"  # o "login" según tus URLs
