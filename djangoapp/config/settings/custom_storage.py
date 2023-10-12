from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage  # noqa E402


class StaticStorage(S3Boto3Storage):
    default_acl=None
    location = settings.STATICFILES_LOCATION

class MediaStorage(S3Boto3Storage):
    default_acl=None
    location = settings.MEDIAFILES_LOCATION
