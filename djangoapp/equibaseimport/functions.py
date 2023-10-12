# import base64
# import requests
# from rest_framework import status
# from django.db import models, transaction
# from rest_framework.response import Response

# from decimal import *
# from . import horse_util
# from collections import defaultdict
# from horse_points.models import HorsePoint
# from stables.models import Runner, calculate_scores_ranks, get_runner_points
# from racecards.models import Track, Racecard, HarnessTracksDetail, PATracksDetail

# # from http im
# import logging
# log = logging.getLogger()
# from games.models import Game
# from games.tasks import finish_game, cancel_game
# from stable_points.tasks import calculate_global_leaderboard


# def harness_result(track_code):
#     session = requests.Session()
#     username = "stableduel"
#     password = "testsd@api"
#     PA_race_id=1251791
#     race_date = 20230817
#     api_url1 = "https://oauth-ca.ustrotting.com/connect/token"  # Replace with the actual API URL
#     auth_header = {"Authorization": "Basic " + (base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8"))}
#     # Prepare the request headers
#     # headers.update(auth_header)
#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded",
#         "Accept": "*/*",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Connection": "keep-alive",
#     }
#     body ={
#         "grant_type":"client_credentials"
#     }
#     headers.update(auth_header)
#     # Send GET request to the API
#     response1=session.post(api_url1, headers=headers, data=body)
#     json = response1.json()


#     if json is not None:
#             token = json['access_token']
            
#                 # pa_race_id= meeting['race']['returns']['pA_RACEID']
#                 # if pa_race_id == race_id:
#                 #     horses=meeting['race']['returns']['return']
#                 #     print (horses)
            
#     api_url2 = "https://uws-ca.ustrotting.com/api/Results/racing/pcd/Results/condensed/8-20-2023"  # Replace with the actual API URL

#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded",
#         "Accept": "*/*",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Connection": "keep-alive",
#     }

#     if token:
#         auth_header = {"Authorization": "Bearer " + token}

#     headers.update(auth_header)
#     if response1.status_code == 200:
#      response2=session.get(api_url2, headers=headers)
#     else:
#         print ("AUTHORIZATION ERROR")
#         return Response(response1.data, status=status.HTTP_400_BAD_REQUEST)
#     try:
#         json2 = response2.json()
#     except:
#         print ("RESULT EXCEPTION")
#         return Response(response2.data, status=status.HTTP_200_OK)
#     if json2 is not None:
#             for result in json2:
#                 raceDate=result['raceDate'].strftime("%Y%m%d")
#                 if track_code == result['trackCode'] and race_date == raceDate:
#                         official_results = True
#                         with transaction.atomic():
#                             try:
#                                 track = Track.objects.get(code=track_code)

#                                 #Without nowait=True, this will actually wait until the above is finished if it 
#                                 #already has a Lock on the db record.
#                                 racecard = Racecard.objects.select_for_update().get(track=track, race_date=race_date)
#                                 log.debug("RACE DATE: %s" % race_date)
#                                 log.debug("TRACK CREATED: %s" % result['trackCode'])
#                                 raceNo=result['raceNo']
#                                 for i in racecard.races:
#                                     if i['race_number'] == result['raceNo']:
#                                         i['status'] = Racecard.OFFICIAL
#                                         #Go ahead and save to prerace_numbervent any issues with FLASHD coming in next.
#                                         racecard.save()
#                                         break
#                                 if result['status']== 'Chart':
#                                     parse_chart(raceNo, racecard, result['results'], official_results)
#                                 racecard.save()
#                                 last_race_number = 1
#                                 for race in racecard.races:
#                                     if(int(race["race_number"]) > last_race_number):
#                                         last_race_number = int(race["race_number"])
                    
#                                 #Go through the Racecard and determine if every race has official results and 
#                                 #has been completed. If so, kick off the Game Finished task. 
                                
#                                 #EDGE CASE: What if Final Race is Cancelled before results for a previous race come in? The Game
#                                 #won't be cancelled in the Change Import above because the results aren't in for a previous race so 
#                                 #we need to do it here.

#                                 races_completed = True
#                                 for race in racecard.races:
#                                     if race['results_are_in'] == False or race['status'] != Racecard.OFFICIAL:
#                                         if int(race['race_number']) == last_race_number and race['status'] == Racecard.CANCELLED: 
#                                             #last race is cancelled. We can still possibly finish the game.
#                                             continue
#                                         else:
#                                             races_completed = False

#                                 games = Game.objects.filter(racecard_id=racecard.id)

#                                 if races_completed == True:
#                                     for game in games:
#                                         if not game.finished:
#                                             finish_game(game.id)

#                                 for game in games:
#                                     calculate_scores_ranks(game)

#                             except Track.DoesNotExist:
#                                 log.debug("DOES NOT EXIST: Track: %s" % track_code)
#                             except Racecard.DoesNotExist:
#                                 log.debug("DOES NOT EXIST: Racecard: track=%s race_date=%s" % (track_code, race_date))

#                         return Response(response2.data, status=status.HTTP_201_CREATED)
#     else:
#         return None
    


# def parse_chart(race_number, racecard, results, official_results):
#     #Update all of the Runners based on the Chart
    

