from rest_framework import permissions

class IsCurrentUser(permissions.BasePermission):
    """
    Verify that user is the currently logged in user
    """
    def has_permission(self, request, view):
        return not request.user.is_anonymous

    def has_object_permission(self, request, view, obj):
        is_owned_obj = obj.user == request.user if obj.user is not None else False
        
        if request.method == 'GET':
            return obj.game.started or is_owned_obj

        return is_owned_obj