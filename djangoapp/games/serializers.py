import hashlib
import time
import requests
from datetime import datetime, timezone, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from racecards.models import Racecard, TrackVideo
from racecards.serializers import RacecardSerializer, TrackSerializer
from rest_framework import serializers
from stables.models import Stable
from wagering.models import Contest
from django.core.cache import cache
from stables.utils import count_stables_with_score
from .models import Banner, Game

from racecards.utils import get_full_race_time


class GameSerializer(serializers.ModelSerializer):
    racecard = serializers.PrimaryKeyRelatedField(many=False, read_only=False, queryset=Racecard.objects.all())
    stable_count = serializers.SerializerMethodField()
    track = serializers.SerializerMethodField()
    race_date = serializers.SerializerMethodField()
    contest_guid = serializers.SerializerMethodField()
    pool = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()
    mode = serializers.SerializerMethodField()
    class Meta:
        model = Game
        fields = (
            'id',
            'racecard',
            'name',
            'started',
            'finished',
            'created_at',
            'updated_at',
            'stable_count',
            'runner_limit',
            'salary_cap',
            'entry_fee',
            'winner_limit',
            'stable_limit',
            'game_state',
            'pool',
            'track',
            'race_date',
            'contest_guid',
            'video',
            'banner',
            'mode',
            'payout_projections'
        )
        ordering = ['race_date', 'created_at']

    def get_stable_count(self, obj):
        return obj.stable_set.filter(~Q(is_valid_at_start=False)).count()
    
    def get_race_date(self, obj):
        return obj.racecard.race_date   
    
    def get_mode(self, obj):
        return obj.racecard.mode

    def get_pool(self, obj):
        return obj.get_pool()

    def get_track(self, obj):
        return TrackSerializer(obj.racecard.track).data

    def get_contest_guid(self, obj):
        try:
            return obj.contest.id
        except Contest.DoesNotExist:
            return None
        
    # Ezras' work
    # def get_video(self, obj):
    #     racecard = obj.racecard
    #     video = None
    #     try:
    #         video =  TrackVideo.objects.get(track=obj.racecard.track)
    #     except:
    #         pass
    #     if video != None:
    #         sortedRaces = sorted(racecard.races, key=lambda race : int(race['race_number']))
    #         currentTime = time.time()
    #         utc_now = datetime.utcnow()
    #         t = str(int(utc_now.timestamp()))    

    #         # If current time is not at least 30 minutes before first race start return None
    #         firstRace = sortedRaces[0]
    #         raceDate = racecard.race_date.strftime("%Y-%m-%d")
    #         firstRaceStart = datetime.strptime(raceDate+"_"+firstRace['post_time'], "%Y-%m-%d_%I:%M%p")

    #         # if datetime.fromtimestamp(currentTime) < (firstRaceStart - timedelta(minutes=30)) :  
    #         #     return None
    #         # If last race is completed, return None
    #         # lastRace = sortedRaces[-1]
    #         # if lastRace['results_are_in'] == True or lastRace['status'] == Racecard.OFFICIAL:
    #         #     return None
    #         if video.mode == TrackVideo.STEEPLECHASE:
    #             return video.link
    #         elif video.mode == TrackVideo.ROBERTS:
    #             private_key = settings.ROBERTS_KEY
    #             stream_name = video.stream_name
    #             message = t + private_key + stream_name
    #             hash_object = hashlib.md5(message.encode())
    #             md5_hash = hash_object.hexdigest()
    #             hd = 1 if video.quality == 'HD' else 0
    #             return f'https://stream.robertsstream.com/streamlive.php?stream={video.stream_name}&referer=StableDuel&t={t}&h={md5_hash}&hd={hd}'
    #     return None
    
    # Updated
    def get_video(self, obj):
        # Video
        video = None
        # get the sorted list of races
        sortedRaces = sorted(obj.racecard.races, key=lambda race: int(race['race_number']))
        
        # get the first race start time
        first_race_date_time =  get_full_race_time(sortedRaces[0])
        last_race_date_time =  get_full_race_time(sortedRaces[-1])
        current_date_time = datetime.now()
        try:
            video =  TrackVideo.objects.get(track=obj.racecard.track)
            if video != None:
                # if current_date_time < (first_race_date_time - timedelta(minutes=30)):
                #     return None
                
                # if current_date_time > (last_race_date_time + timedelta(minutes=10)):
                #     return None
                
                if video.mode == TrackVideo.STEEPLECHASE:
                    return video.link
                
                if video.mode == TrackVideo.ROBERTS:
                    utc_now = datetime.utcnow()
                    timestamp = str(int(utc_now.timestamp()))    
                    private_key = settings.ROBERTS_KEY
                    stream_name = video.stream_name
                    message = timestamp + private_key + stream_name
                    hash_object = hashlib.md5(message.encode())
                    md5_hash = hash_object.hexdigest()
                    hd = 1 if video.quality == 'HD' else 0
                    return f'https://stream.robertsstream.com/streamlive.php?stream={video.stream_name}&referer=StableDuel&t={timestamp}&h={md5_hash}&hd={hd}'
                
                if video.mode == TrackVideo.SMS:  
                    # print ("#############################")
                    # print ("video mode is sms")
                    private_key = settings.SMS_SEED_KEY
                    PartnerCode = settings.SMS_PARTNER_CODE
                    PasswordSMS = settings.SMS_PSSWORD
                    meeting_id = int(sortedRaces[0]['meeting_id'])
                    UserID = self.context['request'].user.id
                    session = requests.Session()
                    # event_api_url = f"https://bwt1.attheraces.com/ps/api/FindEvents?PartnerCode={PartnerCode}&Password={PasswordSMS}&format=json" 
                    event_api_url = f"https://bw230.attheraces.com/ps/api/FindEvents?PartnerCode={PartnerCode}&Password={PasswordSMS}&format=json"  

                    headers = {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "*/*",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                    }
                    event_response = session.get(event_api_url, headers=headers)
                    json_event_response =event_response.json()
                    # print ("**************************")
                    # print (json_event_response)
                    video_urls = []
                    for race in sortedRaces:
                        race_date = race['adjusted_date']
                        race_date = datetime.strptime(race_date, '%Y-%m-%d')
                        start_time = datetime.strptime(race['post_time'], '%I:%M%p')
                        current_race_date_time = datetime.combine(race_date, start_time.time())
                        last_race = sortedRaces[-1]
                        # current_race_date_time= get_full_race_time(race)
                        if race is not last_race:
                            next_race_index = int(race['race_number'])
                            next_race_date_time= get_full_race_time(sortedRaces[next_race_index]) 
                        else:
                            next_race_date_time = get_full_race_time(sortedRaces[-1])+ timedelta(minutes=30)
                        race_name = race['race_name']
                        for event in json_event_response["Events"]:
                            if event['Description']== race_name:
                                  EventID = event["ID"]
                                  break
                            else:
                                EventID = None
                        input = f"{PartnerCode}:{EventID}:L:{UserID}:{private_key}"
                        # print("********************")
                        # print (input)
                        hash_object = hashlib.md5(input.encode())
                        md5_hash = hash_object.hexdigest()
                        key = md5_hash
                        # print("################")
                        # print (key)
                        # if current_date_time < (current_race_date_time):
                        #      video_urls.append("Event not found")
                        
                        # if current_date_time > (next_race_date_time ):
                        #     video_urls.append("Event not found")

                        if EventID:
                            # streaming_api_url= f"http://bwt1.attheraces.com/ps/api/GetStreamingURLs?EventId={EventID}&UserID={UserID}&PartnerCode={PartnerCode}&Key={key}&format=json"
                            # streaming_api_url= f"http://bw230.attheraces.com/ps/api/GetStreamingURLs?EventId={EventID}&UserID={UserID}&PartnerCode={PartnerCode}&Key={key}&format=json"
                            # streaming_response = session.get(streaming_api_url, headers=headers)
                            
                            # if streaming_response.json()['IsOK'] and current_date_time >= (current_race_date_time) and current_date_time < (next_race_date_time ):
                            #     print (streaming_response.json())
                            #     urls = streaming_response.json()["EventInfo"]["Streams"]
                            #     # print (urls)
                            #     for url in urls:
                            #         if url["BitrateLevel"] == "Adaptive":
                            #             Url = url["Url"]
                            #             break
                            #     video_urls.append(Url)
                            # else:
                            #     video_urls.append(streaming_response.json()["Error"]["ErrorMessage"])
                             video_urls.append("Event is available")
                        else:
                            video_urls.append("Event not found")
                    
                    return video_urls
                    # for event in json_event_response["Events"]:
                    #     if event["ID"] == meeting_id:
                    #         EventID = event["ID"]
                    #         break 
                    # input = f"{PartnerCode}:{EventID}:L:{UserID}:{private_key}"

                    # hash_object = hashlib.md5(input.encode())
                    # md5_hash = hash_object.hexdigest()
                    # key = md5_hash
                    # if EventID:
                    #     streaming_api_url= f"http://bwt1.attheraces.com/ps/api/GetStreamingURLs?EventId={EventID}&UserID={UserID}&PartnerCode={PartnerCode}&Key={key}&format=json"
                    #     streaming_response = session.get(streaming_api_url, headers=headers)
                    #     return streaming_response.json()
                    # else:
                    #     print ("herreee")
                    #     return ("None")
                    
                # print ("empty")
                # return None
            
        except BaseException as e:
            print(f"Something Happend: {e}")
            return None
        
    def get_banner(self, obj):
        banner = None
        try:
            banner =  Banner.objects.filter(game=obj.id).first()
        except Banner.DoesNotExist:
            pass
        if banner and banner.visibility == Banner.VISIBLE:
            return BannerSerializer(banner).data
        return None
    
    
