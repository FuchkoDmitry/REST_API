# from pprint import pprint

# from django.core.validators import URLValidator
from django.forms import model_to_dict
from requests import get
from requests.exceptions import ConnectionError
import yaml
from yaml.scanner import ScannerError
from rest_framework import status
# from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from urllib3.exceptions import MaxRetryError, NewConnectionError
from yaml.loader import SafeLoader

from shop.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem
from shop.permissions import IsShop
from shop.serializers import URLSerializer


class ImportProductsView(APIView):
    '''
    Класс для импорта товаров магазином.
    В post-запросе передается url с путем к yaml-файлу.
    При следующих импортах можно передавать в url сайт магазина,
    в таком случае путь к фалу будет прочитан из базы.
    '''

    permission_classes = (IsAuthenticated, IsShop)
    serializer_class = URLSerializer

    def post(self, request):
        serializer = URLSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        url = serializer.validated_data.get('url')

        if not url.endswith('.yaml'):
            shop = get_object_or_404(Shop, site=url)
            if shop:
                url = shop.url + shop.filename
            else:
                return Response({'url': 'Введите корректный url'},
                                status=status.HTTP_400_BAD_REQUEST)
        # try except возможно не надо
        try:
            stream = get(url).content
            data = yaml.load(stream, Loader=SafeLoader)
            shop_data = data['shop']
        except (MaxRetryError, NewConnectionError, ConnectionError, ScannerError, KeyError):
            return Response({'url': 'некорректный yaml файл'},
                            status=status.HTTP_400_BAD_REQUEST)

        shop, created = Shop.objects.get_or_create(user=request.user, **shop_data)
        if created and (shop.url == '' and shop.filename == ''):
            separator = url.rfind('/')
            shop.url = url[:separator + 1]
            shop.filename = url[separator + 1:]
            shop.save()

        categories = data.get('categories')
        if categories:
            for category in categories:
                category_object, _ = Category.objects.get_or_create(id=category['id'],
                                                                    name=category['name'])
                category_object.shops.add(shop.id)
                category_object.save()

        return Response({'status': model_to_dict(shop)}, status=status.HTTP_200_OK)
