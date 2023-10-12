from django import forms
from racecards.models import TrackVideo
from django.core.exceptions import ValidationError

class TrackVideoForm(forms.ModelForm):
    class Meta:
        model= TrackVideo
        exclude= []
    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('mode')
        stream_name = cleaned_data.get('stream_name')
        link = cleaned_data.get('link')
        if mode == TrackVideo.ROBERTS and stream_name == None:
            raise ValidationError({'stream_name': 'Stream name is required for videos in Roberts mode'})
        elif mode == TrackVideo.STEEPLECHASE and link == None:
            raise ValidationError({'link': 'Link is required for videos in Steeplechase mode'})
        elif mode == TrackVideo.SMS and link == None:
            raise ValidationError({'link': 'Link is required for videos in Steeplechase mode'})