class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = (
            '__all__'
        )
class LobbySerializer(serializers.ModelSerializer):
    stable = serializers.SerializerMethodField()
    stable_name = serializers.SerializerMethodField()
    runners_count = serializers.SerializerMethodField()
    projected_payout = serializers.SerializerMethodField()
    class Meta:
        model = Stable
        fields = (
            'stable_name',
            'stable',
            'user',
            'game',
            'score',
            'rank',
            'is_valid_at_start',
            'scratch_limit_reached',
            'scratches_at_finish',
            'stable_count_at_finish',
            'entry_number',
            'runners_count',
            "projected_payout"
    )
    
    def get_stable(self, obj):
        return obj.id
    
    def get_stable_name(self, obj):
        return obj.user.profile.stable_name

    def get_runners_count(self, obj):
        count = 0
        for runner in obj.runners.through.objects.filter(stable_id=obj):
            race_number = int (runner.runner.race_number)
            scratched = runner.runner.scratched  
            racecard = runner.runner.racecard  
            races = racecard.races
            for race in races:
                race_date = datetime.strptime(race["adjusted_date"], "%Y-%m-%d")
                post_time = datetime.strptime(race["post_time"], '%I:%M%p')
                race_date_time = datetime.combine(race_date, post_time.time())
                # if int(race['race_number'])==race_number and race['status']=='NOT_STARTED' and race_date_time > datetime.utcnow() and scratched==False:
                if int(race['race_number'])==race_number and race['results_are_in'] == False and runner.runner.scratched==False:
                    count += 1    
        return count 
    
    def get_projected_payout(self, obj):
        if obj.game.started == False or obj.rank == None:
            return None
        # Count of stables with current score ( greater than 1 for ties)
        stables_count = count_stables_with_score(float(obj.score), obj.game.pk)
        # If s
        if stables_count == 0:
            return None
        """
        Get all keys payouts on ranks from stable rank upto stable rank + number_of_ties
        eg. for rank 1 and no ties, fetch payout for rank 1
            for rank 1 and 2 tied stabled, fetch payout for rank 1 and 2
        """
        payouts_dict= cache.get_many([f"game_payout_{obj.game.pk}_rank_{rank}" for rank in range(obj.rank , obj.rank + stables_count )])
        """Filter out empty payout values (i.e. None values) """
        filtered_payouts= filter(lambda p : p != None, payouts_dict.values())
        """
        Calculate payout by averaging payouts with the number of ties
        eg. with payouts 1: 5000, 2: 2500, 3: 1000
            for rank 1 and no ties, payout = 5000 / 1
            for rank 2 and a tie, payout = 2500 + 1000 / 2
        """
        return sum(filtered_payouts) / stables_count
