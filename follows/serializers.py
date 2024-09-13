from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Follows
from django.db.models import Sum
from stable_points.models import StablePoint
from stables.models import Stable, Runner
from stables.serializers import StableSerializer


class FollowsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follows
        fields = (
            'id',
            'owner',
            'horse',
            'user',
        )



class FollowsUsersSerializer(serializers.ModelSerializer):
        follow_id = serializers.SerializerMethodField()
        stable_name = serializers.SerializerMethodField()
        stable_points = serializers.IntegerField()
        num_entries = serializers.SerializerMethodField()
        
        class Meta:
                model = Follows
                fields = (
                    'user',
                    'owner',
                    'follow_id',
                    'stable_name',
                    'stable_points',
                    'num_entries',
                )

        def get_follow_id(self, obj):
            return obj.id

        def get_stable_name(self, obj):
            #obj should be a follows 
            if(obj.user is not None):
                return obj.user.profile.stable_name

        def get_num_entries(self, obj):
            #obj should be a follows 
            if(obj.user is not None):
                stables = Stable.objects.filter(user=obj.user)
                valid_count = 0
                for stable in stables:
                    if(StableSerializer(stable).isValid == True):
                    #This caused a dramatic increase in response time.  Investigate further.
                    #if(StableSerializer(stable).data['state'] == Stable.FINISHED):
                        valid_count = valid_count + 1
 
                return valid_count



class UsersFollowersSerializer(serializers.ModelSerializer):
        follow_id = serializers.SerializerMethodField()
        stable_name = serializers.SerializerMethodField()
        stable_points = serializers.IntegerField()
        num_entries = serializers.SerializerMethodField()
        am_i_following = serializers.SerializerMethodField()
        user = serializers.SerializerMethodField()
        owner = serializers.SerializerMethodField()
        
        class Meta:
                model = Follows
                fields = (
                    'follow_id',
                    'user',
                    'owner',
                    'stable_name',
                    'stable_points',
                    'num_entries',
                    'am_i_following',
                )
                order_by = ['-stable_points']

        def get_follow_id(self, obj):
            return obj.id

        def get_stable_name(self, obj):
            return obj.owner.profile.stable_name

        def get_user(self, obj):
            return obj.user.id

        def get_owner(self,obj):
            return obj.owner.id

        def get_num_entries(self, obj):
            stables = Stable.objects.filter(user=obj.owner)
            valid_count = 0
            for stable in stables:
                if(StableSerializer(stable).isValid == True):
                        valid_count = valid_count + 1

            return valid_count

        def get_am_i_following(self, obj):
            return (Follows.objects.filter(user=obj.owner, owner=obj.user).count()) > 0



class FollowsHorsesSerializer(serializers.ModelSerializer):
        follow_id = serializers.SerializerMethodField()
        external_id = serializers.SerializerMethodField()
        name = serializers.SerializerMethodField()
        total_points = serializers.SerializerMethodField()
        number_runners = serializers.SerializerMethodField()

        class Meta:
                model = Follows
                fields = (
                    'follow_id',
                    'external_id',
                    'name',
                    'total_points',
                    'number_runners',
                )
                order_by = ['-stable_points']

        def get_follow_id(self, obj):
            return obj.id

        def get_external_id(self, obj):
            if(obj.horse is not None):
                return obj.horse

        def get_name(self, obj):
            if(obj.horse is not None):
                try:
                    horse = Runner.objects.filter(external_id=obj.horse).order_by('-created_at')[:1].get()
                    return horse.name
                except Runner.DoesNotExist:
                    return 

        def get_total_points(self,obj):
            if obj.horse_point is not None:
                return obj.horse_point.points
            else:
                return 0

        def get_number_runners(self, obj):
            if obj.horse_point is not None:
                return obj.horse_point.count
            else:
                return 0
        
                        
