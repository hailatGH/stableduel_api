from datetime import datetime
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import State
from datetime import datetime, timedelta
from collections import defaultdict

User = get_user_model()


class WageringStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = (
            'id',
            'name',
            'abbreviation',
        )



    