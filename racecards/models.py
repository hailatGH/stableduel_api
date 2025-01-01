from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.cache import cache
import pytz

class Track(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=30)
    location = models.CharField(max_length=50,blank=True,null=True)
    opened = models.DateField(null=True)
    nickname = models.CharField(max_length=50,blank=True,null=True)
    distance = models.IntegerField(null=True, blank=True)
    notable_race = models.CharField(max_length=50,null=True,blank=True)
    triple_crown_winners = models.CharField(max_length=200,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        cache_key = "tracks_trackcode_{}".format(self.id)
        track_code = cache.get(cache_key)
        if track_code is None:
            track_code = self.code
            cache.set(cache_key, track_code, 60 * 60 * 24)

        return track_code

class Racecard(models.Model):
    HARNESS ="HARNESS"
    THOROUGHBRED = "THOROUGHBRED"
    PA ="PA"
    RaceModes = (
        [HARNESS, "HARNESS"],
        [PA, "PA"],
        [THOROUGHBRED, "THOROUGHBRED"]
        
    )
    track = models.ForeignKey(Track, on_delete=models.CASCADE, db_index=True)
    races = JSONField(default=[])
    race_date = models.DateField()
    mode = models.CharField(choices=RaceModes, default=THOROUGHBRED, max_length=30)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #Race Statuses
    NOT_STARTED = 'NOT_STARTED'
    RESULTS_PENDING = 'RESULTS_PENDING'
    OFFICIAL = 'OFFICIAL'
    CANCELLED = 'CANCELLED'
    
class TrackVideo(models.Model):
    ROBERTS='ROBERTS'
    STEEPLECHASE="STEEPLECHASE"
    SMS="SMS"

    TrackVideoModes = (
        [ROBERTS, "Roberts"],
        [STEEPLECHASE, 'Steeplechase'],
        [SMS,'SMS']
    )

    quality = models.CharField(choices=[["HD", "HD"], ["SD","SD"]], max_length=25, default='HD')
    mode = models.CharField(choices=TrackVideoModes, default=ROBERTS, max_length=25)
    stream_name = models.CharField(max_length=200, blank=True, null=True)
    link = models.CharField(max_length=200, blank=True, null=True)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, db_index=True)
    usr = models.CharField(max_length=25, default=None, blank=True, null=True)
    speed = models.IntegerField(default=0, blank=True, null=True)
    staticspeed = models.IntegerField(choices=([0, "Adaptive"], [1, 'Single']),default=0, null=True)
    output = JSONField(default=None, blank=True, null=True)
    forceFormat = models.CharField(choices=(['ios', "Ios"], ['rtsp', 'rstp'], ['auto', 'auto']), max_length=25, default='ios', null=True)




class HarnessTracksDetail(models.Model):
    code = models.CharField(max_length=5, unique=True)
    trackmastercode = models.CharField(max_length=10, unique=True)
    equibasecode = models.CharField(max_length=10)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=10)
    state_province = models.CharField(max_length=50,blank=True,null=True)
    timezone = models.CharField(max_length=50,blank=True,null=True)
    timezoneabbrev = models.CharField(max_length=50,blank=True,null=True)
    city = models.CharField(max_length=50,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.timezone:
            tz = pytz.timezone(self.timezone)
            tzabbrev = tz.localize(
            pytz.datetime.datetime.now(), is_dst=None).strftime('%Z')
            self.timezoneabbrev = tzabbrev[0]
        super().save(*args, **kwargs)
        
        
class PATracksDetail(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
