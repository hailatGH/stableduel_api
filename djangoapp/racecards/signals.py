from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_tracker.models import CeleryTask

from .models import Racecard
from games.tasks import start_games, pre_post_notifications

@receiver(post_save, sender=Racecard)
def save_racecard(sender, instance, created, **kwargs):
    
    force_run = kwargs.get('force_run', False)
    if created==False or force_run:
        #check to see if the task has already been created
        if(len(instance.races) > 0 and CeleryTask.objects.filter(task_name='games.tasks.start_games', args='(%s,)' % (instance.id)).count() == 0):
            # Now using adjusted_date since we're handling games that may start on the next day as UTC
            race_date = instance.races[0]['adjusted_date']
            if(type(race_date) == str):
                race_date = datetime.strptime(race_date, '%Y-%m-%d')
                
            start_time = datetime.strptime(instance.races[0]['post_time'], '%I:%M%p')
            eta = datetime.combine(race_date, start_time.time())
            if(eta > datetime.now()):
                start_games.apply_async((instance.id,), eta=eta)
