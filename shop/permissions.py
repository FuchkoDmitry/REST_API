from rest_framework import permissions


class IsShop(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if user.role == 'shop':
            return True
        return False
