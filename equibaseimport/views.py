from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.parsers import JSONParser
from rest_framework.generics import  CreateAPIView
from rest_framework.response import Response
from equibaseimport.racecard_parser import RacecardParser, RacecardAppXmlParser
from racecards.models import Track, Racecard, HarnessTracksDetail, PATracksDetail
from stables.models import Runner, calculate_scores_ranks, get_runner_points
from stables.utils import get_fractional_salary
from lxml import etree as ET
from rest_framework import status
import datetime
# from datetime import datetime
from collections import OrderedDict
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import *
from . import horse_util
from games.models import Game
from games.tasks import finish_game, cancel_game
from racecards.timezones import get_timezone, calculate_timezone_harness
from racecards.tasks import send_race_cancelled_notifications
from stable_points.tasks import calculate_global_leaderboard
from horse_points.models import HorsePoint
from django.db import models, transaction, OperationalError
from django.db.models.expressions import RawSQL
from fractions import Fraction

import pytz

from stables.tasks import send_scratch_notifications

import logging
log = logging.getLogger()

class EquibaseImportView(CreateAPIView):
    parser_classes = (RacecardParser,)

    def post(self, request, format=None):
        log.debug('START IMPORT')
        root = ET.fromstring(request.data)
        race_date = root.find('RaceDate').text.split('+')[0]
        trackEL = root.find('Track')
        track_code = trackEL.find('TrackID').text
        track_name = trackEL.find('TrackName').text
        track_country = trackEL.find('Country').text
        
        try:
            track = Track.objects.get(code=track_code, country=track_country)
        except Track.DoesNotExist:
            track, _ = Track.objects.get_or_create(code=track_code, name=track_name, country=track_country)

        log.debug("RACE DATE: %s" % race_date)
        log.debug("TRACK CREATED: %s" % track_code)
        racecard, _ = Racecard.objects.get_or_create(track=track, race_date=race_date, mode="THOROUGHBRED")
        races = []
        # previous_time_meridiem = ""
        for raceEL in root.findall('Race'):
            # IGNORE SIMULCAST RACES
            if(raceEL.find('SimulcastFlag').text == 'Y'):
                continue

            race_number = raceEL.find('RaceNumber').text
            if(type(race_date) == str):
                race_date = datetime.strptime(race_date, '%Y-%m-%d')
            post_time = datetime.strptime(raceEL.find('PostTime').text, '%I:%M%p')
            # logical_offset_am = datetime.strptime("09:00AM", '%I:%M%p')
            # logical_offset_pm = datetime.strptime("09:00PM", '%I:%M%p')
            # if  post_time < logical_offset_am :
            #     #No race will start before 8:00am
            #     post_time += timedelta(hours=12)
            # elif post_time > logical_offset_pm and previous_time_meridiem == "PM":
            #     #If previous race was pm and the race is after 8:00pm keep it pm 
            #     post_time += timedelta(hours=12)
            # elif  post_time > logical_offset_pm and previous_time_meridiem == "AM":
            #     #No race will start after 8:00pm ut
            #     # post_time=post_time
            #     post_time += timedelta(hours=12)
            #     previous_time_meridiem == "AM"
            # post_time = datetime.strptime(raceEL.find('PostTime').text, '%I:%M%p')
            timezone = get_timezone(track_code)
            race_date_time = datetime.combine(race_date, post_time.time())
            #We need an adjusted date since we're serving everything up as UTC now.  Some 
            #Pacific time, late races will go over to the next day as UTC
            adjusted_date = race_date_time + timedelta(hours=timezone.time_delta) - timezone.tz.localize(race_date_time).dst()
            # if previous_time_meridiem =="PM":
            #     previous_time_meridiem =="PM"
            # else:
            #     previous_time_meridiem = adjusted_date.strftime("%p")
            race_type = raceEL.find('RaceType/RaceType').text
            grade = raceEL.find('Grade').text 
            if grade is not None and race_type == "STK":
                race_type = "G" + grade

            race = {
                'race_number': race_number,
                'surface': raceEL.find('Course/Surface/Value').text,
                'post_time': adjusted_date.strftime("%I:%M%p"),
                'adjusted_date': adjusted_date.strftime("%Y-%m-%d"),
                'race_type': race_type,
                'race_type_description': raceEL.find('RaceType/Description').text,
                'distance': raceEL.find('Distance/PublishedValue').text,
                'division': raceEL.find('Division').text,
                'race_name': raceEL.find('RaceName').text,
                'results_are_in': False,
                'mode': Racecard.THOROUGHBRED,
                'status': Racecard.NOT_STARTED
            }
            log.debug("RACE LOADED: %s" % race_number)
            races.append(race)

            for starterEL in raceEL.findall('Starters'):
                scratchIndicator = starterEL.find('ScratchIndicator/Value').text
                if scratchIndicator is not None and scratchIndicator == 'S':
                    continue
                
                program_number = starterEL.find('ProgramNumber').text
                runner_name = starterEL.find('Horse/HorseName').text
                if '(' in runner_name:
                    runner_name = runner_name[0:runner_name.index('(') - 1]

                horse_id = starterEL.find('Horse/RegistrationNumber').text
                if horse_id is None:
                    horse_id = program_number

                runner, _ = Runner.objects.get_or_create(racecard=racecard, race_number=race_number, external_id=horse_id)
                runner.race_number = race_number
                runner.post_position = starterEL.find('PostPosition').text
                runner.program_number = program_number

                runner.name = runner_name
                
                if scratchIndicator is not None and scratchIndicator == 'A':
                    runner.name = 'AE - ' + runner.name

                if starterEL.find('CoupledIndicator').text is not None:
                    runner.coupled = True
                    runner.coupled_indicator = starterEL.find('CoupledIndicator').text
                runner.trainer = "{} {}".format(starterEL.find('Trainer/FirstName').text, starterEL.find('Trainer/LastName').text)
                runner.jockey =  "{} {}".format(starterEL.find('Jockey/FirstName').text, starterEL.find('Jockey/LastName').text)
                runner.owner =  "{}".format(starterEL.find('OwnerName').text)
                runner.odds = starterEL.find('Odds').text

                runner.pedigree = horse_util.get_pedigree_data(starterEL.find('Horse'))
                runner.career_stats = horse_util.get_career_data(starterEL.findall('RaceSummary'))

                past_performances = []

                for past_performance_EL in starterEL.findall('PastPerformance')[:10]:
                    past_performances.append(horse_util.get_past_performance_data(past_performance_EL))
                runner.past_performance = past_performances


                workouts = []

                for workout_EL in starterEL.findall('Workout'):
                    workouts.append(horse_util.get_workout_data(workout_EL))
                runner.workouts = workouts

                custom_stats = {}
                #Create a default custom_stats entry that will be updated if a Game is created for 
                #this runner

                custom_stats['risk'] = 'N/A'
                custom_stats['timeform_rating'] = 'N/A'
                custom_stats['running_style'] = 'N/A'
                custom_stats['trainer_jockey_rating'] = 'N/A'
                custom_stats['drf_starter_id'] = 'N/A'
                #Note: we're not using this past_performance for value ranking below.  These are being used only to calculate 
                #a speed rating from TimeForm later after the game is created.
                custom_stats['past_performances'] = []

                pp_count = 0
                total_for_avg = 0
                total_salary = 0
                total_points = 0
                for past_performance in past_performances[:10]:
                    pp_count = pp_count + 1
                    total_for_avg += past_performance['performance_figure']
                    total_salary += get_fractional_salary(past_performance['odds'])
                    margin = past_performance['finish']['lengths'] / 100
                    points = get_runner_points(past_performance['finish']['position'])
                    total_points += max( -30, round(points + margin, 2 ))
                
                if pp_count > 0:
                    custom_stats['speed'] = {
                        'rank' : '',
                        'detail': str(round(total_for_avg / pp_count, 2)),
                        'denominator': ''
                    }
                else:
                    custom_stats['speed'] = {
                        'rank' : 'N/A',
                        'detail': 'not enough data',
                        'denominator': ''
                    }

                last_cost_per_point = round(total_salary / total_points, 2) if total_points > 0 else 0
                custom_stats['value'] = {
                    'rank' : '',
                    'detail': str(last_cost_per_point),
                    'denominator': ''
                }
                
                runner.custom_stats = custom_stats
                
                runner.save()
                log.debug("RUNNER LOADED: %s", runner.name)

            #Now, we need to assign the Ranking of each horse based upon the number of Runners in the field.
            runners = Runner.objects.filter(racecard=racecard, race_number=race_number).annotate(
                            detail=RawSQL("custom_stats->'speed'->'detail'", [])).order_by('-detail')
            
            counter = 1
            for runner in runners:
                if runner.custom_stats['speed']['detail'] != "not enough data": 
                    runner.custom_stats['speed']['rank'] = str(counter)
                    runner.custom_stats['speed']['denominator'] = str(len(runners))
                else:
                    runner.custom_stats['speed'] = {
                        'rank' : 'N/A',
                        'detail': 'not enough data',
                        'denominator':''
                    }
                    
                runner.save()
                counter = counter + 1

            runners2 = Runner.objects.filter(racecard=racecard, race_number=race_number).annotate(
                            detail=RawSQL("custom_stats->'value'->'detail'", [])).order_by('-detail')
            counter = 1
            for runner in runners2:
                if runner.custom_stats['value']['detail'] != 0 and runner.custom_stats['value']['detail'] != "not enough data": 
                    runner.custom_stats['value']['rank'] = str(counter)
                    runner.custom_stats['value']['denominator'] = str(len(runners2))
                else:
                    runner.custom_stats['value'] = {
                        'rank' : 'N/A',
                        'detail': 'not enough data',
                        'denominator':''
                    }                
                runner.save()
                counter = counter + 1

        racecard.races = races
        racecard.save()


        return Response(request.data, status=status.HTTP_201_CREATED)




