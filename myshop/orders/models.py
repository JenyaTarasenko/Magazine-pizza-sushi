
from django.db import models
from shop.models import Product

class Order(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    created = models.DateTimeField(auto_now_add=True,  verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    paid = models.BooleanField(default=False, verbose_name="Оплачено")

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


    def __str__(self):
        return f"Заказ №{self.id}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order,
                              related_name='items',
                              on_delete=models.CASCADE, verbose_name="Заказ")
    product = models.ForeignKey(Product,
                                related_name='order_items',
                                on_delete=models.CASCADE, verbose_name="Продукт")
    price = models.DecimalField(max_digits=10,
                                decimal_places=2, verbose_name="Цена")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity

#модель которая хранит платежи  из LiqPay
# Создана для того чтобы отслеживать статус платежа 
# Изначально была только в LiqPay но было принято решение создать универсальную модель для всех платежных систем

class Payment(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='payments',
        on_delete=models.PROTECT, verbose_name="Заказ"
    )

    provider = models.CharField(
        max_length=50,
        default='liqpay', verbose_name="Платежная система liqpay"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2, verbose_name="Сумма"
    )

    currency = models.CharField(
        max_length=3,
        default='UAH', verbose_name="Валюта"
    )

    status = models.CharField(
        max_length=50,
        default='pending', verbose_name="Статус"
    )

    transaction_id = models.CharField(
        max_length=255,
        blank=True, verbose_name="ID транзакции"
    )

    created = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания"
    )

    updated = models.DateTimeField(
        auto_now=True, verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return f'Payment {self.id} for Order {self.order_id}'