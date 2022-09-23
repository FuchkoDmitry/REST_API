from django.urls import path

from users.views import (
    RegisterUserView, ConfirmAccountView, LoginView,
    LogoutView, ResetPasswordView, ResetPasswordConfirmView,
    UserProfileView, UserContactsView
)


urlpatterns = [
    path('register/', RegisterUserView.as_view()),
    path('register/confirm/', ConfirmAccountView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
    path('reset-password/confirm/', ResetPasswordConfirmView.as_view()),
    path('profile/', UserProfileView.as_view()),
    path('contacts/<int:pk>', UserContactsView.as_view())
]
