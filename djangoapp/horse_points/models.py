from django.db import models
from django.contrib.auth import get_user_model


class HorsePoint(models.Model):
    external_id = models.CharField(max_length=10)
    points = models.DecimalField(null=True, blank=True, max_digits=9,decimal_places=2)
    count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)