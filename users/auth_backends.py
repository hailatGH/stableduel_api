from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions

User = get_user_model()

class DebugAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.META.get('HTTP_X_SD_DEBUG_TOKEN')
        if not token or token != settings.SD_DEBUG_TOKEN or settings.SD_DEBUG_TOKEN is None:
            return None

        auth = request.META.get('HTTP_X_SD_DEBUG_AUTH')
        if not auth:
            return None
        
        auth = auth.split(',')
        if len(auth) != 2:
            raise exceptions.AuthenticationFailed('Needs key and value separated by "," to get')
        
        if auth[0] not in ['id', 'email', 'auth0_id']:
            raise exceptions.AuthenticationFailed('Key is not one of the required fields')

        try:
            get_user_kwargs = {
                auth[0]: auth[1]
            }

            user = User.objects.get(**get_user_kwargs)
            return (user, None,)

        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

       