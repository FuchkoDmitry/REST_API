from django.contrib import admin

from shop.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem
# Register your models here.


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'site', 'is_open']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']




@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'rrc', 'category']
    filter_horizontal = ['shops']


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'shop', 'product', 'model', 'article', 'price', 'quantity']
    fields = ('shop', ('product', 'model'), ('article', 'price', 'quantity'))


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(ProductParameter)
class ProductParameter(admin.ModelAdmin):
    list_display = ['id', 'product', 'value']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'contacts', 'created_at', 'status']
    list_filter = ['created_at', 'status', 'user']
    # filter_horizontal = ['user', 'status', 'created_at']
    # list_editable = ['status']
    fields = (('user', 'contacts'), ('created_at', 'updated_at'), 'status')
    readonly_fields = ('user', 'created_at', 'updated_at')
    # list_display_links = []
    inlines = [OrderItemInline]

    # def changeform_view(self, request, object_id=None, form_url="", extra_context=None):

    # def action_checkbox(self, obj):


