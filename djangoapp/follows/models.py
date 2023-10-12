from django.db import models
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q
from horse_points.models import HorsePoint

User = get_user_model()

class Follows(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    #represents the external_id on the runner
    horse = models.CharField(max_length=10, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True, null=True, blank=True, related_name="user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    horse_point = models.ForeignKey(HorsePoint, null=True, on_delete=models.SET_NULL, db_constraint=False, blank=True)

    HORSE = 'HORSE'
    USER = 'USER'

    class Meta:
        unique_together = ('owner', 'horse', 'user')
