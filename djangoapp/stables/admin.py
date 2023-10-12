from django.contrib import admin
from reversion.admin import VersionAdmin

from stables.models import Stable, Runner

@admin.register(Stable)
class StableAdmin(VersionAdmin):
    list_display = ["user__email", "game__name"]
    search_fields = ["user__email", "game__name"]
    raw_id_fields = ["runners"]
    readonly_fields = ["entry_number",]

    def user__email(self, obj):
        if obj.user:
            return obj.user.email
        return None

    def game__name(self, obj):
        if obj.game:
            return obj.game.name
        
        return None

@admin.register(Runner)
class RunnerAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "owner", "jockey", "trainer", "external_id"]
    list_filter = ["racecard__mode"]
    search_fields = ["name", "id", "external_id", "racecard__track__code","racecard__track__name"]
    readonly_fields = ["lengths_behind","lengths_ahead"]
    ordering = ("id",)