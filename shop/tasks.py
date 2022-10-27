from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from celery import shared_task
from django.db.models import Sum, F

from shop.models import Order, Shop, Category, ProductInfo, Product, Parameter, ProductParameter
from users.models import User, UserInfo


@shared_task()
def change_status_email_task(user_id, order_id, status):

    '''Письмо о изменении статуса заказа'''

    user = User.objects.get(id=user_id)
    admin = User.objects.get(is_superuser=True)
    send_mail(
        'Обновлен статус заказа',
        f'Заказ № {order_id}, статус: {status}',
        settings.EMAIL_HOST_USER,
        [user.email, admin.email]
    )


@shared_task()
def new_order_email_task(user_id, basket_id, contacts_id):

    '''Письмо о создании нового заказа'''

    user = User.objects.get(id=user_id)
    basket = Order.objects.filter(id=basket_id).prefetch_related(
        'ordered_items', 'ordered_items__product').annotate(
        total_price=Sum(F('ordered_items__quantity') * F('ordered_items__product__price')
                        )).first()
    contacts = UserInfo.objects.get(id=contacts_id)
    products = [
        f'{i + 1}. {p.product.model}, {float(p.product.price)} кол-во: {p.quantity}'
        for i, p in enumerate(basket.ordered_items.all())
    ]
    products = '\n'.join(products)

    send_mail(
        subject='Спасибо за заказ.',
        message=f'{user.username}, заказ номер {basket.id} создан. \n '
             f'Состав заказа:\n{products}. \n'
             f'Адрес доставки: {contacts}. \n Сумма к оплате: {basket.total_price} р.',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False
    )


@shared_task()
def new_order_email_to_admin_task(user_id, basket_id, contacts_id):

    '''Письмо о создании нового заказа администратору'''

    user = User.objects.get(id=user_id)
    admin = User.objects.get(is_superuser=True)
    basket = Order.objects.filter(id=basket_id).prefetch_related(
        'ordered_items', 'ordered_items__product').annotate(
        total_price=Sum(F('ordered_items__quantity') * F('ordered_items__product__price')
                        )).first()
    contacts = UserInfo.objects.get(id=contacts_id)
    products = [
        f'{i + 1}. {p.product.model}, {float(p.product.price)} кол-во: {p.quantity}'
        for i, p in enumerate(basket.ordered_items.all())
    ]
    products = '\n'.join(products)

    send_mail(
        subject='Новый заказ',
        message=f'Заказ №{basket.id} создан. \n Пользователь: {user.username}\n'
             f'К оплате: {basket.total_price}\n Адрес доставки: {contacts} \n'
             f'Состав заказа:\n{products}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[admin.email],
        fail_silently=False
    )


@shared_task()
def do_import_task(url, user_id, data):
    with transaction.atomic():
        shop, created = Shop.objects.get_or_create(user_id=user_id, **data['shop'])
        if created and (not shop.url and not shop.filename):
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
