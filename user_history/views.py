from rest_framework.generics import RetrieveAPIView, ListAPIView
from django.contrib.auth import get_user_model
from django.db.models import Q
from games.models import Game

from stables.models import Stable
from .serializers import UserHistorySerializer, PastPerformanceSerializer

User = get_user_model()

class UserHistoryView(RetrieveAPIView):
    model = User
    serializer_class = UserHistorySerializer

    def get_object(self):
        return User.objects.get(id=self.kwargs.get('id'))

class PastPerformancesView(ListAPIView):
    model = Stable
    serializer_class = PastPerformanceSerializer
    
    def get_queryset(self):
        return (Stable.objects
            .filter(user__id=self.kwargs.get('id'))
            .filter(is_valid_at_start=True)
            .exclude(game__game_state=Game.CANCELLED)
            .select_related('game', 'game__racecard', 'game__racecard__track')
            .order_by('-game__racecard__race_date'))
       