class HarnessImportView(CreateAPIView):
    parser_classes = (RacecardParser,)

    def post(self, request, format=None):
        log.debug('START IMPORT')
        root = ET.fromstring(request.data)
        track_dataEL = root.find ('trackdata')
        race_dataEL = track_dataEL.find('racedata')
        race_date = race_dataEL.find('racedate').text
        track_code = track_dataEL.find('track').text
        track_country = "USA"
        try:
            track_detail = HarnessTracksDetail.objects.get(code=track_code)
            track_name = track_detail.name
            track_code = track_detail.trackmastercode
            track_country = track_detail.country
            timezone_abbrev = track_detail.timezoneabbrev
            time_zone = track_detail.timezone
            

        except BaseException as e:
            track_name = track_code
        
        try:
            track = Track.objects.get(code=track_code, country=track_country)
        except Track.DoesNotExist:
            track, _ = Track.objects.get_or_create(code=track_code, name=track_name, country=track_country)

        log.debug("RACE DATE: %s" % race_date)
        log.debug("TRACK CREATED: %s" % track_code)
        racecard, _ = Racecard.objects.get_or_create(track=track, race_date=race_date, mode="HARNESS")
        races = []
        previous_time_meridiem = ""
        for raceEL in track_dataEL.findall('racedata'):
            
            # IGNORE SIMULCAST RACES
            if(raceEL.find('simulcast').text == 'Y'):
                continue

            race_number = raceEL.find('race').text
            if(type(race_date) == str):
                race_date = datetime.strptime(race_date, '%Y-%m-%d')

            post_time = datetime.strptime(raceEL.find('posttime').text, '%H:%M')
        
            logical_offset_am = datetime.strptime("09:00", '%H:%M')
            logical_offset_pm = datetime.strptime("21:00", '%H:%M')

            # meridiem_indicator = raceEL.find('card_id')
                
            
            if  post_time < logical_offset_am :
                #No race will start before 8:00am
                post_time += timedelta(hours=12)
            elif post_time > logical_offset_am and previous_time_meridiem == "PM":
                #If previous race was pm and the race is after 8:00pm keep it pm 
                post_time += timedelta(hours=12)
            elif  post_time > logical_offset_pm:
                #No race will start after 8:00pm ut
                post_time -= timedelta(hours=12)
            
            
            timezone = calculate_timezone_harness(track_name, track_code, timezone_abbrev,time_zone)
            
            race_date_time = datetime.combine(race_date, post_time.time())
            #We need an adjusted date since we're serving everything up as UTC now.  Some 
            #Pacific time, late races will go over to the next day as UTC
            
            adjusted_date = race_date_time + timedelta(hours=timezone.time_delta) - timezone.tz.localize(race_date_time).dst()
            if previous_time_meridiem =="PM":
                previous_time_meridiem =="PM"
            else:
                previous_time_meridiem = adjusted_date.strftime("%p")
            
            race_type = raceEL.find('racetext1')
            if race_type is not None:
                race_type = race_type.text
                race_type = " ".join(race_type.split()[:10])
                
            else:
                race_type = None
            
            grade = raceEL.find('grade')
            if grade is not None:
                grade = grade.text
            else:
                grade = None

            if grade is not None and race_type == "STK":
                race_type = "G" + grade

            race_type_description =raceEL.find('RaceType/Description')
            if race_type_description is not None:
                race_type_description = race_type_description.text
            else:
                race_type_description = None


            division =raceEL.find('division')
            if division is not None:
                division = division.text
            else:
                division = None

            race_name =raceEL.find('RaceName')
            if race_name is not None:
                race_name = race_name.text
            else:
                race_name = None
            
            race = {
                'race_number': race_number,
                'surface': "D",
                'post_time': adjusted_date.strftime("%I:%M%p"),
                'adjusted_date': adjusted_date.strftime("%Y-%m-%d"),
                'race_type': race_type,
                'race_type_description': race_type_description,
                'distance': raceEL.find('distance').text,
                'division': division,
                'race_name': race_name,
                'results_are_in': False,
                'mode': Racecard.HARNESS,
                'status': Racecard.NOT_STARTED
            }
            log.debug("RACE LOADED: %s" % race_number)
            races.append(race)

            for horseEL in raceEL.findall('horsedata'):


            # for starterEL in raceEL.findall('starters'):
                scratchIndicator = horseEL.find('scratchindicator')
                if scratchIndicator is not None:
                    scratchIndicator = scratchIndicator.text
                else:
                    scratchIndicator = None

                if scratchIndicator is not None and scratchIndicator == 'S':
                    continue
                
                program_number = horseEL.find('program').text
                runner_name = horseEL.find('horse_name').text
                if '(' in runner_name:
                    runner_name = runner_name[0:runner_name.index('(') - 1]

                horse_id = horseEL.find('hi')
                if horse_id is not None:
                    horse_id = horse_id.text
                else:
                    horse_id = None

                if horse_id is None:
                    horse_id = program_number

                runner, _ = Runner.objects.get_or_create(racecard=racecard, race_number=race_number, external_id=horse_id)
                runner.race_number = race_number
                runner.post_position = horseEL.find('pp').text
                runner.program_number = program_number

                runner.name = runner_name
                
                if scratchIndicator is not None and scratchIndicator == 'A':
                    runner.name = 'AE - ' + runner.name

                CoupledIndicator=horseEL.find('CoupledIndicator')
                if CoupledIndicator is not None:
                    CoupledIndicator = CoupledIndicator.text
                else:
                    CoupledIndicator = None
                    

                if CoupledIndicator is not None:
                    runner.coupled = True
                    runner.coupled_indicator = CoupledIndicator
                runner.trainer = horseEL.find('trainer/trainname').text
                runner.jockey =  horseEL.find('driver/drivername').text
                runner.owner =  horseEL.find('owner_name').text
                runner.odds = horseEL.find('morn_odds').text

                runner.pedigree = horse_util.get_pedigree_data_harness(horseEL)
                horseELs = raceEL.findall('horsedata')
                # for horseEL in horseELs:
                #     runner.career_stats = horse_util.get_career_data_harness(horseEL)
                runner.career_stats = horse_util.get_career_data_harness(horseEL)

                past_performances = []
                
                
                for past_performance_EL in horseEL.findall('ppdata')[:10]:
                    

                    past_performances.append(horse_util.get_harness_past_performance_data(past_performance_EL))
                
                
               

                runner.past_performance = past_performances


                workouts = []

                # for workout_EL in starterEL.findall('Workout'):
                #     workouts.append(horse_util.get_workout_data(workout_EL))
                runner.workouts = workouts

                custom_stats = {}
                #Create a default custom_stats entry that will be updated if a Game is created for 
                #this runner

                custom_stats['risk'] = 'N/A'
                custom_stats['timeform_rating'] = 'N/A'
                custom_stats['running_style'] = 'N/A'
                custom_stats['trainer_jockey_rating'] = 'N/A'
                custom_stats['drf_starter_id'] = 'N/A'
                #Note: we're not using this past_performance for value ranking below.  These are being used only to calculate 
                #a speed rating from TimeForm later after the game is created.
                custom_stats['past_performances'] = []

                pp_count = 0
                total_for_avg = 0
                total_salary = 0
                total_points = 0
                for past_performance in past_performances[:10]:
                    pp_count = pp_count + 1
                    total_for_avg += past_performance['performance_figure']
                    if past_performance['odds'] > 0:
                        total_salary += get_fractional_salary(past_performance['odds'])
                    else: 
                        total_salary += 0
                    try:
                        margin = past_performance['finish']['lengths'] / 100
                    except:
                        margin = 0
                    points = get_runner_points(past_performance['finish']['position'])
                    total_points += max( -30, round(points + margin, 2 ))
                    
                
                if pp_count > 0:
                    custom_stats['speed'] = {
                        'rank' : '',
                        'detail': str(round(total_for_avg / pp_count, 2)),
                        'denominator': ''
                    }
                else:
                    custom_stats['speed'] = {
                        'rank' : 'N/A',
                        'detail': 'not enough data',
                        'denominator': ''
                    }

                last_cost_per_point = round(total_salary / total_points, 2) if total_points > 0 else 0
                custom_stats['value'] = {
                    'rank' : '',
                    'detail': str(last_cost_per_point),
                    'denominator': ''
                }
                
                runner.custom_stats = custom_stats
                
                runner.save()
                log.debug("RUNNER LOADED: %s", runner.name)

            # #Now, we need to assign the Ranking of each horse based upon the number of Runners in the field.
            runners = Runner.objects.filter(racecard=racecard, race_number=race_number).annotate(
                            detail=RawSQL("custom_stats->'speed'->'detail'", [])).order_by('-detail')
            
            counter = 1
            for runner in runners:
                if runner.custom_stats['speed']['detail'] != "not enough data": 
                    runner.custom_stats['speed']['rank'] = str(counter)
                    runner.custom_stats['speed']['denominator'] = str(len(runners))
                else:
                    runner.custom_stats['speed'] = {
                        'rank' : 'N/A',
                        'detail': 'not enough data',
                        'denominator':''
                    }
                    
                runner.save()
                counter = counter + 1

            runners2 = Runner.objects.filter(racecard=racecard, race_number=race_number).annotate(
                            detail=RawSQL("custom_stats->'value'->'detail'", [])).order_by('-detail')
            counter = 1
            for runner in runners2:
                if runner.custom_stats['value']['detail'] != 0 and runner.custom_stats['value']['detail'] != "not enough data": 
                    runner.custom_stats['value']['rank'] = str(counter)
                    runner.custom_stats['value']['denominator'] = str(len(runners2))
                else:
                    runner.custom_stats['value'] = {
                        'rank' : 'N/A',
                        'detail': 'not enough data',
                        'denominator':''
                    }                
                runner.save()
                counter = counter + 1

        racecard.races = races
        racecard.save()


        return Response(request.data, status=status.HTTP_201_CREATED)








