import datetime as dt

from django.db import models
from django.db.models import F, Q
from django.core.validators import MinValueValidator

from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=500,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQueryset(models.QuerySet):
    def cost(self):
        return self.annotate(
            order_cost=models.Sum(F('productsinorder__price') * F('productsinorder__quantity'))
        )


class Order(models.Model):
    NEW = '01'
    COOKING = '02'
    DELIVERY = '03'
    DONE = '04'
    ORDER_STATUS = [
        (NEW, 'Не обработан'),
        (COOKING, 'Готовится'),
        (DELIVERY, 'Доставка'),
        (DONE, 'Доставлен'),
    ]
    CASH ='CSH'
    CARD = 'CRD'
    PAYMENT_TYPE =  [
        (CASH, 'Наличными'),
        (CARD, 'Картой'),
    ]

    status = models.CharField(
        verbose_name='Статус',
        max_length=4,
        choices=ORDER_STATUS,
        default=NEW,
        db_index=True
    )
    payment_type = models.CharField(
        verbose_name='Способ оплаты',
        max_length=4,
        choices=PAYMENT_TYPE,
        default=CASH,
        db_index=True
    )
    datetime_registered = models.DateTimeField(
        verbose_name='Зарегестрирован',
        default=dt.datetime.now,
        db_index=True
    )
    datetime_called = models.DateTimeField(
        verbose_name='Созвон с клиентом',
        null=True,
        blank=True,
        db_index=True
    )
    datetime_delivered = models.DateTimeField(
        verbose_name='Доставлен',
        null=True,
        blank=True,
        db_index=True
    )
    products= models.ManyToManyField(
        Product,
        through='ProductsInOrder',
        null=False
    )
    firstname = models.CharField(
        verbose_name='Имя',
        max_length=30,
        db_index=True
    )
    lastname = models.CharField(
        verbose_name='Имя',
        max_length=30,
        db_index=True
    )
    phonenumber = PhoneNumberField(
        region='RU',
        verbose_name='Номер телефона'
    )
    address = models.CharField(
        verbose_name='Адрес доставки',
        max_length=200,
        db_index=True
    )
    comment = models.TextField(
        verbose_name='Комментарий к заказу',
        blank=True,
        default=''
    )
    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Ресторан',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    objects = OrderQueryset.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname} {self.phonenumber}'


class ProductsInOrder(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Товар'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
    )
    price = models.DecimalField (
        verbose_name='цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity = models.IntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'
