from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import Signal, receiver

order_confirmed = Signal()


@receiver(order_confirmed)
def order_confirmed_signal(user, contacts, basket, **kwargs):
    products = basket.ordered_items.only('product__model', 'product__price')
    message = EmailMultiAlternatives(
        subject='Спасибо за заказ.',
        body=f'{user.username}, заказ номер {basket.id} создан. \n '
             f'Состав заказа: '
             f'{[f"{p.product.model}, {float(p.product.price)} кол-во: {p.quantity}" for p in products]}. \n'
             f'Адрес доставки: {contacts}. \n Сумма к оплате: {basket.total_price} р.',
        to=[user.email],
    )
    message.send()
