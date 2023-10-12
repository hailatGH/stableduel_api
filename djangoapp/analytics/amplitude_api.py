import json
from json.decoder import JSONDecodeError
from datetime import datetime, timedelta
import requests
from django.conf import settings
from wagering.models import Contest
from stables.utils import get_salary
from users.utils import get_custom_user_properties
import logging
log = logging.getLogger()

headers = {
  'Content-Type': 'application/json',
  'Accept': '*/*'
}

def amplitude_submitted_pick(stable):
    try:
        contest = stable.game.contest

        for runner in stable.runners.all():

            race_json = find_race_json(runner.racecard.races, runner.race_number)
            amplitude_data = {
                'api_key': settings.AMPLITUDE_KEY,
                'events': [ {
                    "user_id": stable.user.auth0_id,
                    "device_id" : "Server",
                    "event_type": "Submitted Pick",
                    "event_properties" : {
                        "StableID":stable.id,
                        "HorseID": runner.external_id,
                        "RaceID": runner.racecard.id,
                        "RaceNumber": runner.race_number,
                        "Track": runner.racecard.track.code,
                        "HorseName": runner.name,
                        "RaceType": race_json["race_type"] if race_json is not None else "",
                        "Distance": race_json["distance"] if race_json is not None else "",
                        "Surface": race_json["surface"] if race_json is not None else "",
                        "Salary": get_salary(runner.odds),
                        "SpeedRank": runner.custom_stats['speed'][0]['rank'] if runner.custom_stats is not None else "",
                        "ValueRank": runner.custom_stats['value'][0]['rank'] if runner.custom_stats is not None else "",
                        "RiskRank": runner.custom_stats['risk'] if runner.custom_stats is not None else ""
                    }
                }]
            }
        
            r = requests.post(settings.AMPLITUDE_URL, params={}, headers = headers, json=amplitude_data)

    except Exception as e: 
        log.debug("Amplitude error - Submitted Pick {}".format(e))
    return

def amplitude_contest_result(game):
    try:
        contest = game.contest
        
        for stable in game.stable_set.filter(is_valid_at_start=True):

            amplitude_data = {
                'api_key': settings.AMPLITUDE_KEY,
                'events': [ {
                    "user_id": stable.user.auth0_id,
                    "device_id" : "Server",
                    "event_type": "Contest Result",
                    "event_properties" : {
                        "ContestID": contest.id if contest is not None else "",
                        "StableID": stable.id,
                        "FinishPosition": stable.rank
                    }
                }]
            }
        
            r = requests.post(settings.AMPLITUDE_URL, params={}, headers = headers, json=amplitude_data)

    except Exception as e: 
        log.debug("Amplitude error - Contest Results {}".format(e))
    return

def amplitude_contest_settled(game):
    try:
        contest = game.contest
        
        amplitude_data = {
            'api_key': settings.AMPLITUDE_KEY,
            'events': [ {
                "device_id" : "Server",
                "event_type": "Contest Settled",
                "event_properties" : {
                    "ContestID": contest.id,
                    "Entries": game.stable_set.count(),
                    "ActualPrizePool": game.get_pool()
                }
            }]
        }
    
        r = requests.post(settings.AMPLITUDE_URL, params={}, headers = headers, json=amplitude_data)

    except Exception as e: 
        log.debug("Amplitude error - Contest Settled {}".format(e))
    return

def amplitude_notification_sent(notification):
    try:
        
        amplitude_data = {
            'api_key': settings.AMPLITUDE_KEY,
            'events': [ {
                "user_id" : notification.user.auth0_id,
                "device_id" : "Server",
                "event_type": "Notification Sent",
                "event_properties" : {
                    "NotificiationID": notification.id,
                    "NotificationType": notification.notif_type
                }
            }]
        }

        r = requests.post(settings.AMPLITUDE_URL, params={}, headers = headers, json=amplitude_data)

    except Exception as e: 
        log.debug("Amplitude error - Notification Sent {}".format(e))
    return

def amplitude_custom_user_properties(user):
    try:
        user_properties = get_custom_user_properties(user)
        amplitude_data = {
            'api_key': settings.AMPLITUDE_KEY,
            'events': [ {
                "device_id" : "Server",
                "user_id" : user.auth0_id,
                "event_type": "Custom User Properties",
                "event_properties" : {
                    "Rank": user_propeties["rank"],
                    "StablePoints": user_propeties["stable_points"],
                    "ContestsEntered": user_propeties["contests_entered"],
                    "StablesEntered": user_propeties["stables_entered"],
                    "FollowedHorses": user_propeties["followed_horses"],
                    "FollowedStables": user_propeties["followed_stables"],
                    "WinCount": user_propeties["win_count"],
                    "RacesRun": user_propeties["races_run"],
                    "PlaceCount": user_propeties["place_count"],
                    "ShowCount": user_propeties["show_count"],
                    "FourthCount": user_propeties["fourth_count"],
                    "FifthCount": user_propeties["fifth_count"]
                }
            }]
        }
        #print(amplitude_data)
        #r = requests.post(settings.AMPLITUDE_URL, params={

        #}, headers = headers, json=amplitude_data)

    except Exception as e: 
        log.debug("Amplitude error - Custom User Properties {}".format(e))
    return

def find_race_json(racecard_json, race_number):
    for race in racecard_json:
        if race["race_number"] == str(race_number):
            return race

    return None


