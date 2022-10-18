from django.db.models import Sum, F
from requests import get
from requests.exceptions import ConnectionError
import yaml
from rest_framework.filters import SearchFilter
from yaml.scanner import ScannerError
from rest_framework import status
from rest_framework.generics import get_object_or_404, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.settings import api_settings
from urllib3.exceptions import MaxRetryError, NewConnectionError
from yaml.loader import SafeLoader
from django_filters.rest_framework import DjangoFilterBackend

from shop.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem
from shop.permissions import IsShop, IsBuyer
from shop.serializers import URLSerializer, ShopsViewSerializer, CategoriesViewSerializer, \
    CategoryItemsViewSerializer, ProductSerializer, ShopItemsViewSerializer, ProductInfoSerializer, \
    ProductsViewSerializer, BasketSerializer, OrderedItemsSerializer
from shop.signals import order_confirmed
from shop.mixins import MyPaginationMixin
from users.models import UserInfo
from users.serializers import UserContactsViewSerializer


class ImportProductsView(APIView):
    '''
    Класс для импорта товаров магазином.
    В post-запросе передается url с путем к yaml-файлу.
    При следующих импортах можно передавать в url сайт магазина,
    если параметр site передавался в yaml-файле при первом
    импорте. В таком случае путь к файлу будет прочитан из базы.
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


class CategoryItemsView(RetrieveAPIView):
    '''Все товары определенной категории'''
    queryset = Category.objects.prefetch_related('products')
    serializer_class = CategoryItemsViewSerializer


class ShopItemsView(RetrieveAPIView):
    '''Все товары определенного магазина'''
    queryset = Shop.objects.prefetch_related('product_infos')
    serializer_class = ShopItemsViewSerializer


class ProductView(RetrieveAPIView):
    '''Подробная информация о продукте'''
    queryset = Product.objects.prefetch_related('product_infos')
    serializer_class = ProductSerializer


class ProductsView(ListAPIView):
    '''
    Список всех продуктов с уточнением наличия в магазинах.
    Возможна фильтрация по параметрам 'id', 'shops__id', 'category'
    и поиск по параметру 'name'.
    '''
    queryset = Product.objects.prefetch_related('shops')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['id', 'shops__id', 'category']
    search_fields = ['name']
    serializer_class = ProductsViewSerializer


class BasketView(APIView):
    '''
    Класс для работы с корзиной
    '''

    permission_classes = [IsAuthenticated, IsBuyer]

    def get(self, request):

        '''Просмотреть корзину'''

        basket = Order.objects.filter(
            user=self.request.user, status='basket').prefetch_related(
            'ordered_items').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('ordered_items__product__price'))).first()
        if not basket:
            return Response({'basket': 'Ваша корзина пуста.'},
                            status=status.HTTP_200_OK)
        serializer = BasketSerializer(basket)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        '''
        Добавить товары в корзину, внести изменения в корзину.
        '''

        items = request.data.get('items')
        if not items:
            return Response({'items': 'Укажите товары для добавления'},
                            status=status.HTTP_400_BAD_REQUEST)
        data = {
            'user': request.user,
            'items': items, 'status': 'basket'
        }
        serializer = BasketSerializer(data=data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response({"items": 'Товары добавлены в корзину'},
                        status=status.HTTP_200_OK)

    def put(self, request):
        '''
        Обновить товары в корзине.
        '''

        items = request.data.get('items')
        if not items:
            return Response({'items': 'Укажите товары для добавления'},
                            status=status.HTTP_400_BAD_REQUEST)

        basket, _ = Order.objects.get_or_create(
            user=request.user, status='basket')
        data = {
            'user': request.user,
            'items': items, 'status': 'basket'
        }
        serializer = BasketSerializer(data=data)

        if serializer.is_valid(raise_exception=True):
            serializer.update(basket, serializer.validated_data)
        return Response({"items": 'Товары добавлены в корзину'},
                        status=status.HTTP_200_OK)

    def delete(self, request):
        '''Очистить корзину'''
        instance = Order.objects.filter(user=request.user, status='basket').first()
        if instance:
            instance.delete()
        return Response({"Ваша корзина пуста."}, status=204)


class ConfirmOrderView(APIView):
    '''
    Подтверждение заказа.
    Для подтверждения заказа необходимо передать контакты.
    возможно передать id из имеющихся контактов или все поля
    ("city", "street", "house", "apartment", "phone") для создания
    новых контактов.
    '''
    permission_classes = [IsAuthenticated, IsBuyer]


    def post(self, request):
        contacts = request.data
        contacts_id = contacts.pop('id', 0)
        user = request.user
        basket = Order.objects.filter(user=user, status='basket').prefetch_related(
            'ordered_items').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('ordered_items__product__price')
                            )).first()
        if not basket:
            return Response({"basket": "Сначала добавьте товары в корзину"},
                            status=400)
        if contacts:
            serializer = UserContactsViewSerializer(data=contacts)
            if serializer.is_valid(raise_exception=True):
                contact = serializer.save(user=user)
                basket.status, basket.contacts = 'new', contact
                basket.save()
        elif contacts_id:
            contact = get_object_or_404(UserInfo, id=contacts_id, user=user)
            basket.status, basket.contacts = 'new', contact
            basket.save()
        order_confirmed.send(sender=self.__class__, user=user, basket=basket, contacts=contact)
        return Response({"Спасибо за заказ. На вашу почту отправлено письмо с деталями"},
                        status=201)


class GetOrders(APIView, MyPaginationMixin):
    """
    Получить список заказов
    """

    permission_classes = [IsAuthenticated, IsBuyer]
    serializer_class = BasketSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get(self, request):
        orders = Order.objects.filter(user=self.request.user).order_by('-updated_at').prefetch_related(
            'ordered_items').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('ordered_items__product__price')))
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.serializer_class(orders, many=True)
            return self.get_paginated_response(serializer.data)
        # return Response(serializer.data, status=200)


# class GetOrders(ListAPIView):
#     permission_classes = [IsAuthenticated, IsBuyer]
#     serializer_class = BasketSerializer
#
#     def get_queryset(self):
#         orders = Order.objects.filter(user=self.request.user).order_by('-updated_at').prefetch_related(
#             'ordered_items').annotate(
#             total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product__price')))
#         return orders






