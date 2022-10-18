from rest_framework import permissions


class IsShop(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return user.role == 'shop'


class IsBuyer(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return user.role == 'buyer'
