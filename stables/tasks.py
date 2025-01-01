from celery import shared_task
from celery.decorators import periodic_task
from celery.task.schedules import crontab

from django.db.models import Q, Count
from django.core.cache import cache

from racecards.models import Racecard
from stables.models import Runner, Stable
from stables.notifications import ScratchedNotification

from games.models import Game


@shared_task
def send_scratch_notifications(runner_id, game_id):
    runner = Runner.objects.get(id=runner_id)
    stables = runner.stable_set.filter(~Q(is_valid_at_start=False)).distinct()
    
    for stable in stables:
        user = [stable.user.auth0_id]
        #Create a list with a single user because that's what pusher beams expects
        pn = ScratchedNotification(user, runner, stable)
        pn.send()


@periodic_task(
    run_every=(crontab(minute='*/10')),
    name="runner_update_usage",
    ignore_result=True
)
def runner_update_usage():
    racecards = Racecard.objects.filter(game__in=Game.objects.filter(~Q(game_state=Game.FINISHED))).distinct()
    for racecard in racecards:
        total_stables = Stable.objects.filter(game__in=Game.objects.filter(racecard=racecard)).count()
        cache.set('racecard_{}_total_stables'.format(racecard.id), total_stables, None)

    runners = Runner.objects.filter(racecard__in=racecards).annotate(stable_set_count=Count('stable'))

    for runner in runners:
        cache.set('runner_{}_stable_count'.format(runner.id), runner.stable_set_count, None)