class EquibaseImportChangeView(APIView):
    parser_classes = (JSONParser,)

    def post(self, request, format=None):
        log.debug('START CHANGE IMPORT')
        for change in request.data['changes']:
            racecard_id = change['racecard_id']
            race_number = change['race_number']
            track_code = racecard_id[:-8]
            race_date_YYYYMMDD = racecard_id[-8:]
            race_date = datetime.strptime(race_date_YYYYMMDD, '%Y%m%d').strftime('%Y-%m-%d')

            try:
                track = Track.objects.get(code=track_code)
                racecard = Racecard.objects.get(track=track, race_date=race_date, mode="THOROUGHBRED")

                if 'Scratched' in change['change_description']:
                    
                    horse_name = change['horse_name']
                    if '(' in horse_name:
                        horse_name = horse_name[0:horse_name.index('(') - 1]

                    try:
                        runner = Runner.objects.get(racecard=racecard, race_number=race_number, name=horse_name)
                    except Runner.DoesNotExist:
                        runner = Runner.objects.get(racecard=racecard, race_number=race_number, name='AE - {}'.format(horse_name))

                    if(change['new_value'] == 'Y'):
                        was_scratched = runner.scratched
                        runner.scratched = True
                        games = Game.objects.filter(racecard_id=racecard.id)
                        
                        change_datetime_obj = datetime.strptime(change['date_changed'], "%Y-%m-%d %H:%M:%S.%f")
                        # change_date = change_datetime_obj.date()
                        # change_time = change_datetime_obj.time()
                        timezone = get_timezone(track_code)
                        adjusted_change_date_time = change_datetime_obj + timedelta(hours=timezone.time_delta) - timezone.tz.localize(change_datetime_obj).dst()
                        # runner.scratched_datetime = change['date_changed']
                        runner.scratched_datetime = adjusted_change_date_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                        
                        if not was_scratched:
                            #Send the notification to every game that includes this racecard that contains the specified runner
                            for game in games:
                                send_scratch_notifications.delay(runner.id, game.id)
                    else:
                        runner.scratched = False

                    runner.save()
                    #Is this the last race, if so, don't cancel the game.
                elif 'Race Cancelled' in change['change_description']:
                    #Get all of the races for the racecard
                    last_race_number = 1
                    for race in racecard.races:
                        if(int(race["race_number"]) > last_race_number):
                            last_race_number = int(race["race_number"])

                    #We should now have the last race number for the card. If this change is related to that number, disregard the code below
                    if(int(change["race_number"]) != last_race_number):

                        games = Game.objects.filter(racecard_id=racecard.id)
                        
                        for game in games:
                            cancel_game(game.id)
                    else:
                        #Check to see if the Game is ready to be finished (i.e. if every race up to the last one has been completed)
                        #We're assuming that the Last Race is being cancelled at this point. Check to see if the remaining races have been entered
                        #and are official. If so, finish the game.

                        races_completed = True
                        #traverse every race. if it's not the last one and we don't have official results, don't finish the game.
                        
                        for race in racecard.races:
                            if int(race['race_number']) == last_race_number:
                                race['status'] = Racecard.CANCELLED
                                racecard.save()
                            elif race['results_are_in'] == False or race['status'] != Racecard.OFFICIAL:
                                races_completed = False


                        if races_completed == True:
                            games = Game.objects.filter(racecard_id=racecard.id)
                            for game in games:
                                if not game.finished:
                                    finish_game(game.id)

            except Track.DoesNotExist:
                log.debug("DOES NOT EXIST: Track: %s" % track_code)
                continue
            except Runner.DoesNotExist:
                log.debug("DOES NOT EXIST: Runner: %s" % change['horse_id'])
                continue
            except Racecard.DoesNotExist:
                log.debug("DOES NOT EXIST: Racecard: track=%s race_date=%s" % (track_code, race_date))
                continue
            
        return Response(request.data, status=status.HTTP_201_CREATED)




class PATracksDetailImportView(CreateAPIView):
    parser_classes = (RacecardParser,)

    def post(self, request, format=None):
        log.debug('START PA tracks IMPORT')
        root = ET.fromstring(request.data)
        
        

        try:
            for trackEL in root.findall('record'):
                code = trackEL.find('Abbreviation').text
                name = trackEL.find('CourseName').text
                country = trackEL.find('Country').text

                code = code.strip()
                name = name.strip()
                country = country.strip()

                track, _ = PATracksDetail.objects.get_or_create(code=code, country=country, name=name)
                track.code=code.strip()
                track.country=country.strip()
                track.name=name.strip()
                track.save()

                
      
        except PATracksDetail.DoesNotExist:
            log.debug("DOES NOT EXIST: HarnessTracksDetail: %s" % code)
        
        return Response(request.data, status=status.HTTP_201_CREATED)