#     runners = []
#     for result in results:
        
#         runner = parse_start(race_number, racecard, result)
#         if (runner is not None):
#             runners.append(runner)

#     calculate_race_scores(runners)



# def parse_start(race_number, racecard, start):
#     horse_name = start['horseName']
#     if '(' in horse_name:
#         horse_name = horse_name[0:horse_name.index('(') - 1]
#     # registration_number = start.find('Horse/RegistrationNumber').text
#     horse_id = horse_util.get_horse_id(horse_name)
#     try:
#         try:
#             runner = Runner.objects.get(racecard=racecard, race_number=race_number, name=horse_name)
#         except Runner.DoesNotExist:
#             runner = Runner.objects.get(racecard=racecard, race_number=race_number, name='AE - {}'.format(horse_name))
#         runner_finish = start['finishPos']
#         if(runner_finish == 0):
#             runner_finish = 1000
#         runner.finish = int(runner_finish)

#         # for point_of_call in start.findall('PointOfCall'):
#         #     if(point_of_call.find('PointOfCall').text == 'F'):
#         #         runner.lengths_behind = Decimal(point_of_call.find('LengthsBehind').text)
#         #         runner.lengths_ahead = Decimal(point_of_call.find('LengthsAhead').text)
#         #         break

#         # if(start.find('DQIndicator').text == 'Y'):
#         #     runner.disqualified = True

#         runner.save()
#         return runner
#     except Runner.DoesNotExist:
#         log.debug("DOES NOT EXIST: (Results) Runner: %s" % horse_id)



# def calculate_race_scores(runners):
    
#     #Now check to see if any of the runners have been DQ'd and adjust their Lengths Behind accordingly
#     #We can't do it while we're parsing the individual runners because we're not sure about the order
#     #that we're receiving the entries

#     #Yes, we have to go through the list of runners three different occasions if a DQ exists
#     dq = False
#     adjusted_lengths_behind = 0
#     for runner in runners:
#         if(runner.disqualified is not None and runner.disqualified == True):
#             dq = True
#         if(runner.finish is not None and runner.finish == 1):
#             adjusted_lengths_behind = runner.lengths_behind

#     if dq == True:

#         #Adjust every runner's lengths behind based on moving the new #1 
#         for runner in runners:
#             runner.lengths_behind -= adjusted_lengths_behind
            
#             runner.save()

#         #Adjust DQ'd runners lengths behind even further
#         for runner in runners:
#             #If any runner in the group is disqualified, we need to adjust the lengths back for every runner
#             if(runner.disqualified == True):
#                 #Get the finish position ahead of our DQ'd runner and set lengths behind to be the same
#                 finish_position = runner.finish - 1
#                 if(finish_position > 1):
#                     for runner2 in runners:
#                         if(runner2.finish == finish_position):
#                             runner.lengths_behind = runner2.lengths_behind
                            
#                             runner.save()
#                             break


#     #Now we have to go through the runners and account for those that Did Not Finish
#     #Per equibase, this is determined with a LengthsBehind and LengthsAhead of 9999
#     #StableDuel would like them to be 5 lengths behind the last horse that actually finished. 
#     for runner in runners:
#         # print (runner.lengths_behind)
#         # print (runner.lengths_ahead)
#         #If any runner in the group DNF, make the lengths behind equal to the next runner that did finish
#         if(runner.lengths_behind == 9999 or runner.lengths_ahead == 9999):
#             #Get the finish position ahead of our DNF runner
#             finish_position = runner.finish - 1
#             if(finish_position > 1):
#                 for runner2 in runners:
#                     if(runner2.finish == finish_position):
#                         #We add 500 to the lengths behind because that will give an effective
#                         #score subtraction of 5 points (which is desired by SD)
#                         runner.lengths_behind = runner2.lengths_behind + 500
#                         runner.save()
#                         break


#     #Finally, after all of the lengths and dqs have been determined, go ahead and set the score for the runner
#     for runner in runners:
#         if runner.points is None or runner.margin is None:
#             runner.score = 0
#         else:
#             runner.score = max( -30, round(runner.points + runner.margin, 2 ) )

#         #Set the score for the Horse in HorsePoint so that it can be used for the Follows functionality
#         horse_point, _ = HorsePoint.objects.get_or_create(external_id=runner.external_id, defaults={'points':0,'count':0})
#         horse_point.points += Decimal(runner.score)
#         horse_point.count +=1
#         horse_point.save()

#         runner.save()

#     #Finally, finally -- check to see if any of the runners are Coupled.  If so, take the max of the group of Runners
#     #coupled_runners = []
#     coupled_runners = defaultdict(list)

#     for runner in runners:
#         if(runner.coupled == True):
#             coupled_runners[runner.coupled_indicator].append(runner)

#     for coupled_indicator_value in coupled_runners:
#         max_score = -30
#         for coupled_runner in coupled_runners[coupled_indicator_value]:
#             if coupled_runner.scratched == False and coupled_runner.score > max_score:
#                 max_score = coupled_runner.score

#         for coupled_runner in coupled_runners[coupled_indicator_value]:
#             coupled_runner.score = max_score
#             coupled_runner.save()

#     #Reset the cache for Stable Scores
#     calculate_global_leaderboard()