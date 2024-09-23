from django.db import models
from django.contrib.postgres.fields import JSONField
from racecards.models import Racecard

class VersionRequirement(models.Model):
    ios_latest_version = models.CharField(max_length=200)
    ios_required_version = models.CharField(max_length=200)
    android_latest_version = models.CharField(max_length=200)
    android_required_version = models.CharField(max_length=200)
