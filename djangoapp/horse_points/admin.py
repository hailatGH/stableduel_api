from django.contrib import admin

from .models import HorsePoint

@admin.register(HorsePoint)
class HorsePointAdmin(admin.ModelAdmin):
    list_display = ["external_id", "points", "count"]
    