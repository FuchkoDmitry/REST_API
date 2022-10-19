
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.utils.translation import gettext_lazy as _

from shop.models import Shop, Category, Product, ProductInfo, ProductParameter, Order, OrderItem
from users.models import UserInfo
from users.serializers import UserContactsViewSerializer


class URLSerializer(serializers.Serializer): # noqa
    url = serializers.URLField(write_only=True, required=True, label='URL адрес для импорта товаров')


class ShopsViewSerializer(serializers.ModelSerializer):
    '''Сериализатор для списка магазинов'''

    id = serializers.HyperlinkedIdentityField(view_name='shop-detail')
    is_open = serializers.BooleanField(default=True)

    class Meta:
        model = Shop
        fields = ('id', 'name', 'site', 'is_open')





class CategoriesViewSerializer(serializers.ModelSerializer):
    '''Сериализатор для списка категорий'''

    id = serializers.HyperlinkedIdentityField(view_name='category-products')

    class Meta:
        model = Category
        fields = ('id', 'name')


class ProductParametersSerializer(serializers.ModelSerializer):
    '''Сериализатор параметров продукта'''
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductsViewSerializer(serializers.ModelSerializer):
    '''Сериализатор для списка всех продуктов с уточнением наличия в магазинах'''
    id = serializers.HyperlinkedIdentityField(read_only=True, view_name='product-detail')
    shops = serializers.HyperlinkedRelatedField(read_only=True, many=True, view_name='shop-detail')
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'rrc', 'shops')


class ProductInfoSerializer(serializers.ModelSerializer):
    '''Сериализатор информации о продуктах'''

    product = serializers.StringRelatedField()
    parameters = ProductParametersSerializer(many=True)
    shop = serializers.StringRelatedField()

    class Meta:
        model = ProductInfo
        # id сделать гиперссылкой на детали о товаре
        fields = ('id', 'product', 'model', 'shop', 'article', 'price', 'quantity', 'parameters')


class ProductSerializer(serializers.ModelSerializer):
    '''Сериализатор подробной информации о конкретном продукте'''

    id = serializers.HyperlinkedIdentityField(view_name='product-detail')
    product_infos = ProductInfoSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'rrc', 'product_infos')


class CategoryItemsViewSerializer(serializers.ModelSerializer):
    '''Сериализатор для товаров определенной категории'''

    products = ProductsViewSerializer(many=True)

    class Meta:
        model = Category
        fields = ('name', 'products')


class ShopItemsViewSerializer(serializers.ModelSerializer):
    '''Сериализатор для товаров одного магазина'''

    product_infos = ProductInfoSerializer(many=True)

    class Meta:
        model = Shop
        fields = ('name', 'product_infos')


class OrderedItemsSerializer(serializers.ModelSerializer):
    '''Сериализатор просмотра товаров в заказе'''

    product = ProductInfoSerializer()

    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product', 'quantity')
        extra_kwargs = {'order': {"write_only": True}}


class BasketSerializer(serializers.ModelSerializer):
    '''Сериализатор товаров в корзине'''

    # contacts = UserContactsViewSerializer(required=False, allow_null=True, write_only=True)
    contacts = UserContactsViewSerializer(required=False, allow_null=True)
    ordered_items = OrderedItemsSerializer(many=True, read_only=True)
    total_price = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'status', 'contacts', 'ordered_items', 'total_price')
        read_only_fields = ('id',)

    def create(self, validated_data):
        items = validated_data.pop('items')

        basket, _ = Order.objects.get_or_create(**validated_data)

        for item in items:
            OrderItem.objects.update_or_create(
                order=basket,
                product_id=item['product'],
                defaults={'quantity': item.get('quantity', 1)}
            )
        return basket

    def update(self, instance, validated_data):

        items = validated_data.pop('items')
        instance.ordered_items.all().delete()
        instance = super().update(instance, validated_data)

        for item in items:
            OrderItem.objects.create(
                order=instance,
                product_id=item['product'],
                quantity=item.get('quantity', 1)
            )
        return instance

    def validate(self, attrs):
        attrs = self.initial_data

        products_quantity = {
            product: quantity for product, quantity in ProductInfo.objects.filter(
                shop__is_open=True).values_list('id', 'quantity')
        }
        items = attrs['items']
        for item in items:
            try:
                product_id = item['product']
                quantity = item['quantity']
            except KeyError:
                raise serializers.ValidationError(
                    {'fields': 'поля для передачи: "product", "quantity"'}
                )
            else:
                if product_id not in products_quantity:
                    raise serializers.ValidationError(
                        {'product': f"Продукта с id {product_id} не существует или магазин не принимает заказы"}
                    )
                elif quantity > products_quantity[product_id]:
                    raise serializers.ValidationError(
                        {'quantity': f"Товара с id {product_id} {products_quantity[product_id]}шт"}
                    )
                elif quantity <= 0:
                    raise serializers.ValidationError(
                        {'quantity': 'Значение должно быть больше нуля.'}
                    )
        return attrs


class OrderDetailsSerializer(serializers.ModelSerializer):
    '''Сериализатор деталей заказа'''

    contacts = serializers.StringRelatedField()
    ordered_items = OrderedItemsSerializer(many=True, read_only=True)
    total_price = serializers.IntegerField()

    class Meta:
        model = Order
        fields = ('id', 'contacts', 'total_price', 'status', 'created_at', 'updated_at', 'ordered_items')
