from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Sum, Value as V, Q, Exists, OuterRef
from django.db.models.functions import Coalesce
from .serializers import GameSerializer, LobbySerializer
from .models import Game, GameUser, GameExcludeUsers
from users.models import User
from stables.models import Stable
from .pagination import LeaderboardPagination

class GameViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for data to be viewed or edited.
    """
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    
    def get_queryset(self):
        start_date = self.request.query_params.get('start_date',None)
        end_date = self.request.query_params.get('end_date',None)

        is_authenticated = self.request.user.is_authenticated

        game_set = Game.objects.filter(is_private=False)
        if is_authenticated:
            private_game_users = GameUser.objects.filter(
                game=OuterRef('pk'),
                user=self.request.user
            )
            
            excluded_users = GameExcludeUsers.objects.filter(
                game=OuterRef('pk'),
                user=self.request.user
            )
            
            game_set = Game.objects.annotate(
                in_private_game=Exists(private_game_users),
                in_excluded_users=Exists(excluded_users)
            ).filter(~Q(game_state=Game.CANCELLED)).filter(Q(is_private=False) | Q(in_private_game=True)).filter(Q(in_excluded_users=False))
        else:
            game_set = Game.objects.filter(Q(is_private=False) & ~Q(game_state=Game.CANCELLED))
        
        if end_date is None and start_date is None:
            queryset = game_set
            return queryset
        elif start_date is not None and end_date is not None:
            games = game_set.filter(racecard__race_date__range=[start_date,end_date], archived=False)
            return games
        else:
            #Assume we've been given a specific date
            games = game_set.filter(racecard__race_date=start_date, archived=False)
            return games
        
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    def list(self, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = queryset.filter(archived=False)
        self.queryset = queryset
        return super().list(*args, **kwargs)


class LobbyView(generics.ListAPIView):
    serializer_class = LobbySerializer
    # pagination_class = LeaderboardPagination

    def get_queryset(self):
        game = self.request.query_params.get('game', None)

        if game is None:
            return Stable.objects.none()

        db_game = Game.objects.filter(id=game).first()
        if db_game is not None and db_game.is_private == True:
            user_in_game = GameUser.objects.filter(
                game=db_game,
                user=self.request.user
            ).exists()
            if user_in_game == False:
                return Stable.objects.none()
        
        stables = Stable.objects.filter(game=game).prefetch_related('user__profile')

        return stables

    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)
 
