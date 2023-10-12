from datetime import datetime, timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_tracker.models import CeleryTask

import logging
import pytz

from .models import Follows
from horse_points.models import HorsePoint

@receiver(post_save, sender=Follows)
def associate_horsepoint(sender, instance, created, **kwargs):
    force_run = kwargs.get('force_run', False)
    if created==True or force_run:
        if instance.horse is not None:
            horse_point, _ = HorsePoint.objects.get_or_create(external_id=instance.horse, defaults={'points':0,'count':0})
            instance.horse_point = horse_point
            instance.save()

     


        