class PAImportView(APIView):
    
    parser_classes = (RacecardAppXmlParser,)

    def post(self, request, format=None):
        log.debug('START PA IMPORT')
        root = ET.fromstring(request.data)

        if root.tag != 'HorseRacingCard':
            log.debug('HorseRacingCard')
            return Response(request.data, status=status.HTTP_200_OK)

        meeting_node = root.find("Meeting")
        race_node = root.findall("Meeting/Race")
        if (race_node is None):
            log.debug('Race_node is None')
            return Response(request.data, status=status.HTTP_200_OK)

        course = meeting_node.attrib['course']
        print("###############")
        print (course)
        track_detail= PATracksDetail.objects.get(name=course)
        track_code = track_detail.code
        print(track_code)
        name = track_detail.name
        country = track_detail.country
        # track_code_mapped = course.lower()
        if not track_code:
            log.debug('No track code')
            return Response(request.data, status=status.HTTP_200_OK)
        
        if (track_code is None):
            log.debug('track code is none')
            return Response(request.data, status=status.HTTP_200_OK)

        track = None
        meeting_date = None
        racecard = None

        # try:
        #     track = Track.objects.get(code=track_code)
        # except Track.DoesNotExist:
        #     # track = None
        #     log.debug('Track Does not exist')
        print (track_code)
        track, _ = Track.objects.get_or_create(code=track_code, name=name, country=country)
        print(track_code)
        print ("whyyyy")
        print (track)
        # try:
        #     track = Track.objects.get(code=track_code)
        meeting_date = datetime.strptime(meeting_node.attrib['date'], '%Y%m%d')
        meeting_id = meeting_node.attrib['id']
        race_date=meeting_date
        # racecard = Racecard.objects.get(track=track, race_date=meeting_date)
        # except Racecard.DoesNotExist:
            # racecard = None
            # log.debug('Race card Does not exist')
        print("************************")
        log.debug(track)
        
        racecard, _ = Racecard.objects.get_or_create(track=track, race_date = meeting_date, mode="PA")
        
        log.debug(track.code)
        races = []
        race_number = 0
        for raceEL in race_node:
            race_id = raceEL.attrib['id']
            race_number += 1
            if(type(meeting_date) == str):
                race_date = datetime.strptime(meeting_date, '%Y-%m-%d')
            time_change = "0000"
            time_change = datetime.strptime(time_change, '%H%M')
            if '+' in raceEL.attrib['time']:
                plus_index = raceEL.attrib['time'].index('+')
                time_change = raceEL.attrib['time'][plus_index + 1:]
                # time_delta = datetime.strptime(time_change, '%H%M')
                time_delta = timedelta(hours=int(time_change[:2]), minutes=int(time_change[2:]))
                
            elif '-' in raceEL.attrib['time']:
                minus_index = raceEL.attrib['time'].index('-')
                time_change = raceEL.attrib['time'][minus_index + 1:]
                # time_delta = datetime.strptime(time_change, '%H%M')
                time_delta = timedelta(hours=int(time_change[:2]), minutes=int(time_change[2:]))
                time_delta = -(time_delta)
                

            post_time = datetime.strptime(raceEL.attrib['time'][:-5], '%H%M')
            post_time = post_time - time_delta
            race_date_time = datetime.combine(race_date, post_time.time())

            adjusted_date = race_date_time 
            race_type = raceEL.attrib['raceType']
            race_type_description =raceEL.find('Title').text
            surface = raceEL.attrib['trackType']
            distanceEL = raceEL.find('Distance')
            division = raceEL.attrib['class'] 
            race_name = raceEL.find('Title').text
            race = {
            'race_number': str(race_number),
            'surface': surface,
            'post_time': adjusted_date.strftime("%I:%M%p"),
            'adjusted_date': adjusted_date.strftime("%Y-%m-%d"),
            'race_type': race_type,
            'race_type_description': race_type_description,
            'distance': distanceEL.attrib['value'],
            'division': division,
            'race_name': race_name,
            'results_are_in': False,
            'mode': Racecard.PA,
            'status': Racecard.NOT_STARTED,
            'meeting_id': meeting_id
            }
            log.debug("RACE LOADED: %s" % race_number)
            races.append(race)

            for horseEL in raceEL.findall('Horse'):
                scratchIndicator = None
                try:
                    scratchIndicator = horseEL.attrib['status']
                except KeyError:
                    log.debug("HORSE STATUS IS NOT KNOWN!")
                    pass
                # scratchIndicator = horseEL.attrib['status']
                # if scratchIndicator is not None:
                #     scratchIndicator = scratchIndicator
                # else:
                #     scratchIndicator = None

                if scratchIndicator is not None and scratchIndicator == 'Doubtful':
                    if not runner.scratched:
                        runner.scratched = True
                        games = Game.objects.filter(racecard_id=racecard.id)
                        runner.scratched_datetime = datetime.now()
                #Send the notification to every game that includes this racecard that contains the specified runner
                        for game in games:
                            send_scratch_notifications.delay(runner.id, game.id)
                
                    # continue

                runner_name = horseEL.attrib['name']
                if '(' in runner_name:
                    runner_name = runner_name[0:runner_name.index('(') - 1]
                horse_id = horseEL.attrib['id']
                runner, _ = Runner.objects.get_or_create(racecard=racecard, race_number=race_number, external_id=horse_id)
                runner.race_number = race_number
                program_number = horseEL.find('Cloth')
                post_position = horseEL.find('Drawn')
                if post_position:
                    runner.post_position = post_position.attrib['stall']
                else:
                    runner.post_position = program_number.attrib['number']          
                runner.program_number = program_number.attrib['number']
                runner.name = runner_name
                # if scratchIndicator is not None and scratchIndicator == 'A':
                #     runner.name = 'AE - ' + runner.name

                CoupledIndicator=horseEL.find('CoupledIndicator')
                if CoupledIndicator is not None:
                    CoupledIndicator = CoupledIndicator.text
                else:
                    CoupledIndicator = None
                    

                if CoupledIndicator is not None:
                    runner.coupled = True
                    runner.coupled_indicator = CoupledIndicator
                trainer = horseEL.find('Trainer')
                jockey = horseEL.find('Jockey')
                owner = horseEL.find('Owner')
                runner.trainer = trainer.attrib['name']
                runner.jockey =  jockey.attrib['name']
                runner.owner =  owner.attrib['name']
                try:
                    ForecastPrice = horseEL.find('ForecastPrice/Price')
                    numerator = ForecastPrice.attrib['numerator']
                    denominator = ForecastPrice.attrib['denominator']
                except:
                    numerator = 50
                    denominator = 1
                runner.odds = "{}/{}".format(numerator, denominator)
                # odds = int(numerator)/int(denominator)
                # runner.odds =round(odds, 7)

                runner.pedigree = horse_util.get_pedigree_data_pa(horseEL)
                # horseELs = raceEL.findall('horsedata')
                # for horseEL in horseELs:
                #     runner.career_stats = horse_util.get_career_data_harness(horseEL)
                runner.career_stats = horse_util.get_career_data_pa(horseEL)

                # past_performances = []
                
                
                # for past_performance_EL in horseEL.findall('FormRace')[:10]:
                #     past_performances.append(horse_util.get_pa_past_performance_data(past_performance_EL))
                past_performances = horse_util.get_pa_past_performance_data_from_API(race_date,race_id,horse_id)
                runner.past_performance = past_performances
                custom_stats = {}
                #Create a default custom_stats entry that will be updated if a Game is created for 
                #this runner
                custom_stats['risk'] = 'N/A'
                custom_stats['timeform_rating'] = 'N/A'
                custom_stats['running_style'] = 'N/A'
                custom_stats['trainer_jockey_rating'] = 'N/A'
                custom_stats['drf_starter_id'] = 'N/A'
                #Note: we're not using this past_performance for value ranking below.  These are being used only to calculate 
                #a speed rating from TimeForm later after the game is created.
                custom_stats['past_performances'] = []
                pp_count = 0
                total_for_avg = 0
                total_salary = 0
                total_points = 0
                for past_performance in past_performances[:10]:
                    pp_count = pp_count + 1
                    total_for_avg += past_performance['performance_figure']
                    total_salary += get_fractional_salary(past_performance['odds'])
                    margin = past_performance['finish']['lengths'] / 100
                    points = get_runner_points(past_performance['finish']['position'])
                    total_points += max( -30, round(points + margin, 2 ))
                
                if pp_count > 0:
                    custom_stats['speed'] = {
                        'rank' : '',
                        'detail': str(round(total_for_avg / pp_count, 2)),
                        'denominator': ''
                    }
                else:
                    custom_stats['speed'] = {
                        'rank' : 'N/A',
                        'detail': 'not enough data',
                        'denominator': ''
                    }

                last_cost_per_point = round(total_salary / total_points, 2) if total_points > 0 else 0
                custom_stats['value'] = {
                    'rank' : '',
                    'detail': str(last_cost_per_point),
                    'denominator': ''
                }
                
                runner.custom_stats = custom_stats
                runner.save()
                log.debug("RUNNER LOADED: %s", runner.name)

            runners = Runner.objects.filter(racecard=racecard, race_number=race_number).annotate(
                            detail=RawSQL("custom_stats->'speed'->'detail'", [])).order_by('-detail')
            
            counter = 1
            for runner in runners:
                if runner.custom_stats['speed']['detail'] != "not enough data": 
                    runner.custom_stats['speed']['rank'] = str(counter)
                    runner.custom_stats['speed']['denominator'] = str(len(runners))
                else:
                    runner.custom_stats['speed'] = {
                        'rank' : 'N/A',
                        'detail': 'not enough data',
                        'denominator':''
                    }
                    
                runner.save()
                counter = counter + 1

            runners2 = Runner.objects.filter(racecard=racecard, race_number=race_number).annotate(
                            detail=RawSQL("custom_stats->'value'->'detail'", [])).order_by('-detail')
            counter = 1
            for runner in runners2:
                if runner.custom_stats['value']['detail'] != 0 and runner.custom_stats['value']['detail'] != "not enough data": 
                    runner.custom_stats['value']['rank'] = str(counter)
                    runner.custom_stats['value']['denominator'] = str(len(runners2))
                else:
                    runner.custom_stats['value'] = {
                        'rank' : 'N/A',
                        'detail': 'not enough data',
                        'denominator':''
                    }                
                runner.save()
                counter = counter + 1

        racecard.races = races
        racecard.save()
        log.debug('RACE CARD SAVED')
        return Response(request.data, status=status.HTTP_200_OK)
        






# class PAImportView(APIView):
#     parser_classes = (RacecardAppXmlParser,)

#     track_code_map = {
#         'wolverhampton': 'WOL',
#         'meydan': 'DUB',
#         'cheltenham': 'CHM',
#         'kelso': 'KEL',
#         'taunton': 'TAU',
#         'haydock': 'HAY',
#         'sedgefield': 'SED',
#     }

#     length_name_map = {
#         'short head': 5,
#         'nose': 5,
#         'head': 10,
#         'neck': 25
#     }

#     def post(self, request, format=None):
#         log.debug('START PA IMPORT')
#         root = ET.fromstring(request.data)

#         if root.tag != 'HorseRacing':
#             return Response(request.data, status=status.HTTP_200_OK)

#         meeting_node = root.find("Meeting")
#         race_node = root.find("Meeting/Race")
#         if (race_node is None):
#             return Response(request.data, status=status.HTTP_200_OK)

#         course = meeting_node.attrib['course']
#         track_code_mapped = course.lower()
#         if (track_code_mapped not in self.track_code_map):
#             return Response(request.data, status=status.HTTP_200_OK)
#         track_code = self.track_code_map[track_code_mapped]
#         if (track_code is None):
#             return Response(request.data, status=status.HTTP_200_OK)

#         track = None
#         meeting_date = None
#         racecard = None

#         try:
#             track = Track.objects.get(code=track_code)
#             meeting_date = datetime.strptime(meeting_node.attrib['date'], '%Y%m%d')
#             racecard = Racecard.objects.get(track=track, race_date=meeting_date)
#         except Track.DoesNotExist:
#             track = None
#         except Racecard.DoesNotExist:
#             racecard = None

#         if (track is None or racecard is None):
#             return Response(request.data, status=status.HTTP_200_OK)

#         race_date = datetime.strptime(race_node.attrib['date'], '%Y%m%d')
#         race_time_text = race_node.attrib['time'].split('+')[0]
#         race_time = datetime.strptime(race_time_text, '%H%M')
        
#         race_time_search = race_time.strftime("%I:%M%p")
#         race_date_search = race_date.strftime("%Y-%m-%d")
        
#         race = None
#         race_number = 0
#         for race in racecard.races:
#             if race['post_time'] == race_time_search and race['adjusted_date'] == race_date_search:
#                 race = race
#                 race_number = race['race_number']
#                 break

#         if race_number == 0:
#             return Response(request.data, status=status.HTTP_200_OK)

#         for horseEL in root.findall('Meeting/Race/Horse'):
#             horse_name = horseEL.attrib['name']
#             horse_status = horseEL.attrib['status']
            
#             if horse_status != 'NonRunner':
#                 continue

#             try:
#                 runner = Runner.objects.get(racecard=racecard, race_number=race_number, name__iexact=horse_name)
#             except Runner.DoesNotExist:
#                 runner = Runner.objects.get(racecard=racecard, race_number=race_number, name__iexact='AE - {}'.format(horse_name))

#             if not runner.scratched:
#                 runner.scratched = True
#                 games = Game.objects.filter(racecard_id=racecard.id)
#                 runner.scratched_datetime = datetime.now()
#                 #Send the notification to every game that includes this racecard that contains the specified runner
#                 for game in games:
#                     send_scratch_notifications.delay(runner.id, game.id)
#                 runner.save()

