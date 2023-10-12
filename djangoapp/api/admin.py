from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.http import HttpResponseForbidden
from .models import VersionRequirement

from .models import VersionRequirement

# Changing the name of the admin panel
admin.site.site_header = "StableDuel Game Manager"

@admin.register(VersionRequirement)
class VersionRequirementAdmin(admin.ModelAdmin):
    list_display = ["ios_latest_version", "ios_required_version", "android_latest_version", "android_required_version"]
    
    # Only allow one record to exist
    def has_add_permission(self, request):
        return VersionRequirement.objects.count() < 1