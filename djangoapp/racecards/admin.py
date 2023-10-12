from django.contrib import admin
from racecards.models import Track
from racecards.models import Racecard
from racecards.models import TrackVideo
from racecards.models import HarnessTracksDetail,PATracksDetail
from racecards.forms import TrackVideoForm
from datetime import datetime, timedelta


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]
    search_fields = ["name", "code"]


@admin.register(Racecard)
class RacecardAdmin(admin.ModelAdmin):
    ordering = ["-race_date"]
    list_display = ["track", "race_date"]
    list_filter = ["mode","race_date"]
    search_fields = ["track__name","track__code","race_date"]

    def get_search_results(self, request, queryset, search_term):
        try:
            search_date = datetime.strptime(search_term, '%Y-%m-%d').date()
            queryset = queryset.filter(race_date__icontains=search_date)
        except ValueError:
            pass
        return super().get_search_results(request, queryset, search_term)


@admin.register(TrackVideo)
class TrackVideoAdmin(admin.ModelAdmin):
    form = TrackVideoForm
    list_display = ["track", "mode", "link", "quality", "stream_name", "usr", "speed", "staticspeed", "output", "forceFormat"]
    list_filter = ["mode"]

@admin.register(HarnessTracksDetail)
class HarnessTracksDetailAdmin(admin.ModelAdmin):
    list_display = ["code", "trackmastercode", "name", "country", "state_province", "timezoneabbrev", "timezone", "city", "equibasecode"]
    list_filter = ["country"]
    search_fields = ["trackmastercode"]

@admin.register(PATracksDetail)
class PATracksDetailAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    list_filter = ["country"]
    search_fields = ["code"]