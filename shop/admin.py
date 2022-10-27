
from django.contrib import admin, messages
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect

from shop.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem
from shop.tasks import change_status_email_task


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
    radio_fields = {'product': admin.VERTICAL}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'contacts', 'created_at', 'status']
    list_filter = ['created_at', 'status', 'user']
    # filter_horizontal = ['user', 'status', 'created_at']
    list_editable = ['status']
    fields = (('user', 'contacts'), ('created_at', 'updated_at'), 'status')
    readonly_fields = ('created_at', 'updated_at')
    # list_display_links = []
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        '''
        Перед подтверждением заказа проверяются товары в наличии.
        При успешной проверке товаров отправляется письмо пользователю
        и администратору с измененным статусом заказа. Количество товара
        в магазине уменьшается на количество товара в заказе.
        '''
        if 'status' in form.changed_data and obj.status == 'confirmed':
            with transaction.atomic():
                for item in obj.ordered_items.all():
                    try:
                        item.product.quantity -= item.quantity
                        item.product.save()
                    except IntegrityError:
                        self.message_user(request, 'недостаточно товаров', level=messages.ERROR)
                        return HttpResponseRedirect('')
        change_status_email_task.delay(obj.user.id, obj.id, obj.get_status_display())
        return super().save_model(request, obj, form, change)



