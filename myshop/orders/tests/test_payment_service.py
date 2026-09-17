from decimal import Decimal

from django.test import TestCase, override_settings

from orders.models import Order, OrderItem, Payment
from orders.services import create_payment
from shop.models import Category, Product


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class CreatePaymentTestCase(TestCase):
    """Тесты функции create_payment(order) из orders.services."""

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Пицца', slug='pizza')
        cls.product = Product.objects.create(
            name='Пепперони',
            slug='pepperoni',
            category=cls.category,
            price=Decimal('150.00'),
            weight=500,
            description='Вкусная пицца',
            is_extra=False,
        )
        cls.order = Order.objects.create(
            first_name='Иван',
            last_name='Иванов',
            email='ivan@example.com',
            phone='+380991234567',
            paid=False,
        )
        OrderItem.objects.create(
            order=cls.order,
            product=cls.product,
            price=Decimal('150.00'),
            quantity=2,
        )

    def test_1_payment_created_in_db(self):
        """Payment создаётся в базе"""
        create_payment(self.order)
        self.assertEqual(Payment.objects.count(), 1, 'Должна быть создана одна запись Payment')

    def test_2_payment_order_matches(self):
        """payment.order == order"""
        payment = create_payment(self.order)
        self.assertEqual(payment.order, self.order, 'payment.order должен совпадать с order')

    def test_3_payment_provider_liqpay(self):
        """payment.provider == "liqpay" """
        payment = create_payment(self.order)
        self.assertEqual(payment.provider, 'liqpay', 'provider должен быть "liqpay"')

    def test_4_payment_amount_matches_total(self):
        """payment.amount == order.get_total_cost()"""
        payment = create_payment(self.order)
        self.assertEqual(
            payment.amount,
            self.order.get_total_cost(),
            'amount должен быть равен итоговой сумме заказа',
        )

    def test_5_payment_currency_uah(self):
        """payment.currency == "UAH" """
        payment = create_payment(self.order)
        self.assertEqual(payment.currency, 'UAH', 'currency должен быть "UAH"')

    def test_6_payment_status_pending(self):
        """payment.status == "pending" """
        payment = create_payment(self.order)
        self.assertEqual(payment.status, 'pending', 'status должен быть "pending"')

    def test_7_payment_transaction_id_empty(self):
        """payment.transaction_id остаётся пустым"""
        payment = create_payment(self.order)
        self.assertEqual(payment.transaction_id, '', 'transaction_id должен быть пустым')

    def test_8_order_paid_not_changed(self):
        """Order.paid не изменяется"""
        self.assertFalse(self.order.paid, 'Перед вызовом paid должен быть False')
        create_payment(self.order)
        fresh = Order.objects.get(pk=self.order.pk)
        self.assertFalse(fresh.paid, 'Функция не должна менять paid заказа')

    def test_9_order_data_not_changed(self):
        """Данные Order не изменяются"""
        before = Order.objects.get(pk=self.order.pk)
        create_payment(self.order)
        after = Order.objects.get(pk=self.order.pk)
        fields = ('first_name', 'last_name', 'email', 'phone', 'paid', 'created', 'updated')
        for field in fields:
            self.assertEqual(
                getattr(after, field),
                getattr(before, field),
                f'Поле {field} заказа не должно меняться',
            )

    def test_10_repeat_call_creates_new_payment(self):
        """Повторный вызов создаёт отдельную Payment-запись"""
        p1 = create_payment(self.order)
        p2 = create_payment(self.order)
        self.assertNotEqual(p1.id, p2.id, 'Должны быть созданы разные записи Payment')

    def test_11_payment_count_increments_by_one(self):
        """Количество Payment увеличивается на 1 после каждого вызова"""
        before = Payment.objects.count()
        create_payment(self.order)
        self.assertEqual(
            Payment.objects.count(),
            before + 1,
            'Количество Payment должно увеличиться ровно на 1',
        )
        create_payment(self.order)
        self.assertEqual(
            Payment.objects.count(),
            before + 2,
            'Второй вызов снова должен увеличить счётчик на 1',
        )

    def test_12_created_updated_set(self):
        """created и updated у Payment устанавливаются корректно"""
        from django.utils import timezone
        payment = create_payment(self.order)
        self.assertIsNotNone(payment.created, 'created должен быть установлен')
        self.assertIsNotNone(payment.updated, 'updated должен быть установлен')
        self.assertLessEqual(payment.created, timezone.now(), 'created не должен быть в будущем')
        self.assertLessEqual(payment.updated, timezone.now(), 'updated не должен быть в будущем')