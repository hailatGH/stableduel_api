from rest_framework import serializers
from .models import Track, Racecard
from stables.models import Runner
from games.models import Game
from stables.serializers import RunnerSerializer
from .timezones import get_timezone
from datetime import datetime, timedelta
from time import time

class TrackSerializer(serializers.ModelSerializer):
    timezone = serializers.SerializerMethodField()
    upcoming_games = serializers.SerializerMethodField()
    #upcoming_games = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset=Game.objects.filter(racecard__track=obj.id))

    class Meta:
        model = Track
        fields = (
            'id',
            'code',
            'name',
            'country',
            'created_at',
            'updated_at',
            'timezone',
            'location',
            'opened',
            'nickname',
            'distance',
            'notable_race',
            'triple_crown_winners',
            'upcoming_games'
        )

    def get_timezone(self, obj):
        if (get_timezone(obj.code) is not None):
            return get_timezone(obj.code).utc_offset
        else:
            return "-0500"
     
    def get_upcoming_games(self, obj):
        games = Game.objects.filter(racecard__track=obj, racecard__race_date__gte=datetime.today()).values_list('id',flat=True)
        return games

class RacecardSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    runners = RunnerSerializer(many=True, read_only=True, source='runner_set')

    class Meta:
        model = Racecard
        fields = (
            'id',
            'track',
            'race_date',
            'mode',
            'races',
            'runners',
            'created_at',
            'updated_at',
        )
        