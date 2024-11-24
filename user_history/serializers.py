from rest_framework import serializers
from django.contrib.auth import get_user_model
from games.models import Game
from stables.models import Stable, Runner

User = get_user_model()

class UserHistorySerializer(serializers.ModelSerializer):
    stable_name = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()
    stable_count = serializers.SerializerMethodField()
    finishes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'stable_name',
            'score',
            'rank',
            'average_score',
            'stable_count',
            'finishes',
        )

    def get_stable_name(self, obj):
        try:
            stable_name = obj.profile.stable_name
        except:
            stable_name = 'Not Set' #should not happen in the real world,
        return  stable_name

    def get_average_score(self, obj):
        stable_count = Stable.objects.filter(user=obj, is_valid_at_start=True).exclude(game__game_state=Game.CANCELLED).count()
        return obj.score / stable_count if stable_count > 0 else None

    def get_stable_count(self, obj):
        return Stable.objects.filter(user=obj, is_valid_at_start=True).exclude(game__game_state=Game.CANCELLED).count()

    def get_finishes(self, obj):
        runners = Runner.objects.filter(finish__isnull=False, stable__user=obj).exclude(stable__game__game_state=Game.CANCELLED).distinct()
        finishes = [0] * 100
        total_races = len(runners)
        finishes_total = 0
        points_total = 0
        for runner in runners:
            finishes[runner.finish] += 1
            finishes_total += runner.finish
            points_total += runner.points

        return {
            "win": finishes[1],
            "place": finishes[2],
            "show": finishes[3],
            "fourth": finishes[4],
            "fifth": finishes[5],
            "win_percentage": finishes[1] / total_races if total_races > 0 else None,
            "total_races": total_races,
            "average_finish": round(finishes_total / total_races) if total_races > 0 else None,
            "average_points_per_race": points_total / total_races if total_races > 0 else None,
        }


class PastPerformanceSerializer(serializers.ModelSerializer):
    race_date = serializers.SerializerMethodField()
    game_id = serializers.SerializerMethodField()
    game_name = serializers.SerializerMethodField()
    track_code = serializers.SerializerMethodField()

    class Meta:
        model = Stable
        fields = (
            'id',
            'score',
            'rank',
            'race_date',
            'game_id',
            'game_name',
            'track_code',
        )

        read_only_fields = (
            'id',
            'score',
            'rank',
        )

    def get_race_date(self, obj):
        return obj.game.racecard.race_date

    def get_game_id(self, obj):
        return obj.game.id

    def get_game_name(self, obj):
        return obj.game.name

    def get_track_code(self, obj):
        return obj.game.racecard.track.code