#         win_node = root.find('Meeting/Race/WinTime')
#         winning_distances = root.findall('Meeting/Race/WinningDistance')
#         #  and race['status'] != Racecard.OFFICIAL
#         if win_node is not None and len(winning_distances) > 0:
          
#             missing_data = False
#             first_runner = None
#             second_runner = None
#             runners = []
#             runners_length_behind = {}
#             for horseEL in root.findall('Meeting/Race/Horse'):
#                 horse_name = horseEL.attrib['name']

#                 try:
#                     runner = Runner.objects.get(racecard=racecard, race_number=race_number, name__iexact=horse_name)
#                 except Runner.DoesNotExist:
#                     runner = Runner.objects.get(racecard=racecard, race_number=race_number, name__iexact='AE - {}'.format(horse_name))

#                 result_node = horseEL.find('Result')
#                 casualty_node = horseEL.find('Casualty')
#                 if result_node is None and casualty_node is None and runner.scratched == False:
#                     missing_data = True
#                     break

#                 dq = False
#                 if result_node is not None:
#                     dq = result_node.attrib['disqualified'] != 'No'

#                 finish_pos = 0
#                 btn_distance = '0 lengths'

#                 if dq or runner.scratched:
#                     finish_pos = 1000
#                 elif casualty_node is None:
#                     finish_pos = int(result_node.attrib['finishPos'])
#                     if finish_pos > 1:
#                         btn_distance = result_node.attrib['btnDistance']

#                 runner.disqualified = dq
#                 runner.finish = finish_pos
#                 # the first runner gets its lengths ahead from the second runners lengths behind
#                 if casualty_node is not None:
#                     runner.finish = 0
#                     runner.lengths_behind = 9999
#                     runner.lengths_ahead = 9999
#                 elif dq is False and finish_pos > 1 and finish_pos != 1000:
#                     lengths_behind = 0
#                     if btn_distance.lower() in self.length_name_map:
#                         lengths_behind = self.length_name_map[btn_distance.lower()]
#                     else:
#                         # parse it
#                         btn_distance = btn_distance[0:btn_distance.index('l') - 1]
#                         if ' ' in btn_distance:
#                             whole_num = int(btn_distance[0:btn_distance.index(' ')])
#                             fraction_str = btn_distance[btn_distance.index(' ') + 1:]
#                             fraction = Fraction(fraction_str)
#                             lengths_behind = whole_num + fraction
#                         else:
#                             lengths_behind = Fraction(btn_distance)
#                         lengths_behind = int(float(lengths_behind) * 100)

#                     runners_length_behind[runner.pk] = lengths_behind

#                 if finish_pos == 1:
#                     first_runner = runner
#                 elif finish_pos == 2:
#                     second_runner = runner

#                 runners.append(runner)
            
#             if missing_data:
#                 return Response(request.data, status=status.HTTP_201_CREATED)
                       
#             for runner in runners:
#                 if (runner.pk not in runners_length_behind):
#                     continue

#                 lengths_behind = runners_length_behind[runner.pk]
#                 if (runner.finish == 1 or runner.finish == 0 or runner.finish == 1000):
#                     continue

#                 total_lengths_behind = lengths_behind
#                 for runner2 in runners:
#                     if (runner2.pk not in runners_length_behind):
#                         continue

#                     lengths_behind2 = runners_length_behind[runner2.pk]
#                     if (runner2.finish == 1 or runner2.finish == 0 or runner2.finish == 1000 or runner2.finish >= runner.finish):
#                         continue

#                     total_lengths_behind = total_lengths_behind + lengths_behind2
                
#                 runner.lengths_behind = total_lengths_behind

#             first_runner.lengths_ahead = second_runner.lengths_behind
#             for runner in runners:
#                 runner.save()

#             race['results_are_in'] = True
#             race['status'] = Racecard.OFFICIAL
#             racecard.save()

#             calculate_race_scores(runners)

#             #Get all of the races for the racecard
#             last_race_number = 1
#             for race in racecard.races:
#                 if(int(race["race_number"]) > last_race_number):
#                     last_race_number = int(race["race_number"])
     
#             #Go through the Racecard and determine if every race has official results and 
#             #has been completed. If so, kick off the Game Finished task. 
            
#             #EDGE CASE: What if Final Race is Cancelled before results for a previous race come in? The Game
#             #won't be cancelled in the Change Import above because the results aren't in for a previous race so 
#             #we need to do it here.

#             races_completed = False
#             for race in racecard.races:
#                 if race['results_are_in'] == False or race['status'] != Racecard.OFFICIAL:
#                     if int(race['race_number']) == last_race_number and race['status'] == Racecard.CANCELLED: 
#                         #last race is cancelled. We can still possibly finish the game.
#                         continue
#                     else:
#                         races_completed = False

#             games = Game.objects.filter(racecard_id=racecard.id)

#             if races_completed == True:
#                 for game in games:
#                     if not game.finished:
#                         finish_game(game.id)

#             for game in games:
#                 calculate_scores_ranks(game)

#         return Response(request.data, status=status.HTTP_201_CREATED)

# class EquibaseImportResultsView(CreateAPIView):
#     parser_classes = (RacecardParser,)

#     def post(self, request, format=None):
#         log.debug('START RESULTS IMPORT')
#         root = ET.fromstring(request.data)

#         track_node = xml_to_dict(root.find("Track"))

#         race_date = root.find('RaceDate').text.split('+')[0]
#         race_number = root.find('RaceNumber').text
#         official_results = False

#         with transaction.atomic():

#             try:
#                 track = Track.objects.get(code=track_node['TrackID'])

#                 #nowait=True below will cause an exception to occur if the database record
#                 #is already locked by the Official import below. That's fine. We don't
#                 #want this to process if that's the case anyway.
#                 racecard = Racecard.objects.select_for_update(nowait=True).get(track=track, race_date=race_date)
#                 log.debug("RACE DATE: %s" % race_date)
#                 log.debug("TRACK CREATED: %s" % track_node['TrackID'])
#                 official_already_in = False

#                 for node in root:
#                     if node.tag == 'RaceNumber':
#                         for i in racecard.races:
#                             if i['race_number'] == node.text:
#                                 if i['status'] == Racecard.OFFICIAL:
#                                     official_already_in = True
#                                     break
                                
#                                 i['results_are_in'] = True
#                                 break
#                     #On rare occasions the CHARTD file will beat the FLASHD file. We shouldn't
#                     #process the FLASHD if that's the case.
#                     if official_already_in == True:
#                         break
#                     if node.tag == 'Chart':
#                         parse_chart(race_number, racecard, node, official_results)
                
#                 if official_already_in == False:
#                     racecard.save()
                    
#                     games = Game.objects.filter(racecard_id=racecard.id)
#                     for game in games:
#                         calculate_scores_ranks(game)

#             except OperationalError:
#                 log.debug("Racecard Already Updating: Racecard: track=%s race_date=%s" % (track_node, race_date))
#             except Track.DoesNotExist:
#                 log.debug("DOES NOT EXIST: Track: %s" % track_node)
#             except Racecard.DoesNotExist:
#                 log.debug("DOES NOT EXIST: Racecard: track=%s race_date=%s" % (track_node, race_date))

#         return Response(request.data, status=status.HTTP_201_CREATED)

class EquibaseImportResultsView(CreateAPIView):
    parser_classes = (RacecardParser,)

    def post(self, request, format=None):
        log.debug('START RESULTS IMPORT')
        root = ET.fromstring(request.data)

        track_node = xml_to_dict(root.find("Track"))

        race_date = root.find('RaceDate').text.split('+')[0]
        race_number = root.find('RaceNumber').text
        official_results = True

        with transaction.atomic():
            try:
                track = Track.objects.get(code=track_node['TrackID'])

                #Without nowait=True, this will actually wait until the above is finished if it 
                #already has a Lock on the db record.
                racecard = Racecard.objects.select_for_update().get(track=track, race_date=race_date)
                log.debug("RACE DATE: %s" % race_date)
                log.debug("TRACK CREATED: %s" % track_node['TrackID'])

                for node in root:
                    if node.tag == 'RaceNumber':
                        for i in racecard.races:
                            if i['race_number'] == node.text:
                                i['status'] = Racecard.OFFICIAL
                                #Go ahead and save to prevent any issues with FLASHD coming in next.
                                racecard.save()
                                break
                    if node.tag == 'Chart':
                        parse_chart(race_number, racecard, node, official_results)
                
                racecard.save()
     
                #Get all of the races for the racecard
                last_race_number = 1
                for race in racecard.races:
                    if(int(race["race_number"]) > last_race_number):
                        last_race_number = int(race["race_number"])
     
                #Go through the Racecard and determine if every race has official results and 
                #has been completed. If so, kick off the Game Finished task. 
                
                #EDGE CASE: What if Final Race is Cancelled before results for a previous race come in? The Game
                #won't be cancelled in the Change Import above because the results aren't in for a previous race so 
                #we need to do it here.

                races_completed = True
                for race in racecard.races:
                    if race['results_are_in'] == False or race['status'] != Racecard.OFFICIAL:
                        if int(race['race_number']) == last_race_number and race['status'] == Racecard.CANCELLED: 
                            #last race is cancelled. We can still possibly finish the game.
                            continue
                        else:
                            races_completed = False

                games = Game.objects.filter(racecard_id=racecard.id)

                if races_completed == True:
                    for game in games:
                        if not game.finished:
                            finish_game(game.id)

                for game in games:
                    calculate_scores_ranks(game)

            except Track.DoesNotExist:
                log.debug("DOES NOT EXIST: Track: %s" % track_node)
            except Racecard.DoesNotExist:
                log.debug("DOES NOT EXIST: Racecard: track=%s race_date=%s" % (track_node, race_date))

        return Response(request.data, status=status.HTTP_201_CREATED)




