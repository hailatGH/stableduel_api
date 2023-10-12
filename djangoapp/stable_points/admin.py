from django.contrib import admin

from .models import StablePoint

@admin.register(StablePoint)
class StableAdmin(admin.ModelAdmin):
    list_display = ["user__email", "notes", "points"]

    def user__email(self, obj):
        if obj.user:
            return obj.user.email
        return None
