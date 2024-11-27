from rest_framework import permissions

class IsCurrentUser(permissions.BasePermission):
    """
    Verify that user is the currently logged in user
    """
    def has_permission(self, request, view):
        return not request.user.is_anonymous

    def has_object_permission(self, request, view, obj):
        return obj == request.user