class EquibaseImportOfficialResultsView(CreateAPIView):
    parser_classes = (RacecardParser,)

    def post(self, request, format=None):
        log.debug('START RESULTS IMPORT')
        root = ET.fromstring(request.data)

        track_node = xml_to_dict(root.find("Track"))

        race_date = root.find('RaceDate').text.split('+')[0]
        race_number = root.find('RaceNumber').text
        official_results = True

        with transaction.atomic():
            try:
                track = Track.objects.get(code=track_node['TrackID'])

                #Without nowait=True, this will actually wait until the above is finished if it 
                #already has a Lock on the db record.
                racecard = Racecard.objects.select_for_update().get(track=track, race_date=race_date)
                log.debug("RACE DATE: %s" % race_date)
                log.debug("TRACK CREATED: %s" % track_node['TrackID'])

                for node in root:
                    if node.tag == 'RaceNumber':
                        for i in racecard.races:
                            if i['race_number'] == node.text:
                                i['results_are_in'] = True
                                i['status'] = Racecard.OFFICIAL
                                #Go ahead and save to prevent any issues with FLASHD coming in next.
                                racecard.save()
                                break
                    if node.tag == 'Chart':
                        parse_chart(race_number, racecard, node, official_results)
                
                racecard.save()
     
                #Get all of the races for the racecard
                last_race_number = 1
                for race in racecard.races:
                    if(int(race["race_number"]) > last_race_number):
                        last_race_number = int(race["race_number"])
     
                #Go through the Racecard and determine if every race has official results and 
                #has been completed. If so, kick off the Game Finished task. 
                
                #EDGE CASE: What if Final Race is Cancelled before results for a previous race come in? The Game
                #won't be cancelled in the Change Import above because the results aren't in for a previous race so 
                #we need to do it here.

                races_completed = True
                for race in racecard.races:
                    if race['results_are_in'] == False or race['status'] != Racecard.OFFICIAL:
                        if int(race['race_number']) == last_race_number and race['status'] == Racecard.CANCELLED: 
                            #last race is cancelled. We can still possibly finish the game.
                            continue
                        else:
                            races_completed = False

                games = Game.objects.filter(racecard_id=racecard.id)

                if races_completed == True:
                    for game in games:
                        if not game.finished:
                            finish_game(game.id)

                for game in games:
                    calculate_scores_ranks(game)

            except Track.DoesNotExist:
                log.debug("DOES NOT EXIST: Track: %s" % track_node)
            except Racecard.DoesNotExist:
                log.debug("DOES NOT EXIST: Racecard: track=%s race_date=%s" % (track_node, race_date))

        return Response(request.data, status=status.HTTP_201_CREATED)






class HarnessImportOfficialResultsView(CreateAPIView):
    parser_classes = (RacecardParser,)

    def post(self, request, format=None):
        log.debug('START RESULTS IMPORT')
        root = ET.fromstring(request.data)
        
        track_node = xml_to_dict(root.find("TRACK"))
        race_date = root.attrib['RACE_DATE']
        raceEL = root.findall('RACE')
        official_results = True
        code=track_node['CODE'].strip()
        track_detail = HarnessTracksDetail.objects.get(code=code)
        code = track_detail.trackmastercode

       
        for race in raceEL:
            race_number = race.attrib['NUMBER'] 
            with transaction.atomic():
                try:
                    track = Track.objects.get(code=code)
                    #Without nowait=True, this will actually wait until the above is finished if it 
                    #already has a Lock on the db record.
                    racecard = Racecard.objects.select_for_update().get(track=track, race_date=race_date)
                    
                    log.debug("RACE DATE: %s" % race_date)
                    log.debug("TRACK CREATED: %s" % track_node['CODE'])

                    
                    for i in racecard.races:
                        if i['race_number'] == race_number:
                            i['results_are_in'] = True
                            i['status'] = Racecard.OFFICIAL
                            #Go ahead and save to prevent any issues with FLASHD coming in next.
                            racecard.save()
                            
                    starters_element = race.find('STARTERS')
                    if race.find('STARTERS'):
                        parse_chart_harness(race_number, racecard, starters_element, official_results)
                    racecard.save()

                    
                    
                    #Get all of the races for the racecard
                    last_race_number = 1
                    for race in racecard.races:
                        
                        if(int(race["race_number"]) > last_race_number):
                            
                            last_race_number = int(race["race_number"])
        
                    #Go through the Racecard and determine if every race has official results and 
                    #has been completed. If so, kick off the Game Finished task. 
                    
                    #EDGE CASE: What if Final Race is Cancelled before results for a previous race come in? The Game
                    #won't be cancelled in the Change Import above because the results aren't in for a previous race so 
                    #we need to do it here.

                    races_completed = True
                    for race in racecard.races:
                        if race['results_are_in'] == False or race['status'] != Racecard.OFFICIAL:
                            if int(race['race_number']) == last_race_number and race['status'] == Racecard.CANCELLED: 
                                #last race is cancelled. We can still possibly finish the game.
                                
                                continue
                            else:
                                races_completed = False

                    games = Game.objects.filter(racecard_id=racecard.id)
                    
                    if races_completed == True:
                        for game in games:
                            if not game.finished:
                                finish_game(game.id)

                    for game in games:
                        calculate_scores_ranks(game)

                except Track.DoesNotExist:
                    log.debug("DOES NOT EXIST: Track: %s" % track_node)
                except Racecard.DoesNotExist:
                    log.debug("DOES NOT EXIST: Racecard: track=%s race_date=%s" % (track_node, race_date))

        return Response(request.data, status=status.HTTP_201_CREATED)














