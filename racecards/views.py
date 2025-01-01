from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from rest_framework.generics import  CreateAPIView
from .serializers import RacecardSerializer, TrackSerializer, RunnerSerializer
from .models import Racecard, Track, HarnessTracksDetail
from stables.models import Runner
from rest_framework.response import Response
from rest_framework import status
from equibaseimport.racecard_parser import RacecardParser
from lxml import etree as ET


import logging
log = logging.getLogger()

class RacecardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for data to be viewed or edited.
    """
    queryset = Racecard.objects.all().prefetch_related('runner_set').select_related('track')
    serializer_class = RacecardSerializer

    @method_decorator(cache_page(30))
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)

    @method_decorator(cache_page(30))
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

class TrackViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for data to be viewed or edited.
    """
    queryset = Track.objects.all()
    serializer_class = TrackSerializer

    @method_decorator(cache_page(60))
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)







class HarnessTracksDetailImportView(CreateAPIView):
    parser_classes = (RacecardParser,)

    def post(self, request, format=None):
        log.debug('START Harness IMPORT')
        root = ET.fromstring(request.data)
        
        

        try:
            for trackEL in root.findall('track'):
                code = trackEL.attrib['code']
                name = trackEL.text
                trackmastercode = trackEL.find('trackmasterCode').text
                equibasecode = trackEL.find('equibaseCode').text
                state_province = trackEL.find('state-province').text
                country = trackEL.find('country').text
                timezone = trackEL.find('timeZone').text

                code = code.strip()
                trackmastercode = trackmastercode.strip()
                name = name.strip()

                track, _ = HarnessTracksDetail.objects.get_or_create(code=code, trackmastercode=trackmastercode, name=name)
                track.equibasecode=equibasecode.strip()
                track.state_province=state_province.strip()
                track.country=country.strip()
                track.timezone=timezone.strip()
                print ('##############################################')
                print (timezone)
                track.save()

                
      
        except HarnessTracksDetail.DoesNotExist:
            log.debug("DOES NOT EXIST: HarnessTracksDetail: %s" % trackmastercode)
        
        return Response(request.data, status=status.HTTP_201_CREATED)

