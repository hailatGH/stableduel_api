from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import NotificationSerializer
from .models import Notification
from utils.filters import IsUserFilterBackend
from games.models import Game

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for data to be viewed or edited.
    """
    queryset = Notification.objects.filter(expired=False)
    serializer_class = NotificationSerializer
    filter_backends = (IsUserFilterBackend, DjangoFilterBackend)
    filter_fields = ('user', 'notif_type', 'action')

    @action(detail=True, methods=['post', 'delete'])
    def dismiss(self, request, pk=None):

        if pk:
            try:
                notification = Notification.objects.get(id=pk)

                if notification.is_dismissible:
                    if request.user.is_superuser or notification.user == request.user:
                        notification.delete()
                        return Response("Notification dismissed", status=status.HTTP_200_OK)
                else:
                    return Response("Notification cannot be dismissed", status=status.HTTP_405_METHOD_NOT_ALLOWED)

            except Notification.DoesNotExist:
                return Response("Not found", status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_200_OK)

class InterestsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        """
        Return a list of all interests for requesting user
        """
        interests = ['main']

        games = Game.objects.filter(stable__user=request.user, finished=False).distinct()

        for game in games:
            interests.append('game-{}'.format(game.id))

        return Response(interests)


