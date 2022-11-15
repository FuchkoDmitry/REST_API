from django.urls import path
from rest_framework.routers import DefaultRouter

from users.views import (
    RegisterUserView, ConfirmAccountView, LoginView,
    LogoutView, ResetPasswordView, ResetPasswordConfirmView,
    UserProfileView, UserContactsViewSet
)


router = DefaultRouter()
router.register('contacts', UserContactsViewSet)

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='user-registration'),
    path('register/confirm/', ConfirmAccountView.as_view()),
    path('login/', LoginView.as_view(), name='user-login'),
    path('logout/', LogoutView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    path('reset-password/confirm/', ResetPasswordConfirmView.as_view()),
    path('profile/', UserProfileView.as_view()),
] + router.urls
