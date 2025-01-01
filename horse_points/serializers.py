from datetime import datetime
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import HorsePoint
from collections import defaultdict

class HorsePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorsePoint
        
        fields = (
            'id',
            'external_id',
            'points',
            'count',
            'created_at',
            'updated_at',
        )