class PAImportOfficialResultsView(CreateAPIView):
    parser_classes = (RacecardAppXmlParser,)
    length_name_map = {
        'short head': 5,
        'nose': 5,
        'head': 10,
        'neck': 25,
        'dead heat':0,
    }
    def post(self, request, format=None):
        log.debug('START RESULTS IMPORT')
        root = ET.fromstring(request.data)
        if root.tag != 'HorseRacing':
            log.debug('Not B FILE')
            return Response(request.data, status=status.HTTP_200_OK)
        meeting_node = root.find("Meeting")
        race_node = root.find("Meeting/Race")

        if (race_node is None):
            log.debug('RACE NODE IS NONE')
            return Response(request.data, status=status.HTTP_200_OK)
        
        course = meeting_node.attrib['course']
        track_detail= PATracksDetail.objects.get(name=course)
        track_code = track_detail.code
        name = track_detail.name
        country = track_detail.country
        # track_code_mapped = course.lower()
        if not track_code:
            log.debug('NOT VALID TRACK CODE')
            return Response(request.data, status=status.HTTP_200_OK)
        if (track_code is None):
            log.debug('TRACK CODE IS NONE')
            return Response(request.data, status=status.HTTP_200_OK)

        track = None
        meeting_date = None
        racecard = None

        try:
            track = Track.objects.get(code=track_code)
            meeting_date = datetime.strptime(meeting_node.attrib['date'], '%Y%m%d')
            race_date=meeting_date
            racecard = Racecard.objects.get(track=track, race_date=meeting_date)
        except Track.DoesNotExist:
            log.debug('TRACK DOES NOT EXIST')
            return Response(request.data, status=status.HTTP_200_OK)
        
        except Racecard.DoesNotExist:
            log.debug('RACE CARD DOES NOT EXIST')
            return Response(request.data, status=status.HTTP_200_OK)

        if (track is None or racecard is None):
            
            log.debug('EITHER TRACK OR RACECARD IS NONE')
            return Response(request.data, status=status.HTTP_200_OK)
    
        race_date = datetime.strptime(race_node.attrib['date'], '%Y%m%d')
        race_time_text = race_node.attrib['time'].split('+')[0]
        time_change = race_node.attrib['time'].split('+')[1]
        if '+' in race_node.attrib['time']:
                # time_delta = datetime.strptime(time_change, '%H%M')
                time_delta = timedelta(hours=int(time_change[:2]), minutes=int(time_change[2:]))
                
        elif '-' in race_node.attrib['time']:
            
            time_delta = timedelta(hours=int(time_change[:2]), minutes=int(time_change[2:]))
            time_delta = -(time_delta)

        race_time = datetime.strptime(race_time_text, '%H%M')
        race_time = race_time - time_delta
        race_time_search = race_time.strftime("%I:%M%p")
        race_date_search = race_date.strftime("%Y-%m-%d")
        log.debug(race_time_search)
        race = None
        race_number = 0
        for race in racecard.races:
            if race['post_time'] == race_time_search and race['adjusted_date'] == race_date_search:

                race = race
                race_number = race['race_number']
                break

        if race_number == 0:
            log.debug('RACE NUMBER EQUAL TO 0')
            return Response(request.data, status=status.HTTP_200_OK)

        for horseEL in root.findall('Meeting/Race/Horse'):
            horse_name = horseEL.attrib['name']
            horse_status = horseEL.attrib['status']
            
            if horse_status != 'NonRunner':
                continue

            try:
                runner = Runner.objects.get(racecard=racecard, race_number=race_number, name__iexact=horse_name)
            except Runner.DoesNotExist:
                runner = Runner.objects.get(racecard=racecard, race_number=race_number, name__iexact='AE - {}'.format(horse_name))

            if not runner.scratched:
                runner.scratched = True
                games = Game.objects.filter(racecard_id=racecard.id)
                runner.scratched_datetime = datetime.now()
                #Send the notification to every game that includes this racecard that contains the specified runner
                for game in games:
                    send_scratch_notifications.delay(runner.id, game.id)
                runner.save()

        win_node = root.find('Meeting/Race/WinTime')
        winning_distances = root.findall('Meeting/Race/WinningDistance')
        #  and race['status'] != Racecard.OFFICIAL
        race_status = race_node.attrib['status']
        if win_node is not None and len(winning_distances) > 0:
           
            missing_data = False
            first_runner = None
            second_runner = None
            runners = []
            runners_length_behind = {}
            for horseEL in root.findall('Meeting/Race/Horse'):
                horse_name = horseEL.attrib['name']

                try:
                    
                    runner = Runner.objects.get(racecard=racecard, race_number=race_number, name__iexact=horse_name)
                except Runner.DoesNotExist:
                    print("========================================")
                    print (horse_name)
                    print (race_number)
                    print (racecard)
                    runner = Runner.objects.get(racecard=racecard, race_number=race_number, name__iexact='AE - {}'.format(horse_name))

                result_node = horseEL.find('Result')
                casualty_node = horseEL.find('Casualty')
                if result_node is None and casualty_node is None and runner.scratched == False:
                    missing_data = True
                    break

                dq = False
                if result_node is not None:
                    dq = result_node.attrib['disqualified'] != 'No'

                finish_pos = 0
                btn_distance = '0 lengths'

                if dq or runner.scratched:
                    finish_pos = 1000
                elif casualty_node is None:
                    finish_pos = int(result_node.attrib['finishPos'])
                    if finish_pos > 1:
                        try:
                            btn_distance = result_node.attrib['btnDistance']
                        except:
                             btn_distance = "0 lengths"

                runner.disqualified = dq
                runner.finish = finish_pos
                # the first runner gets its lengths ahead from the second runners lengths behind
                if casualty_node is not None:
                    runner.finish = 0
                    runner.lengths_behind = 9999
                    runner.lengths_ahead = 9999
                elif dq is False and finish_pos > 1 and finish_pos != 1000:
                    lengths_behind = 0
                    if btn_distance.lower() in self.length_name_map:
                        lengths_behind = self.length_name_map[btn_distance.lower()]
                    else:
                        # parse it
                        btn_distance = btn_distance[0:btn_distance.index('l') - 1]
                        if ' ' in btn_distance:
                            whole_num = int(btn_distance[0:btn_distance.index(' ')])
                            fraction_str = btn_distance[btn_distance.index(' ') + 1:]
                            fraction = Fraction(fraction_str)
                            lengths_behind = whole_num + fraction
                        else:
                            lengths_behind = Fraction(btn_distance)
                        lengths_behind = int(float(lengths_behind) * 100)

                    runners_length_behind[runner.pk] = lengths_behind

                if finish_pos == 1:
                    first_runner = runner
                elif finish_pos == 2:
                    second_runner = runner

                runners.append(runner)
            
            if missing_data:
                log.debug('MISSING DATA')
                return Response(request.data, status=status.HTTP_201_CREATED)
                       
            for runner in runners:
                if (runner.pk not in runners_length_behind):
                    continue

                lengths_behind = runners_length_behind[runner.pk]
                if (runner.finish == 1 or runner.finish == 0 or runner.finish == 1000):
                    continue

                total_lengths_behind = lengths_behind
                for runner2 in runners:
                    if (runner2.pk not in runners_length_behind):
                        continue

                    lengths_behind2 = runners_length_behind[runner2.pk]
                    if (runner2.finish == 1 or runner2.finish == 0 or runner2.finish == 1000 or runner2.finish >= runner.finish):
                        continue

                    total_lengths_behind = total_lengths_behind + lengths_behind2
                
                runner.lengths_behind = total_lengths_behind
            
            if first_runner and second_runner:
                first_runner.lengths_ahead = second_runner.lengths_behind   
            for runner in runners:
                runner.save()

            race['results_are_in'] = True
            race['status'] = Racecard.OFFICIAL
            log.debug(' status == 0')
            racecard.save()
            log.debug(' race_number == 0')
            race_number
            calculate_race_scores(runners)

            #Get all of the races for the racecard
            last_race_number = 1
            for race in racecard.races:
                if(int(race["race_number"]) > last_race_number):
                    last_race_number = int(race["race_number"])
     
            #Go through the Racecard and determine if every race has official results and 
            #has been completed. If so, kick off the Game Finished task. 
            
            #EDGE CASE: What if Final Race is Cancelled before results for a previous race come in? The Game
            #won't be cancelled in the Change Import above because the results aren't in for a previous race so 
            #we need to do it here.

            races_completed = False
            for race in racecard.races:
                if race['results_are_in'] == False or race['status'] != Racecard.OFFICIAL:
                    if int(race['race_number']) == last_race_number and race['status'] == Racecard.CANCELLED: 
                        #last race is cancelled. We can still possibly finish the game.
                        continue
                    else:
                        races_completed = False

            games = Game.objects.filter(racecard_id=racecard.id)

            if races_completed == True:
                for game in games:
                    if not game.finished:
                        finish_game(game.id)

            for game in games:
                calculate_scores_ranks(game)
        if race_status == "Abandoned":
            race['status'] = Racecard.CANCELLED
            racecard.save()
        log.debug('FINISHED IMPORT')
        return Response(request.data, status=status.HTTP_201_CREATED)

class TrackmasterImportView(CreateAPIView):
    parser_classes = (RacecardParser,)

    def post(self, request, format=None):
        log.debug('START TRACKMASTER IMPORT')
        root = ET.fromstring(request.data)

        try:
            for raceEL in root.findall('racedata'):
                race_date = raceEL.find('race_date').text
                if(type(race_date) == str):
                    race_date = datetime.strptime(race_date, '%Y%m%d')

                race_number = raceEL.find('race').text
                track_code = raceEL.find('track').text
                track_country = raceEL.find('country').text
                todays_class = raceEL.find('todays_cls').text
                track = Track.objects.get(code=track_code, country=track_country)
                racecard = Racecard.objects.get(track=track, race_date=race_date)
                runners = []
                for horseEL in raceEL.findall('horsedata'):
                    #Find the appropriate runner
                    try:
                        runner = Runner.objects.get(racecard=racecard, race_number=race_number, post_position=int(horseEL.find('pp').text), program_number=horseEL.find('program').text)
                        ave_cls_sd = horseEL.find('ave_cl_sd').text
                        pfigfin = horseEL.find('pfigfin').text
                        convert = "NA" if ave_cls_sd == "NA" else Decimal(pfigfin)/Decimal(10) - ((Decimal(ave_cls_sd)-Decimal(todays_class))*Decimal(.5))
                        runners.append([runner,convert])
                    except Runner.DoesNotExist:
                        log.debug("DOES NOT EXIST: Runner: %s" % horseEL) 

                #Get the lowest 'convert' value from the multi-dimensional array
                lowest_convert_value = Decimal('Inf')
                for record in runners:
                    if(record[1] != "NA" and record[1] < lowest_convert_value):
                        lowest_convert_value = record[1]

                normal_factor = 1 - lowest_convert_value
                for record in runners:
                    if(record[1] != "NA"):
                        normal = record[1] + normal_factor
                        projected_bl = (normal-Decimal(1))*Decimal(0.75)
                        if(projected_bl < Decimal(2.5)):
                            record[0].custom_stats['risk'] = "Low"
                        elif (projected_bl >= Decimal(2.5) and projected_bl < Decimal(5)):
                            record[0].custom_stats['risk'] = "Medium"
                        else:
                            record[0].custom_stats['risk'] = "High"
                        record[0].save()
      
        except Track.DoesNotExist:
            log.debug("DOES NOT EXIST: Track: %s" % track_code)
        except Racecard.DoesNotExist:
            log.debug("DOES NOT EXIST: Racecard: track=%s race_date=%s" % (track_code, race_date))

        return Response(request.data, status=status.HTTP_201_CREATED)

class TrackImportView(CreateAPIView):
    parser_classes = (RacecardAppXmlParser,)
    def post(self, request, format=None):
        log.debug('Start Track Import')
        root = ET.fromstring(request.data)
        # try:
        created_tracks_count = 0
        for trackEL in root.findall('track'):
            track_name = trackEL.text
            track_code = trackEL.find("trackmasterCode").text.strip()
            track_country = trackEL.find('country').text.strip()
            now = datetime.now()
            _, created = Track.objects.get_or_create(code=track_code, defaults={"name":track_name, "country":track_country,"opened":now})
            if(created == True):
                created_tracks_count+=1
        log.debug("Track import complete. Imported {} tracks".format(created_tracks_count))
        return Response(created_tracks_count, status=status.HTTP_201_CREATED)    


