import os
from django.core.exceptions import ValidationError

def validate_banner_image(value):
    if value is None:
        return
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename; [1] returns .extention
    valid_extensions = ['.jpg', '.png', '.jpeg','.gif'] # list of valid extentions for image
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension for an Ad!')
    if value.size > 4 * 1024 * 1024: # 4 MB
        raise ValidationError('File size must be under 2 MB.')

