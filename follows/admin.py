from django.contrib import admin

from .models import Follows

@admin.register(Follows)
class FollowsAdmin(admin.ModelAdmin):
    list_display = ["owner__email", "horse", "user"]

    def owner__email(self, obj):
        if obj.owner:
            return obj.owner.email
        return None
