from django.contrib import admin

from shop.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem
# Register your models here.


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'site', 'is_open']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'shop']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'rrc', 'category', 'shops']


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'shop', 'product', 'model', 'article', 'price', 'quantity']


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(ProductParameter)
class ProductParameter(admin.ModelAdmin):
    list_display = ['id', 'product', 'value']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'contacts', 'created_at', 'updated_at', 'status']


