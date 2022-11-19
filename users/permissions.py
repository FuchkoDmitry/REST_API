from rest_framework import permissions
from rest_framework.authtoken.models import Token


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class NotSocial(permissions.BasePermission):

    def has_permission(self, request, view):
        token = Token.objects.filter(user=request.user).first()
        return bool(token)
