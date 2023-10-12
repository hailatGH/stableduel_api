from rest_framework.generics import RetrieveAPIView, ListAPIView, ListCreateAPIView
from django.contrib.auth import get_user_model
from django.db.models import Q, Prefetch
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.db.models import Case, When, Sum, OuterRef, Subquery, Count
from django.db.models.functions import Coalesce
from stable_points.models import StablePoint

from follows.models import Follows
from .serializers import FollowsSerializer, FollowsUsersSerializer, UsersFollowersSerializer, FollowsHorsesSerializer
from users.serializers import ProfileSerializer
from users.models import Profile
from stables.models import Runner
from stables.serializers import RunnerSerializer
from horse_points.models import HorsePoint
from datetime import datetime

class UserFollowsViewSet(viewsets.ModelViewSet):
    queryset = Follows.objects.all()
    model = Follows
    serializer_class = FollowsSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = queryset.filter(owner=self.request.user)
        follow_type = self.request.query_params.get('follow_type', None)
        horse = self.request.query_params.get('horse', None)
        user = self.request.query_params.get('user', None)
        
        if horse is not None:
            queryset = queryset.filter(horse=horse)

        if user is not None:
            queryset = queryset.filter(user=user)

        if follow_type == Follows.HORSE:
            queryset = queryset.filter(user__isnull=True).order_by('id')
        elif follow_type == Follows.USER:
            queryset = queryset.filter(horse__isnull=True).order_by('id')
        else:
            queryset.order_by('id')

        self.queryset = queryset
        return super().list(*args, **kwargs)
        
class UserFollowsUsersView(ListAPIView):
    model = Follows
    serializer_class = FollowsUsersSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        
        follows = Follows.objects.filter(owner=self.request.user, horse__isnull=True).annotate(stable_points = Coalesce(Sum(Case(When(user__stablepoint__created_at__year=datetime.now().year, then='user__stablepoint__points'))), 0))
        
        return follows.order_by('-stable_points')

class UsersFollowersView(ListAPIView):
    model = Follows
    serializer_class = UsersFollowersSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        #Get the number of followers of me
        follows = Follows.objects.filter(user=self.request.user, horse__isnull=True).annotate(stable_points = Coalesce(Sum(Case(When(owner__stablepoint__created_at__year=datetime.now().year, then='owner__stablepoint__points'))), 0))
        return follows.order_by('-stable_points')


class UserFollowsHorsesView(ListAPIView):
    model = Follows
    serializer_class = FollowsHorsesSerializer
    permission_classes = (IsAuthenticated,)


    def get_queryset(self):
        follows = Follows.objects.filter(owner=self.request.user, user__isnull=True).select_related('horse_point')
        print(follows.order_by('-horse_point__points'))

        return follows.order_by('-horse_point__points')
