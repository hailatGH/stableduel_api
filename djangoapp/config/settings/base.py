"""
Base settings to build other settings files upon.
"""
import json
import environ
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from six.moves.urllib import request
# from django.core.management.utils import get_env_variable
ROOT_DIR = environ.Path(__file__) - 3  # (api/config/settings/base.py - 3 = api/)
APPS_DIR = ROOT_DIR

env = environ.Env()


# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env('DJANGO_DEBUG', default='True') == 'True'
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = 'UTC'
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = False

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

if env.get_value("ENV", default="dev") == "dev" :
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": env.get_value("DB_HOST", default="localhost"),
            "NAME": env.get_value("DB_NAME", default="stableduel"),
            "USER": env.get_value("DB_USER"),   
            "PASSWORD": env.get_value("DB_PASSWORD"),
            "PORT": env.get_value("DB_PORT", default="5432"),
        }
    }
else:
    DATABASES = {
        'default': env.db('DATABASE_URL', default='postgres://postgres:password@localhost:5432/stableduel'),
    }

DATABASES['default']['ATOMIC_REQUESTS'] = True

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = 'config.urls'
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'config.wsgi.application'

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize', # Handy template tags
    'django.contrib.admin',
]
THIRD_PARTY_APPS = [
    'crispy_forms',
    'rest_framework',
    'rest_framework_jwt',
    'django_filters',
    'django_celery_tracker',
    'corsheaders',
    'celerybeat_status',
    'uszipcode',
    'drf_yasg',
    'reversion',
    'django_summernote'
]
LOCAL_APPS = [
    'users.apps.UsersAppConfig',
    'stables.apps.StablesAppConfig',
    'games.apps.GamesAppConfig',
    'racecards.apps.RacecardsAppConfig',
    'notifications.apps.NotificationsAppConfig',
    'api.apps.ApiAppConfig',
    'messaging.apps.MessagingAppConfig',
    'stable_points.apps.StablePointsConfig',
    'user_history.apps.UserHistoryConfig',
    'follows.apps.FollowsConfig',
    'horse_points.apps.HorsePointsConfig',
    'wagering.apps.WageringConfig',
    'analytics.apps.AnalyticsConfig'
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {
    'sites': 'contrib.sites.migrations'
}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = 'users.User'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = '/'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = '/login'

DRIP_ACTIVE = True
DRIP_TAGS = ['New Account', 'TEST']
DRIP_ACCOUNT_ID = env('DRIP_ACCOUNT_ID')
DRIP_API_TOKEN = env('DRIP_API_TOKEN')

# Settings for TimeformUS
TIMEFORM_URL = env('TIMEFORM_URL', default='')
TIMEFORM_USERNAME = env('TIMEFORM_USERNAME', default='')
TIMEFORM_PASSWORD = env('TIMEFORM_PASSWORD', default='')

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
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

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR('staticfiles'))
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [
    str(APPS_DIR.path('static')),
]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = env('DJANGO_MEDIA_ROOT', default='/tmp/media')
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        'DIRS': [
            str(APPS_DIR.path('templates')),
        ],
        'OPTIONS': {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            'debug': DEBUG,
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (
    str(APPS_DIR.path('fixtures')),
)

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env(
    'DJANGO_DEFAULT_FROM_EMAIL',
    default='Stable Duel <noreply@stableduel.com>'
)
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = env('DJANGO_SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env('DJANGO_EMAIL_SUBJECT_PREFIX', default='[Stable Duel]')

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = 'admin/'
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [
    ("""Stephen Moyer""", 'stephen.moyer@mmspartner.com'),
]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# Celery
# ------------------------------------------------------------------------------
INSTALLED_APPS += ['taskapp.celery.CeleryAppConfig']
if USE_TZ:
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-timezone
    CELERY_TIMEZONE = TIME_ZONE
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-broker_url
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://redis:6379/0')
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_backend
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-accept_content
CELERY_ACCEPT_CONTENT = ['json']
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-task_serializer
CELERY_TASK_SERIALIZER = 'json'
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_serializer
CELERY_RESULT_SERIALIZER = 'json'
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-time-limit
CELERYD_TASK_TIME_LIMIT = 60 * 60
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-soft-time-limit
# CELERYD_TASK_SOFT_TIME_LIMIT = 60
CELERY_HIJACK_ROOT_LOGGER = False
CELERY_TASK_ALWAYS_EAGER = env("CELERY_TASK_ALWAYS_EAGER", default=False)

# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_ALLOW_REGISTRATION = env.bool('DJANGO_ACCOUNT_ALLOW_REGISTRATION', True)
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_ADAPTER = 'users.adapters.AccountAdapter'
REST_SESSION_LOGIN = False

REST_AUTH_SERIALIZERS = {
    'USER_DETAILS_SERIALIZER': 'users.serializers.CurrentUserSerializer',
}

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PAGINATION_CLASS': 'config.pagination.CustomPagination',
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',
    'PAGE_SIZE': 100,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers' : {
        'parso': {
            'propagate': False,
            }
    }
}

