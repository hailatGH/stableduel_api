from rest_framework import serializers
from .models import VersionRequirement


class VersionRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionRequirement
        fields = (
            "ios_latest_version",
            "ios_required_version",
            "android_latest_version",
            "android_required_version"
        )

        read_only_fields = (
            "ios_latest_version",
            "ios_required_version",
            "android_latest_version",
            "android_required_version"
        )