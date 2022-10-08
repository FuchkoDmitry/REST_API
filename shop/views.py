
from requests import get
from requests.exceptions import ConnectionError
import yaml
from yaml.scanner import ScannerError
from rest_framework import status
from rest_framework.generics import get_object_or_404, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from urllib3.exceptions import MaxRetryError, NewConnectionError
from yaml.loader import SafeLoader
from django_filters.rest_framework import DjangoFilterBackend

from shop.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem
from shop.permissions import IsShop
from shop.serializers import URLSerializer, ShopsViewSerializer, CategoriesViewSerializer, ProductsViewSerializer


class ImportProductsView(APIView):
    '''
    Класс для импорта товаров магазином.
    В post-запросе передается url с путем к yaml-файлу.
    При следующих импортах можно передавать в url сайт магазина,
    если параметр site передавался в yaml-файле при первом
    импорте. В таком случае путь к фалу будет прочитан из базы.
    '''

    permission_classes = (IsAuthenticated, IsShop)
    serializer_class = URLSerializer

    def post(self, request):
        serializer = URLSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        url = serializer.validated_data.get('url')

        if not url.endswith('.yaml'):
            shop = get_object_or_404(Shop, site=url, user=request.user)
            if shop:
                url = shop.url + shop.filename
            else:
                return Response({'url': 'Введите корректный url'},
                                status=status.HTTP_400_BAD_REQUEST)
        try:
            stream = get(url).content
            data = yaml.load(stream, Loader=SafeLoader)
            shop_data = data['shop']
        except (KeyError, MaxRetryError, NewConnectionError, ConnectionError, ScannerError):
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
        ProductInfo.objects.filter(shop_id=shop.id).delete()
        for item in data['goods']:
            product, _ = Product.objects.get_or_create(
                name=item['name'], category_id=item['category'], rrc=item['price_rrc']
            )
            product_info = ProductInfo.objects.create(
                shop_id=shop.id, product_id=product.id, model=item['model'],
                article=item['id'], price=item['price'], quantity=item['quantity']
            )
            for name, value in item['parameters'].items():
                parameter, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.update_or_create(
                    product_id=product_info.id, parameter_id=parameter.id,
                    defaults={'value': value}
                )

        return Response({'status': 'Данные загружены'}, status=status.HTTP_200_OK)


class ShopsView(ListAPIView):
    '''Список магазинов'''
    serializer_class = ShopsViewSerializer
    queryset = Shop.objects.filter(is_open=True).all()


class CategoriesView(ListAPIView):
    '''Список категорий'''
    serializer_class = CategoriesViewSerializer
    queryset = Category.objects.all()


# class ProductsView(ListAPIView):
#     '''
#     Список продуктов с фильтрацией по категории и магазину
#     '''
#     queryset = Product.objects.all()
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['category', 'shop', 'id']
#     serializer_class = ProductsViewSerializer
#
#
# # ???
# class ProductInfoView(RetrieveAPIView):
#     queryset = ProductInfo.objects.all()
#     serializer_class = ProductsViewSerializer


class ProductsView(ListAPIView):
    queryset = ProductInfo.objects.filter(shop__is_open=True).all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product_id', 'shop_id', 'product__category']
    serializer_class = ProductsViewSerializer
