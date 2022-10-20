from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator
from django.conf import settings


USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),
)

# Create your models here.


class UserManager(BaseUserManager):
    """
    Класс менеджера пользователей
    """
    use_in_migrations = True

    def _create_user(self, email, password, contacts=None, **extra_fields):
        """
        создание и сохранение пользователя по email и паролю
        """
        if not email:
            raise ValueError('Вы не ввели поле email')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        ###
        # if contacts:
        #     user_contacts = UserInfo(user=user, **contacts)
        # else:
        #     user_contacts = UserInfo(user=user)
        # user_contacts.save()
        ###
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Кастомная модель пользователя
    """
    REQUIRED_FIELDS = []
    objects = UserManager()
    USERNAME_FIELD = 'email'
    username_validator = UnicodeUsernameValidator()

    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _('Пользователь с таким e-mail существует')
        })
    username = models.CharField(
        _('username'),
        max_length=50,
        help_text=_('Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
        unique=True,
        blank=False
    )
    role = models.CharField(
        max_length=5,
        choices=USER_TYPE_CHOICES,
        default='buyer',
        verbose_name='Тип пользователя',
        error_messages={"invalid_choice": 'Необходимо выбрать "Buyer" или "Shop"'}
    )
    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active.'
            'Unselect this instead of deleting accounts'
        )
    )
    company = models.CharField(
        verbose_name="Компания",
        max_length=50,
        blank=True
    )
    position = models.CharField(
        verbose_name="Должность",
        max_length=50,
        blank=True
    )

    def __str__(self):
        return '%s %s(%s)' % (self.first_name, self.last_name, self.email)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)


class ConfirmEmailToken(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Токен подтверждения Email и смены пароля'
        verbose_name_plural = 'Токены подтверждения Email и смены пароля'

    @staticmethod
    def generate_token():
        return get_token_generator().generate_token()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return 'Password reset token for %s' % self.user


class UserInfo(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    city = models.CharField(max_length=50, verbose_name='Город')
    street = models.CharField(max_length=100, verbose_name='Улица')
    house = models.CharField(max_length=10, verbose_name='Дом')
    apartment = models.CharField(max_length=10, verbose_name='Квартира')
    phone = models.CharField(max_length=20, verbose_name='Телефон')

    def __str__(self):
        return f'г. {self.city}, ул. {self.street}- {self.house}- {self.apartment}. тел: {self.phone}'

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = "Контакты"
        ordering = ['user', 'city']
