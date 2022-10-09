
from rest_framework import serializers

from shop.models import Shop, Category, Product, ProductInfo, ProductParameter


class URLSerializer(serializers.Serializer): # noqa
    url = serializers.URLField(write_only=True, required=True, label='URL адрес для импорта товаров')


class ShopsViewSerializer(serializers.ModelSerializer):
    '''Сериализатор для списка магазинов'''

    id = serializers.HyperlinkedIdentityField(view_name='shop-detail')

    class Meta:
        model = Shop
        fields = ('id', 'name', 'site')


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

