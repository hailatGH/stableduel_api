from celery import shared_task
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from datetime import datetime, timedelta
from games.models import Game, GamePayout
from games.notifications import FirstPostNotification
from racecards.models import Racecard
from racecards.tasks import send_race_cancelled_notifications
from racecards.notifications import RaceCanceledNotification
from follows.models import Follows
from follows.notifications import FollowsHorseNotification
from stables.models import calculate_stable_is_valid, calculate_scores_ranks, Runner,Stable
from stables.utils import get_salary
from django.conf import settings
from django.db.models.expressions import RawSQL
from stable_points.models import StablePoint
from notifications.models import Notification
import requests
from django.db.models import Count
from django.core.cache import cache

from wagering.chrims_api import finalize_bets, update_contest, cancel_bet

from racecards.timezones import get_timezone

import logging
import pytz

@shared_task
def start_games(racecard_id):
    games = Game.objects.filter(racecard_id=racecard_id)
    for game in games:
        # if game cancelled dont run this!
        if (game.game_state == Game.CANCELLED):
            continue

        if not game.started:
            validate_finalize_game.apply_async((game.id,))
        game.started = True
        game.game_state = Game.LIVE
        game.save()

@shared_task
def validate_finalize_game(game_id):
    game = Game.objects.get(id=game_id)

    calculate_stable_is_valid(game)
    calculate_scores_ranks(game)

    stables = Stable.objects.filter(game=game).annotate(runner_count=Count('runners')).prefetch_related('runners')
    finalize_bets(stables)

@shared_task
def create_game_update_custom_stats(game_id):
    pass

def points(finish):
    points = 0
    if finish is None:
        return 0

    if finish == 1:
        points = 60
    else:
        if finish == 2:
            points += 40
        elif finish == 3:
            points += 30
        elif finish == 4:
            points += 20
        elif finish == 5:
            points += 10
    return points

@shared_task
def follow_horses_notification(racecard_id):
    runners = Runner.objects.filter(racecard_id=racecard_id)
    racecard = Racecard.objects.get(id=racecard_id)

    for runner in runners:
        #Do any Follows exist with this horse external_id
        follows = Follows.objects.filter(horse=runner.external_id)
        for follow in follows:
            #Send a message to each user who is following that horse

            user = [follow.owner.auth0_id]
            #Create a list with a single user because that's what pusher beams expects
            pn = FollowsHorseNotification(user, runner, racecard)
            pn.send()

@periodic_task(
    run_every=(crontab(minute='*/30')),
    name="pre_post_notifications",
    ignore_result=True
)

def pre_post_notifications():
    games = Game.objects.filter(game_state=Game.OPEN, notification_sent=False)
    for game in games:
        race_date = game.racecard.races[0]['adjusted_date']
        if(type(race_date) == str):
            race_date = datetime.strptime(race_date, '%Y-%m-%d')

        start_time = datetime.strptime(game.racecard.races[0]['post_time'], '%I:%M%p')
        eta = datetime.combine(race_date, start_time.time())
        first_post_notification_time = eta - timedelta(minutes=30)

        #If we are within 60 minutes of when the notification should be sent, create the worker process
        if(first_post_notification_time-timedelta(minutes=60)) < datetime.now():
            game.notification_sent = True
            game.save()
            pre_post_notification.apply_async((game.racecard.id, ), eta=first_post_notification_time)

@shared_task
def pre_post_notification(racecard_id):
    games = Game.objects.filter(racecard_id=racecard_id)
    for game in games:
        pn = FirstPostNotification(game)
        pn.send()      


@shared_task
def finish_game(game_id):
    game = Game.objects.get(id=game_id)
    game.finished = True
    game.save()
    
    stables = Stable.objects.filter(game=game, is_valid_at_start=True)
    for stable in stables:
        runners = stable.runners.all()
        scratches = [runner for runner in runners if runner.scratched]
        if len(scratches) > 0:
            stable.scratches_at_finish = True
        else:
            stable.scratches_at_finish = False

        stable.stable_count_at_finish = len(runners)
        stable.save()

        #Only award points if the Game was not cancelled and Stable is valid
        if stable.is_valid_at_start and game.game_state is not Game.CANCELLED:
            points = stable.score if stable.score > 0 else 0
            stable_point, _ = StablePoint.objects.get_or_create(stable=stable, user=stable.user)
            stable_point.stable = stable
            stable_point.points = round(points)
            stable_point.notes = 'Points awarded for game {}'.format(game.name)
            stable_point.user = stable.user
            stable_point.save()

    #Expire all of the existing notifications so they aren't returned in the API
    #This also expires notifications from contests past since they haven't been
    #marked as such already.
    notifications = Notification.objects.filter(expired=False)
    for notification in notifications:
        notification.expired = True
        notification.save()


@periodic_task(
    run_every=(crontab(minute='*/30')),
    name="auto_archive_games",
    ignore_result=True
)
def auto_archive_games():
    games = Game.objects.filter(finished=True, archived=False)
    for game in games:
        race_date = game.racecard.races[-1]['adjusted_date']
        if(type(race_date) == str):
            race_date = datetime.strptime(race_date, '%Y-%m-%d')

        end_time = datetime.strptime(game.racecard.races[-1]['post_time'], '%I:%M%p')
        eta = datetime.combine(race_date, end_time.time())
        eta = eta + timedelta(hours=3)
        #set the task to archive if we are less than 30 minutes away
        if(eta-timedelta(minutes=30)) < datetime.now():
            auto_archive_game.apply_async((game.id, ), eta=eta)

@shared_task
def auto_archive_game(game_id):
    game = Game.objects.get(id=game_id)
    game.archived = True
    game.save()

@shared_task
def cancel_game(game_id):
    game = Game.objects.get(id=game_id)
    
    stables = Stable.objects.filter(game=game)
    for stable in stables:
        # Delete the stable and submit a bet refund
        cancel_bet(stable)

    #Don't cancel it more than once since we're sending out notifications and communicating with CHRIMS
    if( game.game_state != Game.CANCELLED):
        game.published = False
        game.archived = True
        game.game_state = Game.CANCELLED
        game.save()
        update_contest(game, 'contestIsCancelled')
        send_race_cancelled_notifications.delay(game.racecard.id)
