from datetime import datetime, timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_tracker.models import CeleryTask

import logging
import pytz

from notifications.models import Notification
from stables.models import Stable
from analytics.amplitude_api import amplitude_notification_sent, amplitude_submitted_pick

@receiver(post_save, sender=Notification)
def save_notification(sender, instance, created, **kwargs):
    if created==True:
        amplitude_notification_sent(instance)

@receiver(post_save, sender=Stable)
def save_notification(sender, instance, created, **kwargs):
    amplitude_submitted_pick(instance)
