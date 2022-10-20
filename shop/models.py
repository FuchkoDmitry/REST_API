
from django.db import models
from django.conf import settings

# Create your models here.
from users.models import UserInfo


class Shop(models.Model):
    name = models.CharField(max_length=75, verbose_name="Название", db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Владелец"
    )
    site = models.URLField(verbose_name="Сайт", blank=True)
    url = models.URLField(verbose_name="Ссылка(путь к файлу)", blank=True)
    filename = models.CharField(max_length=55, verbose_name="Имя файла", blank=True)
    is_open = models.BooleanField(verbose_name="Статус получения заказов", default=True)

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Список магазинов"
        ordering = ("name",)

    def __str__(self):
        return f'"{self.name}"'


class Category(models.Model):

    name = models.CharField(max_length=50, verbose_name="Название")
    shops = models.ManyToManyField(Shop, related_name="categories", blank=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Список категорий"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория", related_name='products')
    rrc = models.PositiveIntegerField(verbose_name="Рекомендованная розничная цена")
    shops = models.ManyToManyField(Shop, related_name="products",
                                   through="ProductInfo", through_fields=('product', 'shop'))

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Список продуктов"
        ordering = ('name',)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name="Магазин",
                             related_name="product_infos", blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт",
                                related_name="product_infos", blank=True)
    model = models.CharField(max_length=100, verbose_name="Модель")
    article = models.PositiveIntegerField(verbose_name="Код товара")
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="цена")
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Информация о продукте"
        verbose_name_plural = "Информация о продуктах"
        unique_together = ("shop", "product", "article")

    def __str__(self):
        return f'{self.shop} {self.model}, {self.price} р.'


class Parameter(models.Model):
    name = models.CharField(max_length=55, verbose_name="Параметр")

    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Список параметров"

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product = models.ForeignKey(ProductInfo, on_delete=models.CASCADE,
                                verbose_name="Информация о продукте", blank=True,
                                related_name="parameters")
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE,
                                  verbose_name="имя параметра", blank=True,
                                  related_name="products")
    value = models.CharField(max_length=55, verbose_name="Значение")

    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Список параметров"
        unique_together = ("product", "parameter")

    def __str__(self):
        return f'{self.product}, {self.parameter}, {self.value}'


class Order(models.Model):
    STATE_CHOICES = (
        ('basket', 'Корзина'),
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('assembled', 'Собран'),
        ('sent', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменен'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь", related_name='orders'
    )
    contacts = models.ForeignKey(
        UserInfo, on_delete=models.CASCADE, verbose_name="Контакты пользователя", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Заказ создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время последнего изменения статуса")
    status = models.CharField(max_length=10, choices=STATE_CHOICES, verbose_name="Текущий статус")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Список заказов"
        ordering = ('-created_at',)

    def __str__(self):
        return f'Создан: {self.created_at}, статус: {self.status}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name="ordered_items", blank=True, verbose_name="Заказ")
    product = models.ForeignKey(ProductInfo, on_delete=models.CASCADE,
                                related_name="in_orders", blank=True, verbose_name="Продукт")
    quantity = models.PositiveIntegerField(verbose_name="Количество", default=1)

    class Meta:
        verbose_name = "Позиция в заказе"
        verbose_name_plural = "Позиции в заказе"
        unique_together = ("order", "product")

    def __str__(self):
        return f'{self.product} - {self.quantity}'
