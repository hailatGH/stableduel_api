from datetime import datetime, timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_tracker.models import CeleryTask
from django.core.cache import cache

import logging
import pytz

from .models import Game, GamePayout
from racecards.serializers import RacecardSerializer
from games.tasks import create_game_update_custom_stats, follow_horses_notification

@receiver(post_save, sender=Game)
def save_game(sender, instance, created, **kwargs):
    force_run = kwargs.get('force_run', False)
    if instance.archived == False:
        create_game_update_custom_stats(instance.id)
    if created==True or force_run:

        #If a Game is created, we should go ahead and update the custom_stats
        #for the Runners.
        #Kick off as a celery task once we actually take live
        
        #Send push notifications that a horse you are following has been entered into a Game
        follow_horses_notification.delay(instance.racecard.id)
     

@receiver(post_save, sender=GamePayout)
def cache_payout(sender, instance, **kwargs):
    print(f"Caching payout for game: {instance.game_id}, rank: {instance.position}, value: {instance.value}")
    key = f'game_payout_{instance.game_id}_rank_{instance.position}'
    cache.set(key, instance.value, None)