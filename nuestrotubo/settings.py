"""
Django settings for nuestrotubo project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path

import dj_database_url
import os
from dotenv import load_dotenv

load_dotenv()  # 👉 Esto carga automáticamente el archivo .env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-ff(ii27o)5bnj*cy5l6bz1hr=hecla%@rxat^zg8g*&6z&e1dx'

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-ff(ii27o)5bnj*cy5l6bz1hr=hecla%@rxat^zg8g*&6z&e1dx')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# DEBUG = False

# DEBUG = os.environ.get('DEBUG', 'False') == 'True'


# ALLOWED_HOSTS = []

ALLOWED_HOSTS = ["127.0.0.1",'.railway.app', 'localhost']


CSRF_TRUSTED_ORIGINS = [
    'https://quecomemos-production.up.railway.app',  # o tu dominio si es otro
]

CSRF_COOKIE_DOMAIN = '.railway.app'

# COMENTADO EN DESARROLLO >>> SESSION_COOKIE_DOMAIN = '.railway.app'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'AdminVideos',
    'widget_tweaks',  # <--- lo añades aquí

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nuestrotubo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
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

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# El código que tienes actualmente está tomando la configuración de la base de datos de una variable de entorno llamada DATABASE_URL. Esta es una buena práctica para entornos de producción, pero para desarrollo local necesitamos configurarlo explícitamente para que apunte a la base de datos que has creado con PostgreSQL en tu máquina.
# DATABASES = {
#     'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
# }


DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'postgres://guillermo:@localhost:5432/quecomemos_local')
    )
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'es-Ar'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

# STATIC_ROOT = str(Path(BASE_DIR) / 'AdminVideos/static')
# STATIC_URL = 'AdminVideos/static/'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Para producción
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = str(Path(BASE_DIR) / 'media')
MEDIA_URL = '/media/'

LOGIN_URL = "login"

