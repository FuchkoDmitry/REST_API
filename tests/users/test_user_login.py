import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_201_CREATED
from rest_framework.authtoken.models import Token


@pytest.mark.django_db
def test_user_registration(client, django_user_model):
    url = reverse('user-registration')
    data = {
        'username': 'user1', 'email': 'example@yandex.ru',
        'password': 'PaSSword@2', 'password2': 'PaSSword@2'
    }

    response = client.post(url, data)
    response_json = response.json()
    new_user = django_user_model.objects.get(email=data['email'])

    assert response.status_code == HTTP_201_CREATED
    assert response_json['username'] == new_user.username
    assert new_user.is_active is False


@pytest.mark.django_db
def test_correct_login(client, create_user):
    user = create_user
    url = reverse('user-login')
    data = {'username': user.email, 'password': 'QWERTY!1qwerty'}

    response = client.post(url, data)
    token = Token.objects.get(user=user)

    assert response.status_code == HTTP_200_OK
    assert response.json()['email'] == user.email
    assert response.json()['token'] == token.key
    assert 'token' in response.json()


@pytest.mark.django_db
def test_incorrect_login(client, create_user):
    user = create_user
    url = reverse('user-login')
    data = {'username': user.email, 'password': 'bad_password'}

    response = client.post(url, data)

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert 'Некорректные имя пользователя и/или пароль' in response.json()['error']
    assert 'token' not in response.json()


@pytest.mark.django_db
def test_required_fields(client, create_user):

    user = create_user
    url = reverse('user-login')
    data = {'username': user.email}

    response = client.post(url, data)

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert 'Обязательное поле.' in response.json()['password']
    assert 'token' not in response.json()


@pytest.mark.django_db
def test_logout(client, get_token):

    user_token = get_token
    url = reverse('user-logout')
    token_count = Token.objects.count()

    client.credentials(HTTP_AUTHORIZATION='Token ' + user_token.key)
    response = client.post(url)
    token_count_after_user_logout = Token.objects.count()

    assert response.status_code == HTTP_200_OK
    assert token_count_after_user_logout == token_count - 1
    assert user_token.key not in Token.objects.all()

