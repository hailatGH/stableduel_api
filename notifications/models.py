from django.db import models
from users.models import User
from .constants import Type, Action

class Notification(models.Model):
    user           = models.ForeignKey(User, on_delete=models.CASCADE)
    title          = models.CharField(max_length=140)
    message        = models.CharField(max_length=280)
    notif_type     = models.CharField(max_length=25, choices=Type.VALUES, null=True, blank=True, default=None)
    action         = models.CharField(max_length=25, choices=Action.VALUES, null=True, blank=True, default=None)
    stable_id      = models.IntegerField(null=True, blank=True, default=None)
    runner_id      = models.IntegerField(null=True, blank=True, default=None)
    is_dismissible = models.BooleanField(default=True)
    expired        = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)