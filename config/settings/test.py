    """
With these settings, tests run faster.
"""

import warnings
import os
import dotenv
from django.core.cache import CacheKeyWarning

from .base import *  # noqa
from .base import env

env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)+'/../../'), '.env')
if os.path.isfile(env_file):
    dotenv.read_dotenv(env_file)

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = False
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY", default="uaBvtIQVLLpxA9sCtpuIqEY8U3T5PhAhOSnbFGb7ixHu10l2lwrfRi3B2KzBUxrO")
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

USE_DOCKER_POSTGRES = env("USE_DOCKER_POSTGRES", default=True)
if USE_DOCKER_POSTGRES:
    DATABASES = {
        'default': env.db('DATABASE_URL', default='postgres://postgres@postgres/stableduel'),
    }

# Make celery tasks syncronous
CELERY_TASK_ALWAYS_EAGER = True


# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": ""
    }
}
warnings.simplefilter("ignore", CacheKeyWarning)

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # noqa F405
TEMPLATES[0]["OPTIONS"]["loaders"] = [  # noqa F405
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = "localhost"
# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = 1025

DRIP_ACTIVE = True
DRIP_TAGS = ['New Account', 'TEST']

# Your stuff...
# ------------------------------------------------------------------------------
WINDOWS_MNT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)) + '../../api/tests/sample_output')
