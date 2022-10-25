

from django.conf import settings
from django.core.mail import send_mail

from celery import shared_task

from users.models import User, ConfirmEmailToken


@shared_task()
def user_register_email_task(user_id):

    '''Отправка письма с подтверждением регистрации'''

    user = User.objects.get(id=user_id)
    token, _ = ConfirmEmailToken.objects.get_or_create(user=user)

    send_mail(
        subject='Подтверждение регистрации',
        message=f'{user.username}, ваш токен для подтверждения регистрации {token.token}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False
    )


@shared_task()
def account_confirmed_email_task(email):

    '''Отправка письма о подтверждении аккаунта'''

    user = User.objects.get(email=email)

    send_mail(
        subject='Учётная запись подтверждена',
        message=f'{user.username}, поздравляем! Ваша учетная запись подтверждена',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False
    )


@shared_task()
def reset_password_email_task(user_id):

    '''Письмо о сбросе пароля'''

    user = User.objects.get(id=user_id)
    token, _ = ConfirmEmailToken.objects.get_or_create(user=user)

    send_mail(
        subject='Заявка на сброс пароля',
        message=f'{user.username}, Ваш токен для сброса пароля: {token.token}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False
    )


@shared_task()
def reset_password_confirmed_email_task(user_id):

    '''Письмо об успешной смене пароля'''

    user = User.objects.get(id=user_id)

    send_mail(
        subject='Пароль успешно обновлён.',
        message=f'{user.username}, Пароль был успешно обновлен',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False
    )

