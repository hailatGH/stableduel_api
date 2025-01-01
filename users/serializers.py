from datetime import date
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework import serializers

from .models import Profile
from stable_points.models import StablePoint
from stable_points.utils import  tier_list, get_tier, get_tier_by_name, get_next_tier

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    def validate_stable_name(self, value):
        if Profile.objects.filter(unique_stable_name=value.lower()).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("profile with this stable name already exists.")
        else:
            return value
    class Meta:
        model = Profile
        fields = (
            'id',
            'birthdate',
            'zip_code',
            'stable_name',
            'country',
            'is_admin',
            'deposit_limit'
        )
        read_only_fields = ('is_admin',)
        

class CurrentUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    stable_points = serializers.SerializerMethodField()
    total_stable_points = serializers.SerializerMethodField()
    next_tier_progress = serializers.SerializerMethodField()
    current_tier = serializers.SerializerMethodField()
    tiers = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'auth0_id',
            'email',
            'first_name',
            'last_name',
            'is_superuser',
            'profile',
            'stable_points',
            'total_stable_points',
            'next_tier_progress',
            'current_tier',
            'tiers',
            'rank',
            'gamstop_exclude',
        )
        read_only_fields = (
            'profile',
            'tiers'
        )
    
    # stable points for current year. displayed to user
    def get_stable_points(self, obj):
        curr_year = date.today().year
        points =  StablePoint.objects.filter(user=obj).filter(created_at__year=curr_year).aggregate(Sum('points'))['points__sum']
        return points if points is not None and points > 0 else 0

    # total stable points. apps use this to set tier. hidden value never seen
    def get_total_stable_points(self, obj):
        points =  StablePoint.objects.filter(user=obj).aggregate(Sum('points'))['points__sum']
        return points if points is not None and points > 0 else 0

    def get_current_tier(self, obj):
       """Get tier earned over lifetime
       """
       current_tier = get_tier(self.get_total_stable_points(obj))
       return current_tier["tier"]

    def map_tier(self, tier, current_tier_min):
        tier = tier.copy()
        # mark tier as achieved if minimum of current tier is greater than the tier's min
        tier['achieved_level'] = current_tier_min >= tier['min']
        return tier
    
    def get_tiers(self, obj):
        """Return tiers achieved over current year"""
        current_year_tier = get_tier(self.get_stable_points(obj))
        current_year_min = current_year_tier["min"]
        return map(lambda tier: self.map_tier(tier, current_year_min), tier_list)

    def get_next_tier_progress(self, obj):   
        """Return progress to next tier for current year"""
        current_year_tier = get_tier(self.get_stable_points(obj))
        next_tier = get_next_tier(current_year_tier)
        if next_tier:
            progress = self.get_stable_points(obj) - current_year_tier["min"]
            total_required_progress = next_tier["min"] - current_year_tier["min"]
            return progress / total_required_progress
        return None


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'auth0_id',
        )
class ProfileSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            'id',
            'birthdate',
            'zip_code',
            'stable_name',
            'country',
            'deposit_limit'
        )

        read_only_fields = (
            'stable_name',
        )

class SignupSerializer(serializers.Serializer):
    user = UserSignupSerializer()
    profile = ProfileSignupSerializer()

    def create(self, validated_data):
        user_data = validated_data.get('user')
        
        user = User.objects.create(username=user_data['email'], **user_data)
        user.set_unusable_password()
        user.save()

        # drip_integration_task.delay(user.id)

        profile_data = validated_data.get('profile')
        profile = None
        index = 0
        while profile == None:
            suffix = "" if index == 0 else str(index)
            profile_data['stable_name'] = "{}{}".format(user_data['email'].split('@')[0], suffix)
            index += 1

            try:
                with transaction.atomic():
                    profile = Profile.objects.create(user=user, **profile_data)
            except IntegrityError:
                pass
    
        return {'user': user, 'profile': profile}