# Adds a way to impersonate other users for the API
SD_DEBUG_TOKEN = env('SD_DEBUG_TOKEN', default=None)
if env('SD_DEBUG_AUTH', default=False):
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
        *REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'],
        'users.auth_backends.DebugAuthentication',
    )

REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_OBJECT_CACHE_KEY_FUNC':
        'rest_framework_extensions.utils.default_object_cache_key_func',
    'DEFAULT_LIST_CACHE_KEY_FUNC':
        'rest_framework_extensions.utils.default_list_cache_key_func',
}

# CACHES
# ------------------------------------------------------------------------------
if env('DJANGO_CACHING_ENABLED', default=True):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env('REDIS_CACHE_URL', default='redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                # Mimicing memcache behavior.
                # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
                'IGNORE_EXCEPTIONS': True,
                'PASSWORD': env('REDIS_AZURE_PASSWORD', default=''),
                'SSL': True,
            }
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# JWT...
# -----------------------------------------------------------------------------
if env('AUTH_ISSUER', default='https://stableduel.auth0.com/'):
    jsonurl = request.urlopen("{}.well-known/jwks.json".format(env('AUTH_ISSUER',
                              default='https://stableduel.auth0.com/')))
    jwks = json.loads(jsonurl.read())
    cert = '-----BEGIN CERTIFICATE-----\n' + jwks['keys'][0]['x5c'][0] + '\n-----END CERTIFICATE-----'

    certificate = load_pem_x509_certificate(str.encode(cert), default_backend())
    publickey = certificate.public_key()
    JWT_AUTH = {
        'JWT_PAYLOAD_GET_USERNAME_HANDLER':
            'users.jwt.jwt_get_username_from_payload_handler',
        'JWT_PUBLIC_KEY': publickey,
        'JWT_ALGORITHM': 'RS256',
        'JWT_AUDIENCE': env('AUTH_AUDIENCE', default='http://localhost:8000'),
        'JWT_ISSUER': env('AUTH_ISSUER', default='https://stableduel.auth0.com/'),
        'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    }

# Misc...
# ------------------------------------------------------------------------------
CORS_ORIGIN_WHITELIST = (
    'localhost:8080',
    'localhost:3000',
)
# CORS Headers
# Only set CORS headers on 'api' endpoints
CORS_URLS_REGEX = r'^/api/.*$'

# Pusher Beams Settings
PUSHERBEAMS_INSTANCE_ID = env('PUSHERBEAMS_INSTANCE_ID', default='')
PUSHERBEAMS_SECRET_KEY = env('PUSHERBEAMS_SECRET_KEY', default='')
PUSHER_APP_ID = env('PUSHER_APP_ID', default='')
PUSHER_APP_KEY = env('PUSHER_APP_KEY', default='')
PUSHER_APP_SECRET = env('PUSHER_APP_SECRET', default='')
PUSHER_APP_CLUSTER = env('PUSHER_APP_CLUSTER', default='us2')

RUNNER_UPDATE_USAGE_INTERVAL = 5  # minutes

# CHRIMS
CHRIMS_BASE_URL = env('CHRIMS_BASE_URL', default=None)
NEW_CHRIMS_BASE_URL = env('NEW_CHRIMS_BASE_URL', default=None)
CHRIMS_SECRET = env('CHRIMS_SECRET', default=None)
CHRIMS_AUDIT = env('CHRIMS_AUDIT', default=None)
CHRIMS_DECRYPT = env('CHRIMS_DECRYPT', default=None)

# AMPLITUDE
AMPLITUDE_URL = env('AMPLITUDE_URL', default=None)
AMPLITUDE_KEY = env('AMPLITUDE_KEY', default=None)

# ROBERTS 
ROBERTS_KEY = env('ROBERTS_KEY', default=None)

#SMS
SMS_SEED_KEY = env.get_value('SMS_SeedKey_KEY', default=None)
SMS_PARTNER_CODE = env.get_value('SMS_PartnerCode', default=None)
SMS_PSSWORD = env.get_value('SMS_Password', default=None)
#ATR
ATR_USER_NAME = env.get_value('ATRusername', default=None)
PASSWORD_ATR = env.get_value('passwordATR', default=None)

# SMS_SeedKey_KEY= get_env_variable('SMS_SeedKey_KEY', default=None)
# SMS_PartnerCode= get_env_variable('SMS_PartnerCode', default=None)
# SMS_Password= get_env_variable('SMS_Password', default=None)
# #ATR
# ATRusername = get_env_variable('ATRusername', default=None)
# passwordATR= get_env_variable('passwordATR', default=None)

# GAMSTOP
GAMSTOP_APIKEY = env.get_value('GAMSTOP_APIKEY', default=None)
GAMSTOP_URL = env.get_value('GAMSTOP_URL', default=None)

# NUVEI
NUVEI_MERCHANT_ID = env.get_value("NUVEI_MERCHANT_ID")
NUVEI_MERCHANT_SITE_ID = env.get_value("NUVEI_MERCHANT_SITE_ID")
NUVEI_SECRET_KEY = env.get_value("NUVEI_SECRET_KEY")
NUVEI_URL = env.get_value("NUVEI_URL")
