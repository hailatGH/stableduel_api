from django.http import Http404
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from reversion.views import RevisionMixin

from .serializers import StableSerializer, RunnerSerializer, RunnerDetailsSerializer
from .models import Stable, Runner
from games.models import Game, GameUser
from .permissions import IsCurrentUser

class StableViewSet(RevisionMixin, viewsets.ModelViewSet):
    """
    API endpoint for data to be viewed or edited.
    """
    queryset = Stable.objects.all().prefetch_related('runners').select_related('game')
    serializer_class = StableSerializer
    permission_classes = (IsCurrentUser, )
    filter_fields = ('user', 'game')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = queryset.filter(Q(user=request.user) | Q(game__started=True))

        if (self.request.query_params.get('game') is None):
            queryset = queryset.filter(game__archived=False)
        else:
            game = self.request.query_params.get('game', None)
            db_game = Game.objects.filter(id=game).first()
            if db_game.is_private == True:
                user_in_game = GameUser.objects.filter(
                    game=db_game,
                    user=self.request.user
                ).exists()
                if user_in_game == False:
                    return Stable.objects.none()

        self.queryset = queryset
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        content = {'Cannot delete your stable, the game has begun'}
        stable = self.get_object()
        self.check_object_permissions(self.request, stable)
        if stable.game.game_state == Game.OPEN:
            self.perform_destroy(stable)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def create (self, request):
        if str(request.user.id) != str(request.data['user']):
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        game = request.data['game']
        db_game = Game.objects.filter(id=game).first()
        if db_game.is_private == True:
            user_in_game = GameUser.objects.filter(
                game=db_game,
                user=self.request.user
            ).exists()
            if user_in_game == False:
                return Response(status=status.HTTP_403_FORBIDDEN)

        return super().create(request)

class RunnerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for runners
    """
    queryset = Runner.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RunnerDetailsSerializer
        return RunnerSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        race_number = self.request.query_params.get('race_number', None)
        racecard = self.request.query_params.get('racecard', None)

        if(race_number is not None):
            if(racecard is None):
                content = {'Racecard must be specified if race number is given'}
                return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            else:
                queryset=queryset.filter(racecard=racecard,race_number=race_number)
        elif (racecard is not None):
            queryset = queryset.filter(racecard=racecard)


        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class HorseDetailView(APIView):
    """
    API endpoint for most recent version of runners(horses)
    """

    def get(self, request, external_id):
        #getting most up to date version of this runner
        runner = Runner.objects.filter(external_id=external_id).order_by('-updated_at').first()
        if runner is None:
            raise Http404

        return Response(RunnerDetailsSerializer(runner).data)

class CanCreateStableView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        if(request.user.profile.is_admin == True):
            return Response(False)

        self.game = Game.objects.get(id=self.request.query_params.get('game', None))
        
        #-1 indicates an infinite number of stables.  Go ahead and return try without querying for stables
        if (self.game.stable_limit == -1): 
            return Response(True)

        existing_stables = Stable.objects.filter(user=request.user, game=self.game).count()

        if(existing_stables + 1 > self.game.stable_limit):
            return Response(False)

        return Response(True)
    