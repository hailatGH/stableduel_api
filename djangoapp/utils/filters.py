from rest_framework.filters import BaseFilterBackend

class IsUserFilterBackend(BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """
    def filter_queryset(self, request, queryset, view):

        if request.user.is_superuser:
           return queryset.all()

        return queryset.filter(user=request.user)