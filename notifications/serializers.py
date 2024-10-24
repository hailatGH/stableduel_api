from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id',
            'user',
            'title',
            'message',
            'action',
            'stable_id',
            'runner_id',
            'notif_type',
            'is_dismissible',
            'expired',
            'created_at'
        )