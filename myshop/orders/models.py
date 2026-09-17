
from django.db import models
from shop.models import Product

class Order(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order,
                              related_name='items',
                              on_delete=models.CASCADE)
    product = models.ForeignKey(Product,
                                related_name='order_items',
                                on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10,
                                decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

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
        on_delete=models.PROTECT,
    )

    provider = models.CharField(
        max_length=50,
        default='liqpay',
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    currency = models.CharField(
        max_length=3,
        default='UAH',
    )

    status = models.CharField(
        max_length=50,
        default='pending',
    )

    transaction_id = models.CharField(
        max_length=255,
        blank=True,
    )

    created = models.DateTimeField(
        auto_now_add=True,
    )

    updated = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f'Payment {self.id} for Order {self.order_id}'