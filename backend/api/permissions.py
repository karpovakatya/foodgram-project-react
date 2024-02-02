from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    # def has_permission(self, request, view):
    #     if request.method in SAFE_METHODS:
    #         return True
    #     return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS 
            or obj.author == request.user
        )
