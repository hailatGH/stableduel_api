from rest_framework.generics import RetrieveAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import VersionRequirementSerializer
from .models import VersionRequirement


class VersionRequirementView(RetrieveAPIView):
    model = VersionRequirement
    serializer_class = VersionRequirementSerializer

    def get_object(self):
        return self.model.objects.first()

@api_view(['GET', 'POST'])
def error_500(self):
    content = {'error': 'This is a test error'}
    return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)