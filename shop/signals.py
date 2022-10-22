from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import Signal, receiver

from users.models import User

order_confirmed = Signal()


@receiver(order_confirmed)
def order_confirmed_signal(user, contacts, basket, **kwargs):
    admin = User.objects.get(is_superuser=True)
    products = [
        f'{i + 1}. {p.product.model}, {float(p.product.price)} кол-во: {p.quantity}'
        for i, p in enumerate(basket.ordered_items.all())
    ]
    products = '\n'.join(products)
    message = EmailMultiAlternatives(
        subject='Спасибо за заказ.',
        body=f'{user.username}, заказ номер {basket.id} создан. \n '
             f'Состав заказа:\n{products}. \n'
             f'Адрес доставки: {contacts}. \n Сумма к оплате: {basket.total_price} р.',
        to=[user.email],
    )

    message_to_admin = EmailMultiAlternatives(
        subject='Новый заказ',
        body=f'Заказ №{basket.id} создан. \n Пользователь: {user.username}\n'
             f'К оплате: {basket.total_price}\n Адрес доставки: {contacts} \n'
             f'Состав заказа:\n{products}',
        to=[admin.email]
    )

    message.send()
    message_to_admin.send()
