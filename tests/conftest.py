import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.models import User


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def model_factory():
    def factory(model, *args, **kwargs):
        return baker.make(model, *args, **kwargs)
    return factory


@pytest.fixture
def create_user():
    return get_user_model().objects.create_user(
                username='username', email='example@mail.ru',
                password='QWERTY!1qwerty', is_active=True
            )


@pytest.fixture
def get_token(db, create_user):
    user = create_user
    token, _ = Token.objects.get_or_create(user=user)
    return token