class TrackmasterHarnessImportView(CreateAPIView):
    parser_classes = (RacecardParser,)

    def post(self, request, format=None):
        log.debug('START Harness IMPORT')
        root = ET.fromstring(request.data)
        track_dataEL = root.find ('trackdata')
        race_dataEL = track_dataEL.find('racedata')
        race_date = race_dataEL.find('racedate').text
        track_code = track_dataEL.find('track').text
        

        try:
            for raceEL in track_dataEL.findall('racedata'):
                race_date = raceEL.find('racedate').text
                if(type(race_date) == str):
                    race_date = datetime.strptime(race_date, '%Y-%m-%d').date()
                    
                race_number = raceEL.find('race').text
                track_code = raceEL.find('track').text
                track_country = "USA"
                try:
                    track_detail = HarnessTracksDetail.objects.get(code=track_code)
                    track_name = track_detail.name
                    track_code = track_detail.trackmastercode
                    track_country = track_detail.country
                except BaseException as e:
                    log.debug("DOES NOT EXIST: Track: %s" % track_code)

                todays_class = raceEL.find('todays_cr').text
                track = Track.objects.get(code=track_code, country=track_country)
                racecard = Racecard.objects.get(track=track, race_date=race_date)
                runners = []
                for horseEL in raceEL.findall('horsedata'):
                    #Find the appropriate runner
                    try:
                        runner = Runner.objects.get(racecard=racecard, race_number=race_number, post_position=int(horseEL.find('pp').text), program_number=horseEL.find('program').text)
                        sc_avgcr = horseEL.find('sc_avgcr').text
                        pc_fig_cp = horseEL.find('pc_fig_cp').text
                        convert = "NA" if sc_avgcr == "NA" else Decimal(pc_fig_cp)/Decimal(10) - ((Decimal(sc_avgcr)-Decimal(todays_class))*Decimal(.5))
                        
                        runners.append([runner,convert])
                    except Runner.DoesNotExist:
                        log.debug("DOES NOT EXIST: Runner: %s" % horseEL) 

                #Get the lowest 'convert' value from the multi-dimensional array
                lowest_convert_value = Decimal('Inf')
                for record in runners:
                    if(record[1] != "NA" and record[1] < lowest_convert_value):
                        lowest_convert_value = record[1]

                normal_factor = 1 - lowest_convert_value
                for record in runners:
                    if(record[1] != "NA"):
                        normal = record[1] + normal_factor
                        projected_bl = (normal-Decimal(1))*Decimal(0.75)
                        if(projected_bl < Decimal(2.5)):
                            if record[0].custom_stats:
                                record[0].custom_stats['risk'] = "Low"
                            else:
                                continue
                        elif (projected_bl >= Decimal(2.5) and projected_bl < Decimal(5)):
                            if record[0].custom_stats:
                                record[0].custom_stats['risk'] = "Medium"
                            else:
                                continue
                        else:
                            if record[0].custom_stats:
                                record[0].custom_stats['risk'] = "High"
                            else:
                                continue
                        record[0].save()
      
        except Track.DoesNotExist:
            log.debug("DOES NOT EXIST: Track: %s" % track_code)
        except Racecard.DoesNotExist:
            log.debug("DOES NOT EXIST: Racecard: track=%s race_date=%s" % (track_code, race_date))

        return Response(request.data, status=status.HTTP_201_CREATED)




def parse_chart(race_number, racecard, chart_node, official_results):
    #Update all of the Runners based on the Chart
    

    runners = []
    for node in chart_node:
        if node.tag == 'Start':
            
            runner = parse_start(race_number, racecard, node)
            if (runner is not None):
                runners.append(runner)

    calculate_race_scores(runners)



def parse_chart_harness(race_number, racecard, chart_node, official_results):
    #Update all of the Runners based on the Chart
    

    runners = []
    for node in chart_node:
        if node.tag == 'STARTER':
            
            runner = parse_start_harness(race_number, racecard, node)
            if (runner is not None):
                runners.append(runner)

    calculate_race_scores(runners)





def calculate_race_scores(runners):
    
    #Now check to see if any of the runners have been DQ'd and adjust their Lengths Behind accordingly
    #We can't do it while we're parsing the individual runners because we're not sure about the order
    #that we're receiving the entries

    #Yes, we have to go through the list of runners three different occasions if a DQ exists
    dq = False
    adjusted_lengths_behind = 0
    for runner in runners:
        if(runner.disqualified is not None and runner.disqualified == True):
            dq = True
        if(runner.finish is not None and runner.finish == 1):
            adjusted_lengths_behind = runner.lengths_behind

    if dq == True:

        #Adjust every runner's lengths behind based on moving the new #1 
        for runner in runners:
            runner.lengths_behind -= adjusted_lengths_behind
            
            runner.save()

        #Adjust DQ'd runners lengths behind even further
        for runner in runners:
            #If any runner in the group is disqualified, we need to adjust the lengths back for every runner
            if(runner.disqualified == True):
                #Get the finish position ahead of our DQ'd runner and set lengths behind to be the same
                finish_position = runner.finish - 1
                if(finish_position > 1):
                    for runner2 in runners:
                        if(runner2.finish == finish_position):
                            runner.lengths_behind = runner2.lengths_behind
                            
                            runner.save()
                            break


    #Now we have to go through the runners and account for those that Did Not Finish
    #Per equibase, this is determined with a LengthsBehind and LengthsAhead of 9999
    #StableDuel would like them to be 5 lengths behind the last horse that actually finished. 
    for runner in runners:
        # print (runner.lengths_behind)
        # print (runner.lengths_ahead)
        #If any runner in the group DNF, make the lengths behind equal to the next runner that did finish
        if(runner.lengths_behind == 9999 or runner.lengths_ahead == 9999):
            #Get the finish position ahead of our DNF runner
            finish_position = runner.finish - 1
            if(finish_position > 1):
                for runner2 in runners:
                    if(runner2.finish == finish_position):
                        #We add 500 to the lengths behind because that will give an effective
                        #score subtraction of 5 points (which is desired by SD)
                        runner.lengths_behind = runner2.lengths_behind + 500
                        runner.save()
                        break


    #Finally, after all of the lengths and dqs have been determined, go ahead and set the score for the runner
    for runner in runners:
        if runner.points is None or runner.margin is None:
            runner.score = 0
        else:
            runner.score = max( -30, round(runner.points + runner.margin, 2 ) )

        #Set the score for the Horse in HorsePoint so that it can be used for the Follows functionality
        horse_point, _ = HorsePoint.objects.get_or_create(external_id=runner.external_id, defaults={'points':0,'count':0})
        horse_point.points += Decimal(runner.score)
        horse_point.count +=1
        horse_point.save()

        runner.save()

    #Finally, finally -- check to see if any of the runners are Coupled.  If so, take the max of the group of Runners
    #coupled_runners = []
    coupled_runners = defaultdict(list)

    for runner in runners:
        if(runner.coupled == True):
            coupled_runners[runner.coupled_indicator].append(runner)

    for coupled_indicator_value in coupled_runners:
        max_score = -30
        for coupled_runner in coupled_runners[coupled_indicator_value]:
            if coupled_runner.scratched == False and coupled_runner.score > max_score:
                max_score = coupled_runner.score

        for coupled_runner in coupled_runners[coupled_indicator_value]:
            coupled_runner.score = max_score
            coupled_runner.save()

    #Reset the cache for Stable Scores
    calculate_global_leaderboard()

def parse_start(race_number, racecard, start):
    horse_name = start.find('Horse/HorseName').text
    if '(' in horse_name:
        horse_name = horse_name[0:horse_name.index('(') - 1]
    registration_number = start.find('Horse/RegistrationNumber').text
    horse_id = horse_util.get_horse_id(horse_name)
    try:
        try:
            runner = Runner.objects.get(racecard=racecard, race_number=race_number, name=horse_name)
        except Runner.DoesNotExist:
            runner = Runner.objects.get(racecard=racecard, race_number=race_number, name='AE - {}'.format(horse_name))
        runner_finish = start.find('OfficialFinish').text
        if(runner_finish == 0):
            runner_finish = 1000
        runner.finish = int(runner_finish)

        for point_of_call in start.findall('PointOfCall'):
            if(point_of_call.find('PointOfCall').text == 'F'):
                runner.lengths_behind = Decimal(point_of_call.find('LengthsBehind').text)
                runner.lengths_ahead = Decimal(point_of_call.find('LengthsAhead').text)
                break

        if(start.find('DQIndicator').text == 'Y'):
            runner.disqualified = True


        runner.save()
        return runner
    except Runner.DoesNotExist:
        log.debug("DOES NOT EXIST: (Results) Runner: %s" % horse_id)


def parse_start_harness(race_number, racecard, start):
    horse_name = start.find('HORSE_NAME').text
    if '(' in horse_name:
        horse_name = horse_name[0:horse_name.index('(') - 1]
    registration_number = start.find('REGISTRATION_NUM').text
    horse_id = horse_util.get_horse_id(horse_name)
    try:
        try:
            runner = Runner.objects.get(racecard=racecard, race_number=race_number, name=horse_name.upper())
        except Runner.DoesNotExist:
            runner = Runner.objects.get(racecard=racecard, race_number=race_number, name='AE - {}'.format(horse_name))
        runner_finish = start.find('FINISH/FINISHPOC/Official').text
        
        if(runner_finish == 0):
            runner_finish = 1000
        runner.finish = int(runner_finish)

        if runner_finish == "1":
            runner.lengths_ahead = Decimal(start.find('FINISH/FINISHPOC/Lengths').text)
            runner.lengths_behind= Decimal (0)
            
        else :
            runner.lengths_behind = Decimal(start.find('FINISH/FINISHPOC/Lengths').text)
            runner.lengths_ahead = Decimal (0)
            
        # if(start.find('DQIndicator').text == 'Y'):
        #     runner.disqualified = True

        runner.save()
        return runner
    except Runner.DoesNotExist:
        log.debug("DOES NOT EXIST: (Results) Runner: %s" % horse_id)



def xml_to_dict(xml):

    d = {}
    for e in xml:
        if e.text is not None:
            d[e.tag] = e.text

    return d











