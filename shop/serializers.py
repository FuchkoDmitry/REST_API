
from rest_framework import serializers

from shop.models import Shop, Category, Product, ProductInfo, ProductParameter, Parameter


class URLSerializer(serializers.Serializer): # noqa
    url = serializers.URLField(write_only=True, required=True, label='URL адрес для импорта товаров')


class ShopsViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'site')


class CategoriesViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'rrc')


# class ParameterSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Parameter
#         fields = ('name',)


class ProductParametersSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductsViewSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    shop = ShopsViewSerializer()
    parameters = ProductParametersSerializer(many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'product', 'shop', 'model', 'parameters', 'article', 'price', 'quantity')

# class ProductsViewSerializer(serializers.ModelSerializer):
#     category = CategoriesViewSerializer()
#     shops = ShopsViewSerializer(many=True)
#     # product_infos = ProductInfoViewSerializer(many=True)
#
#     class Meta:
#         model = Product
#         fields = ('id', 'name', 'category', 'rrc', 'shops')
#         # fields = ('id', 'name', 'category', 'rrc', 'product_infos')
#
#
# class ProductInfoViewSerializer(serializers.ModelSerializer):
#     shop = ShopsViewSerializer()
#     # product
#
#     product = ProductsViewSerializer()
#
#     class Meta:
#         model = ProductInfo
#         fields = ('id', 'product', 'shop', 'model', 'article', 'price', 'quantity')