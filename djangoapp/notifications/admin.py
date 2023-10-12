from django.http import HttpResponse
from django.contrib import admin
from django.contrib.admin import widgets
from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from django.db import models

from users.models import User
from games.models import Game
from stables.models import Stable

from .push_notifications import PushToUsersNotification, PushToInterestsNotification
from notifications.constants import Type, Action, Lifespan

from .models import Notification

class CreateNotificationForm(forms.Form):
    game = forms.ModelChoiceField(queryset=Game.objects.filter(),
            label="Game", required=False)
    title = forms.CharField(max_length=140)
    
    message = forms.CharField(max_length=280, widget=forms.TextInput(attrs={'size':80}))

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    change_list_template = "notifications/admin/notification_changelist.html"
    list_display = ["user__email", "notif_type", "action", "created_at"]
    search_fields = ["user__email", "notif_type", "action"]

    def user__email(self, obj):
        if obj.user:
            return obj.user.email
        return None

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('create-notification/', self.create_notification),
        ]
        return my_urls + urls

    def create_notification(self, request):
        if request.method == "POST":
            game_id = 0
            message = str(request.POST['message'])
            title = str(request.POST['title'])
            # Send to all users in the Game 
            if request.POST['game'] != '':
                game_id = int(request.POST['game'])
                # Seems like it would make sense to PushToInterests here. The only
                # problem is that game_ids on DEV may match game_ids on PROD. Pusher 
                # only knows that you're sending an ID and will send to both PROD and DEV
                game = Game.objects.get(id=game_id)
                auth0_ids = list(Stable.objects.filter(game=game).select_related('user').distinct('user').values_list('user__auth0_id',flat=True))
                
                if (len(auth0_ids)):
                    pn = PushToUsersNotification(Type.GENERAL, Action.NONE, Lifespan.PERSISTENT_CONDITIONAL, auth0_ids, None)
                    pn.title = title
                    pn.message = message
                    pn.send()
            else:
                # Get all of the user_ids in the system
                auth0_ids = list(User.objects.all().values_list('auth0_id', flat=True))

                if (len(auth0_ids)):
                    pn = PushToUsersNotification(Type.GENERAL, Action.NONE, Lifespan.PERSISTENT_CONDITIONAL, auth0_ids, None)
                    pn.title = title
                    pn.message = message
                    pn.send()

            return redirect("..")
        form = CreateNotificationForm()
        payload = {
            "form": form,
            "submit_label": 'Create Notification',
        }
        return render(
            request, "notifications/admin/create_notification_form.html", payload
        )