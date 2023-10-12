from django.contrib.auth import get_user_model
from rest_framework import exceptions

User = get_user_model()

def jwt_get_username_from_payload_handler(payload):
    try:
        return User.objects.get(auth0_id=payload['sub'])
    except User.DoesNotExist:
        raise exceptions.AuthenticationFailed("Invalid credentials")

