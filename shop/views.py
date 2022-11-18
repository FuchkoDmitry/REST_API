from django.db.models import Sum, F
from drf_yasg import openapi
from requests import get
from requests.exceptions import ConnectionError
import yaml
from rest_framework.filters import SearchFilter
from yaml.scanner import ScannerError
from rest_framework import status
from rest_framework.generics import get_object_or_404, ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.settings import api_settings
from urllib3.exceptions import MaxRetryError, NewConnectionError
from yaml.loader import SafeLoader
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema

from shop.models import Shop, Category, Product, Order
from shop.permissions import IsShop, IsBuyer
from shop.serializers import (
    URLSerializer, ShopsViewSerializer, CategoriesViewSerializer,
    CategoryItemsViewSerializer, ProductSerializer, ShopItemsViewSerializer,
    ProductsViewSerializer, BasketSerializer, OrderDetailsSerializer, OrdersSerializer
)

from shop.mixins import MyPaginationMixin
from shop.tasks import new_order_email_task, new_order_email_to_admin_task, do_import_task
from users.models import UserInfo
from users.permissions import IsOwner
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
        except (KeyError, MaxRetryError, NewConnectionError, ConnectionError, ScannerError):
            return Response({'url': 'некорректный yaml файл'},
                            status=status.HTTP_400_BAD_REQUEST)

        do_import_task.delay(url, request.user.id, data)

        return Response({'status': 'Данные загружены'}, status=status.HTTP_200_OK)


class GetOrUpdateStatus(RetrieveUpdateAPIView):
    '''Получить или изменить статус получения заказов'''
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Shop.objects.all()
    serializer_class = ShopsViewSerializer


class GetPartnerOrders(ListAPIView):
    '''Получить заказы пользователей'''

    permission_classes = [IsAuthenticated, IsShop]
    serializer_class = OrdersSerializer

    def get_queryset(self):
        queryset = Order.objects.filter(ordered_items__product__shop__user=self.request.user).exclude(
            status='basket').prefetch_related('ordered_items', 'ordered_items__product').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('ordered_items__product__price'))).distinct()
        return queryset


class ShopsViewSet(ReadOnlyModelViewSet):
    '''Список магазинов и товары из одного магазина'''

    def get_queryset(self):
        if self.action == 'retrieve':
            return Shop.objects.filter(is_open=True).prefetch_related('product_infos')
        return Shop.objects.filter(is_open=True).all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ShopItemsViewSerializer
        return ShopsViewSerializer


class CategoriesViewSet(ReadOnlyModelViewSet):
    '''Список категорий и товары определенной категории'''

    def get_queryset(self):
        if self.action == 'retrieve':
            return Category.objects.prefetch_related('products')
        return Category.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CategoryItemsViewSerializer
        return CategoriesViewSerializer


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

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'items': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT, properties={
                        'product': openapi.Schema(type=openapi.TYPE_NUMBER, description='positive integer'),
                        'quantity': openapi.Schema(type=openapi.TYPE_NUMBER, description='positive integer')
                    }),
                description='items'),
        }
    ))
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

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'items': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT, properties={
                        'product': openapi.Schema(type=openapi.TYPE_NUMBER, description='positive integer'),
                        'quantity': openapi.Schema(type=openapi.TYPE_NUMBER, description='positive integer')
                    }),
                description='items'),
        }
    ))
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
        basket = Order.objects.filter(user=user, status='basket').first()
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
        else:
            return Response({"Необходимо передать контаты для доставки"}, status=400)
        new_order_email_task.delay(user.id, basket.id, contact.id)
        new_order_email_to_admin_task.delay(user.id, basket.id, contact.id)
        # order_confirmed.send(sender=self.__class__, user=user, basket=basket, contacts=contact)
        return Response({"Спасибо за заказ. На вашу почту отправлено письмо с деталями"},
                        status=201)


class GetOrders(APIView, MyPaginationMixin):
    """
    Получить список заказов
    """

    permission_classes = [IsAuthenticated, IsBuyer]
    serializer_class = OrdersSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get(self, request):
        orders = Order.objects.filter(user=self.request.user).order_by('-updated_at').prefetch_related(
            'ordered_items').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('ordered_items__product__price')))
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.serializer_class(orders, many=True)
            return self.get_paginated_response(serializer.data)


class GetOrderDetail(RetrieveAPIView):
    '''Детали заказа'''

    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Order.objects.prefetch_related('ordered_items').annotate(
            total_price=Sum(F('ordered_items__quantity') * F('ordered_items__product__price')))
    serializer_class = OrderDetailsSerializer
