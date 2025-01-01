from django.contrib.auth.models import User
from rest_framework.generics import RetrieveAPIView, CreateAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ParseError, NotFound, AuthenticationFailed
from pusher_push_notifications import PushNotifications
from uszipcode import SearchEngine
import requests
import base64
import logging
import datetime
import re
from api.models import VersionRequirement

from .serializers import CurrentUserSerializer, SignupSerializer, ProfileSerializer
from .permissions import IsCurrentUser
from .models import User as CustomUser
# GAMSTOP INTEGRATION VIEWSET 
class GamstopExcludeUsersCheck(APIView):
    def post(self, request):
        try:
            api_key = settings.GAMSTOP_APIKEY
            url = settings.GAMSTOP_URL
            
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': api_key
            }
            data = {
                "firstName": request.data['firstName'],
                "lastName": request.data['lastName'],
                "dateOfBirth": request.data['dateOfBirth'],
                "email": request.data['email'],
                "postcode": request.data['postcode'],
                "mobile": request.data['mobile'],
            }
            response = requests.post(url, data=data, headers=headers)

            if response.status_code == 200:
                print(response.headers)
                if response.headers['x-exclusion'] == "Y":
                    
                    # user = CustomUser.objects.get(email=data['email'])
                    # user.gamstop_exclude = True
                    # user.save()
                    
                    return Response({"message": "You are registered with the GAMSTOP service with a valid current self-exclusion."}, status=403)
            
                if (response.headers['x-exclusion'] == "P") or (response.headers['x-exclusion'] == "N"):
                    
                    # user = CustomUser.objects.get(email=data['email'])
                    # user.gamstop_exclude = False
                    # user.save()
                    
                    return Response({"message": "You are either not registered with the GAMSTOP service or you do not have a valid current self-exclusion."}, status=200)
            
            return Response(f'Request failed with status code {response.status_code}')
            
        
        except Exception as e:
            return Response({"message": f"Failed due to -> {e}"})
        
       

class CurrentUserDetails(RetrieveUpdateAPIView):
    model = User
    serializer_class = CurrentUserSerializer
    permission_classes = (IsCurrentUser, )

    def get_object(self):
        meta = self.request.META
        
        platform = meta.get("HTTP_X_APPLICATION_PLATFORM")
        version = meta.get("HTTP_X_APPLICATION_VERSION")
        # print("Platform: {}, Version: {}".format(platform, version))
        
        if platform == None or version == None:
            raise AuthenticationFailed("Application version outdated, please update to continue!")
        
        if platform.lower() != "android" and platform.lower() != "ios":
            raise AuthenticationFailed("Application platform not supported!")
        
        version_obj = VersionRequirement.objects.last()        
        required_version = version_obj.android_required_version if platform.lower() == "android" else version_obj.ios_required_version
        try:
            if float(required_version) > float(version):
                raise AuthenticationFailed("Application version outdated, please update to continue!")
        except ValueError:
                raise AuthenticationFailed("Invalid version format. Please provide a valid version number.")
        # if int(required_version) > int(version):
        #     raise AuthenticationFailed("Application version outdated, please update to continue!")
         
        return self.request.user
    

class CurrentProfileUpdate(RetrieveUpdateAPIView):
    model = User
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user.profile

class SignupUserView(CreateAPIView):
    serializer_class = SignupSerializer

class BeamsAuthView(APIView):
    
    permission_classes = (IsCurrentUser, )
    '''
       Generate a new beams auth token for the requesting user.

       These tokens are used for sending push notifications to a specific list of users
    '''
    def get(self, request, format=None):

        if len(settings.PUSHERBEAMS_INSTANCE_ID) > 0 and len(settings.PUSHERBEAMS_SECRET_KEY) > 0:
            beams_client = PushNotifications(
                instance_id=settings.PUSHERBEAMS_INSTANCE_ID,
                secret_key=settings.PUSHERBEAMS_SECRET_KEY
            )

            beams_token = beams_client.generate_token(request.user.auth0_id)

            return Response(beams_token, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_200_OK)

class ValidateBirthdayView(APIView):

    '''
        Validate users birthday against their location

        Generally states require a user to be 18 years of age
        to use the StableDuel application, however some states
        require that the user be 19 or 21 years of age and so this
        endpoint was created to validate a users age against their location.

        Params:
            zip - required
                  A 5-digit US zip code

            birthday - required
                  The users birthday formatted as 'YYYY-MM-DD'  
    '''
    def get(self, request, format=None):

        zip_code = request.query_params.get("zip", None)
        birthday = request.query_params.get("birthday", None)

        if zip_code is None:
            raise ParseError('Zip is required')
        elif re.search('^\d{5}$', zip_code) is None:
            raise ParseError('Valid 5 digit US zip code is required')

        if birthday is None:
            raise ParseError('Birthday is required')
        else:
            try:
                birth_date = datetime.datetime.strptime(birthday, "%Y-%m-%d")
            except ValueError:
                raise ParseError('Birthday must be formatted as YYYY-MM-DD')

        search = SearchEngine(simple_zipcode=True)
        zipcode = search.by_zipcode(zip_code)
        if zipcode:
            state = zipcode.state
        else:
            raise NotFound('Unable to find zip code')

        now = datetime.datetime.now()

        age = (now - birth_date).days / 365.25

        unique_states = {
            "AL": 19,
            "NE": 19,
            "DE": 19,
            "MA": 21,
            "MN": 21
        }

        required_age = unique_states.get(state, 18)

        if age < required_age:
            raise ParseError("Must be {} years of age (or older) to signup".format(required_age))
                
        return Response("OK", status=status.HTTP_200_OK)

            
