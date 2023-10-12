from celery import shared_task
from django.db.models import Q, Count
from django.core.cache import cache
from stables.models import Runner, Stable
from stables.notifications import ScratchedNotification
from racecards.models import Track, Racecard
from racecards.notifications import RaceCanceledNotification
from games.models import Game

import logging
log = logging.getLogger()


#manipulate this for race cancelled
@shared_task
def send_race_cancelled_notifications(racecard_id):

    #veryify that I get a track back from the query before I get the name
    track = Track.objects.filter(racecard__id=racecard_id)

    if track.exists():
        track = track.first()
        trackname = track.name
        games = Game.objects.filter(racecard__id=racecard_id)
        interests = []
        for game in games:
            interests.append('game-' + str(game.id))
            
        if len(interests) > 0:
            pn = RaceCanceledNotification(trackname, interests)
            pn.send()

    else:
        debugmessage = "Race Cancelled Notification, Track DOES NOT EXIST, racecard_id {}"
        log.debug(debugmessage.format(racecard_id))



