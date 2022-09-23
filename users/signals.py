from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.dispatch import Signal, receiver

from users.models import ConfirmEmailToken

new_user_registered = Signal()
account_confirmed = Signal()
reset_password = Signal()
reset_password_confirmed = Signal()


@receiver(new_user_registered)
def new_user_registered_signal(instance, **kwargs):
    token, _ = ConfirmEmailToken.objects.get_or_create(user=instance)

    message = EmailMultiAlternatives(
        subject='Подтверждение регистрации',
        body=f'{instance.username}, ваш токен для подтверждения регистрации {token.token}',
        to=[instance.email],
        bcc=[settings.EMAIL_HOST_USER]
    )

    message.send()


@receiver(account_confirmed)
def account_confirmed_signal(instance, **kwargs):
    message = EmailMultiAlternatives(
        subject='Учётная запись подтверждена',
        body=f'{instance.username}, поздравляем! Ваша учетная запись подтверждена',
        to=[instance.email]
        # bcc=[settings.EMAIL_HOST_USER]
    )

    message.send()


@receiver(reset_password)
def reset_password_signal(instance, **kwargs):
    token, _ = ConfirmEmailToken.objects.get_or_create(user=instance)
    message = EmailMultiAlternatives(
        subject='Заявка на сброс пароля',
        body=f'{instance}, Ваш токен для сброса пароля: {token.token}',
        to=[instance.email]
    )

    message.send()


@receiver(reset_password_confirmed)
def reset_password_confirmed_signal(instance, **kwargs):
    message = EmailMultiAlternatives(
        subject='Пароль успешно обновлён.',
        body=f'{instance}, Пароль был успешно обновлен',
        to=[instance.email]
    )

    message.send()
