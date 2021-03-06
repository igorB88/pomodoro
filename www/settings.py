"""
Django settings for pomodoro project.

Generated by 'django-admin startproject' using Django 1.9.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.environ.get('SERVER', 'dev')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '#ucf4j=^&8mcpnvswe3i(dot(%80@i!^z_o(+12yd1t=*rgjl0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = SERVER != 'prod'

if SERVER == 'dev':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['pomodoro.ferumflex.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
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

ROOT_URLCONF = 'www.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
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

WSGI_APPLICATION = 'www.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pomodoro',
        'USER': 'pomodoro',
        'PASSWORD': 'pomodoro123123',
        'HOST': 'pomodoro-postgres',
        'PORT': '',
        'CONN_MAX_AGE': 60,
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, '..', 'volatile', 'static')

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'static'),
)

MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'persistent', 'media')
MEDIA_URL = '/media/'


########################################################################################################################
# TELEPOT
########################################################################################################################
if SERVER == 'prod':
    TELEGRAM_BOT_TOKEN = '<<changed>>'
    TELEGRAM_BOT_NAME = 'pomodoros_bot'
    TUNNEL_URL = f'https://{ALLOWED_HOSTS[0]}'
else:
    TELEGRAM_BOT_TOKEN = '<<changed>>'
    TELEGRAM_BOT_NAME = 'devpomidoro_bot'
    TUNNEL_URL = 'https://85865308.ngrok.io'

TELEGRAM_ADMIN_USERS = [
    '242433650',   # Anton Pomieschenko
]


########################################################################################################################
# Raven
########################################################################################################################
from raven.transport.requests import RequestsHTTPTransport

INSTALLED_APPS += (
    'raven.contrib.django.raven_compat',
)

RAVEN_CONFIG = {
    'dsn': 'https://39faf06e033441979b3b7d068cc17e78:1241be8d581c4b4b937810ea3338ff65@sentry.ferumflex.com/7',
    'transport': RequestsHTTPTransport,
}


########################################################################################################################
# Admin logs
########################################################################################################################
INSTALLED_APPS += ('admin_logs', )
MIDDLEWARE = ['admin_logs.middleware.LogRequestMiddleware', ] + MIDDLEWARE

ADMIN_LOGS_BACKEND = 'admin_logs.backends.database.DatabaseBackend'


########################################################################################################################
# Django celery
########################################################################################################################
REDIS_LOCATION = "pomodoro-redis:6379"

CELERY_DISABLE_RATE_LIMITS = True

CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'

CELERY_BROKER_URL = 'redis://%s/0' % REDIS_LOCATION

CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_RESULT_PERSISTENT = False
CELERY_TASK_RESULT_EXPIRES = 18000  # 5 hours.
CELERY_TIMEZONE = 'Europe/Kiev'
CELERY_ALWAYS_EAGER = False

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send_emails': {
        'task': 'app.tasks.send_regular_emails_task',
        'schedule': crontab(),
        'args': (),
    }
}

########################################################################################################################
# Cache
########################################################################################################################
CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": REDIS_LOCATION,
        "TIMEOUT": 60 * 60 * 48,
        "OPTIONS": {
            "DB": "0",
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'


########################################################################################################################
# EMAILS
########################################################################################################################
EMAIL_SUBJECT_PREFIX = '[Pomodoro] '
SERVER_EMAIL = 'pomodoro-noreply@ferumflex.com'
DEFAULT_FROM_EMAIL = SERVER_EMAIL


########################################################################################################################
# sparkpost
########################################################################################################################
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sparkpostmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'SMTP_Injection'
EMAIL_HOST_PASSWORD = '<<changed>>'
EMAIL_USE_TLS = True


########################################################################################################################
# Post office
########################################################################################################################
INSTALLED_APPS += ('post_office', )
EMAIL_BACKEND = 'post_office.EmailBackend'


########################################################################################################################
# Django clean up
########################################################################################################################
INSTALLED_APPS += ('django_cleanup', )


########################################################################################################################
# LOGGING
########################################################################################################################
LOGENTRIES_TOKEN = '<<changed>>'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'DEBUG',
        'handlers': ['sentry', 'admin_logs', 'console'],
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'sentry': {
            'level': 'ERROR', # To capture more than ERROR, change to WARNING, INFO, etc.
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'filters': ['require_debug_false'],
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'admin_logs': {
            'level': 'DEBUG',
            'class': 'admin_logs.log.AdminLogHandler',
        },
        'logentries': {
            'level': 'WARNING',
            'token': LOGENTRIES_TOKEN,
            'class': 'logentries.LogentriesHandler',
            'filters': ['require_debug_false'],
        },
    }
}


########################################################################################################################
# Backup
########################################################################################################################
INSTALLED_APPS += (
    'dbbackup',
)

DBBACKUP_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DBBACKUP_FILENAME_TEMPLATE = '{databasename}-{datetime}.{extension}'
DBBACKUP_MEDIA_FILENAME_TEMPLATE = '{databasename}-{datetime}.{extension}'

if SERVER == 'prod':
    location = 'pomodoro-prod'
else:
    location = 'pomodoro-dev'

DBBACKUP_STORAGE_OPTIONS = {
    'access_key': 'AKIAJMPQQ3J63ZYQJC6Q',
    'secret_key': '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',
    'bucket_name': 'ferumflex-backups',
    'default_acl': 'private',
    'location': location,
}

CELERY_BEAT_SCHEDULE['backup'] = {
    'task': 'app.tasks.backup_task',
    'schedule': crontab(minute='0', hour='5'),
    'args': (),
}


########################################################################################################################
# Kibana
########################################################################################################################
# Add the agent to the installed apps
if SERVER == 'prod' or True:
    INSTALLED_APPS = [
        'elasticapm.contrib.django',
    ] + INSTALLED_APPS

    ELASTIC_APM = {
        # Set required service name. 
        # Allowed characters:
        # a-z, A-Z, 0-9, -, _, and space
        'SERVICE_NAME': 'pomodoro',

        # Use if APM Server requires a token
        'SECRET_TOKEN': '',

        # Set custom APM Server URL (
        # default: http://localhost:8200)
        #
        'SERVER_URL': 'http://apm:8200',
    }
    # To send performance metrics, add our tracing middleware:
    MIDDLEWARE = [
        'elasticapm.contrib.django.middleware.TracingMiddleware',
    ] + MIDDLEWARE
