
import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK


from shop.models import Shop, Product, ProductInfo


@pytest.mark.django_db
def test_shops_list(client, model_factory):
    '''Проверка списка магазинов с сортировкой'''
    shops = model_factory(Shop, _quantity=5)
    shops.sort(key=lambda x: x.name.lower())
    url = reverse('shops-list')

    response = client.get(url)

    assert response.status_code == HTTP_200_OK

    shops_list = response.json()
    assert shops_list['count'] == len(shops)
    for index, shop in enumerate(shops_list['results']):
        assert shop['name'] == shops[index].name


@pytest.mark.django_db
def test_get_shop(client, model_factory):
    shop = model_factory(Shop)
    url = reverse('shops-detail', kwargs={'pk': shop.pk})

    response = client.get(url)
    response_json = response.json()

    assert response.status_code == HTTP_200_OK

    assert response_json['name'] == shop.name


@pytest.mark.django_db
def test_products_filter(client, model_factory):
    shop = model_factory(Shop)
    products = model_factory(Product, _quantity=5)
    model_factory(ProductInfo, shop=shop, product=products[0], price=100, quantity=1)

    url = reverse('products-list')
    response = client.get(url, {'shops__id': shop.id})
    response_json = response.json()

    assert response.status_code == HTTP_200_OK
    assert response_json['count'] == 1


@pytest.mark.django_db
def test_products_searching(client, model_factory):
    products = model_factory(Product, _quantity=5)

    url = reverse('products-list')
    response = client.get(url, {'search': products[1].name})
    response_json = response.json()

    assert response.status_code == HTTP_200_OK
    assert response_json['count'] == 1


@pytest.mark.parametrize('role, status, auth_method, is_open', [
    ('shop', 200, 'Token ', True),
    ('shop', 401, 'Token 2', False)
]
                         )
def test_partner_change_state(client, model_factory, get_token, role, status, auth_method, is_open):

    token = get_token
    shop = model_factory(Shop, user=token.user, is_open=False)

    url = reverse('partner-details', kwargs={'pk': shop.id})
    client.credentials(HTTP_AUTHORIZATION=auth_method + token.key)
    response = client.patch(url, {'is_open': 'on'})
    response_json = response.json()

    assert response.status_code == status
    assert response_json.get('is_open', shop.is_open) == is_open
