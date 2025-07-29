import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'alamana-jo-production-secret-key-change-this'
DEBUG = False
ALLOWED_HOSTS = ['alamanajo.eu', 'www.alamanajo.eu', '62.169.19.39']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'repairs',
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

ROOT_URLCONF = 'alamana_repair.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'alamana_repair.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'alamanajo_repair.db',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Brussels'
USE_I18N = True
USE_TZ = True

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/alamanajo.eu/static'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files configuration for photo uploads
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/alamanajo.eu/media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login settings
LOGIN_URL = '/alamana-admin/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# HTTPS and security settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = ['https://alamanajo.eu', 'https://www.alamanajo.eu']
USE_X_FORWARDED_HOST = True

# SMS Gateway Settings
SMS_GATEWAY_USERNAME = os.environ.get('SMS_USERNAME', '')
SMS_GATEWAY_PASSWORD = os.environ.get('SMS_PASSWORD', '')
SMS_GATEWAY_URL = 'https://api.sms-gate.app/3rdparty/v1/message'

# Alamana Jo Shop Information
SHOP_NAME = "Alamana Jo"
SHOP_ADDRESS = "Quellinstraat 45, 2018 Antwerpen"
SHOP_PHONE = "+32 (499) 89-0237"
SHOP_EMAIL = "alamanajo@gmail.com"
SHOP_WEBSITE = "www.alamanajo.eu"
SHOP_HOURS = "Mon-Fri 9:00-18:00, Sat 9:00-16:00"

# Storage and Policy Settings
STORAGE_FEE_PER_DAY = 2
STORAGE_FREE_DAYS = 14
ABANDONMENT_MONTHS = 3
DIAGNOSTIC_FEE_MIN = 25
DIAGNOSTIC_FEE_MAX = 50

# File upload settings - INCREASED LIMITS FOR PHOTOS
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52 * 1024 * 1024  # 52MB  
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
FILE_UPLOAD_TEMP_DIR = '/tmp'

# Image processing settings
IMAGE_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per image
IMAGE_MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB total

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 86400
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
