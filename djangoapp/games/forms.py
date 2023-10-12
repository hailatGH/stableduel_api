from django import forms
from django.core.files.images import get_image_dimensions
from games.models import Banner
from django.core.exceptions import ValidationError


class GameUserFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        for form in self.forms:
            cleaned_data = form.cleaned_data
            game = cleaned_data.get('game')
            if game != None and not game.is_private  :
                raise ValidationError('Game users are only allowed on private games')

class GamePayoutFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        payouts_positions = set([])
        for form in self.forms:
            cleaned_data = form.cleaned_data
            position = cleaned_data.get("position")
            if position in payouts_positions:
                raise ValidationError(f'Duplicate payout projection for position {position}')
            else:
                payouts_positions.add(position)

class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        exclude = []

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if image != None:
            _, h = get_image_dimensions(image)
            if h > 85:
                raise forms.ValidationError( 'Image height exceeds the allowed maximum (85 pixels) ')
        return image