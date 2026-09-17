from decimal import Decimal

from django.conf import settings
from django.test import TestCase, override_settings

from orders.liqpay import LiqPay
from orders.models import Order, OrderItem, Payment
from orders.services import create_payment, get_liqpay_context
from shop.models import Category, Product

PUBLIC_KEY = 'flow_test_public_key'
PRIVATE_KEY = 'flow_test_private_key'


@override_settings(
    LIQPAY_PUBLIC_KEY=PUBLIC_KEY,
    LIQPAY_PRIVATE_KEY=PRIVATE_KEY,
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class OrderPaymentFlowTestCase(TestCase):
    """Полный сервисный сценарий: заказ -> create_payment -> get_liqpay_context."""

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

    def decode(self, data):
        return LiqPay('', '').decode_data_from_str(data)

    def test_01_create_payment_creates_record(self):
        """create_payment создаёт Payment в базе"""
        create_payment(self.order)
        self.assertEqual(Payment.objects.count(), 1, 'Должна появиться одна запись Payment')

    def test_02_payment_linked_to_order(self):
        """Payment связан именно с нужным Order"""
        payment = create_payment(self.order)
        self.assertEqual(payment.order, self.order, 'Payment должен быть связан с Order')

    def test_03_payment_provider_is_liqpay(self):
        """Payment.provider == "liqpay" """
        payment = create_payment(self.order)
        self.assertEqual(payment.provider, 'liqpay', 'provider должен быть "liqpay"')

    def test_04_payment_amount_matches_order_total(self):
        """Payment.amount == order.get_total_cost()"""
        payment = create_payment(self.order)
        self.assertEqual(
            payment.amount,
            self.order.get_total_cost(),
            'amount должен равняться итоговой сумме заказа',
        )

    def test_05_payment_defaults_currency_status_transaction(self):
        """currency == "UAH", status == "pending", transaction_id пуст"""
        payment = create_payment(self.order)
        self.assertEqual(payment.currency, 'UAH', 'currency должен быть "UAH"')
        self.assertEqual(payment.status, 'pending', 'status должен быть "pending"')
        self.assertEqual(payment.transaction_id, '', 'transaction_id должен быть пустым')

    def test_06_order_paid_stays_false(self):
        """Order.paid остаётся False"""
        create_payment(self.order)
        get_liqpay_context(self.order)
        fresh = Order.objects.get(pk=self.order.pk)
        self.assertFalse(fresh.paid, 'paid должен остаться False после вызова сервисов')

    def test_07_order_data_not_changed(self):
        """Данные Order после вызова сервисов не изменяются"""
        before = Order.objects.get(pk=self.order.pk)
        create_payment(self.order)
        get_liqpay_context(self.order)
        after = Order.objects.get(pk=self.order.pk)
        fields = ('first_name', 'last_name', 'email', 'phone', 'paid', 'created', 'updated')
        for field in fields:
            self.assertEqual(
                getattr(after, field),
                getattr(before, field),
                f'Поле {field} заказа не должно меняться',
            )

    def test_08_context_is_dict_with_data_and_signature(self):
        """get_liqpay_context возвращает словарь с ключами data и signature"""
        context = get_liqpay_context(self.order)
        self.assertIsInstance(context, dict, 'Результат должен быть словарём')
        self.assertIn('data', context, 'Должен быть ключ data')
        self.assertIn('signature', context, 'Должен быть ключ signature')

    def test_09_data_decodes_via_liqpay(self):
        """data декодируется через существующий decode_data_from_str"""
        context = get_liqpay_context(self.order)
        decoded = self.decode(context['data'])
        self.assertIsInstance(decoded, dict, 'data должна декодироваться в словарь')

    def test_10_decoded_order_id_matches(self):
        """order_id после декодирования соответствует созданному Order"""
        context = get_liqpay_context(self.order)
        decoded = self.decode(context['data'])
        self.assertEqual(
            str(decoded['order_id']),
            str(self.order.id),
            'order_id в data должен соответствовать Order.id',
        )

    def test_11_decoded_amount_and_currency(self):
        """amount и currency в data соответствуют заказу"""
        context = get_liqpay_context(self.order)
        decoded = self.decode(context['data'])
        self.assertEqual(
            str(decoded['amount']),
            str(self.order.get_total_cost()),
            'amount в data должен равняться итоговой сумме заказа',
        )
        self.assertEqual(decoded['currency'], 'UAH', 'currency в data должен быть "UAH"')

    def test_12_signature_non_empty_and_payments_accumulate(self):
        """signature непустая; повторный вызов create_payment создаёт новую запись"""
        context = get_liqpay_context(self.order)
        self.assertIsInstance(context['signature'], str, 'signature должна быть строкой')
        self.assertTrue(context['signature'], 'signature не должна быть пустой')

        p1 = create_payment(self.order)
        p2 = create_payment(self.order)
        self.assertNotEqual(p1.id, p2.id, 'Повторный вызов должен создавать новую запись')
        self.assertEqual(Payment.objects.count(), 2, 'Должно быть две записи Payment')