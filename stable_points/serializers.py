from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class GlobalLeaderboardSerializer(serializers.ModelSerializer):
    stable_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'stable_name',
            'score',
            'rank',
        )

    def get_stable_name(self, obj):
        try:
            stable_name = obj.profile.stable_name
        except:
            stable_name = 'Not Set' #should not happen in the real world,
        return  stable_name
