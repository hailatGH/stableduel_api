from rest_framework import generics
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth import get_user_model

User = get_user_model()

from .serializers import GlobalLeaderboardSerializer
from .pagination import GlobalLeaderboardPagination

class GlobalLeaderboardView(generics.ListAPIView):
    serializer_class = GlobalLeaderboardSerializer
    pagination_class = GlobalLeaderboardPagination
    queryset = User.objects.filter(profile__isnull=False)

    @method_decorator(cache_page(30))
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)
 