import base64
import hashlib
import json
from decimal import Decimal

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from orders.models import Order, OrderItem, Payment
from orders.services import get_liqpay_context
from shop.models import Category, Product

PUBLIC_KEY = 'test_public_key'
PRIVATE_KEY = 'test_private_key'
SITE_BASE = 'https://sushipizza.pythonanywhere.com'

EXPECTED_SERVER_URL = SITE_BASE + reverse('orders:liqpay_webhook')
EXPECTED_RESULT_URL = SITE_BASE + reverse('orders:payment_success')


def decode_data(data: str) -> dict:
    """Декодирует data из base64 в словарь."""
    return json.loads(base64.b64decode(data).decode('utf-8'))


def manual_signature(private_key: str, data: str) -> str:
    """Считает подпись LiqPay вручную: base64(sha1(private + data + private))."""
    return base64.b64encode(
        hashlib.sha1(
            (private_key + data + private_key).encode('utf-8')
        ).digest()
    ).decode('utf-8')


@override_settings(
    LIQPAY_PUBLIC_KEY=PUBLIC_KEY,
    LIQPAY_PRIVATE_KEY=PRIVATE_KEY,
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class BaseLiqpayContextTestCase(TestCase):
    """Базовая подготовка данных для тестов get_liqpay_context."""

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
        cls.extra = Product.objects.create(
            name='Сыр',
            slug='syr',
            category=cls.category,
            price=Decimal('25.00'),
            weight=50,
            description='Дополнительный сыр',
            is_extra=True,
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
        OrderItem.objects.create(
            order=cls.order,
            product=cls.extra,
            price=Decimal('25.00'),
            quantity=3,
        )


class TestGetLiqpayContextStructure(BaseLiqpayContextTestCase):
    """1. Структура возвращаемого словаря."""

    def test_returns_dict_with_data_and_signature(self):
        result = get_liqpay_context(self.order)
        self.assertIsInstance(result, dict, 'Функция должна возвращать словарь')
        self.assertIn('data', result, 'Словарь должен содержать ключ data')
        self.assertIn('signature', result, 'Словарь должен содержать ключ signature')

    def test_data_is_non_empty_base64_string(self):
        result = get_liqpay_context(self.order)
        data = result['data']
        self.assertIsInstance(data, str, 'data должна быть строкой')
        self.assertTrue(data, 'data не должна быть пустой')
        decoded = base64.b64decode(data)
        self.assertIsInstance(decoded, bytes, 'data должна декодироваться из base64')

    def test_signature_is_non_empty_base64_of_sha1(self):
        result = get_liqpay_context(self.order)
        signature = result['signature']
        self.assertIsInstance(signature, str, 'signature должна быть строкой')
        self.assertTrue(signature, 'signature не должна быть пустой')
        digest = base64.b64decode(signature)
        self.assertEqual(len(digest), 20, 'SHA-1 дайджест занимает ровно 20 байт')


class TestGetLiqpayContextDataContent(BaseLiqpayContextTestCase):
    """2. Декодирование и валидация содержимого data."""

    def test_data_decodes_to_json(self):
        result = get_liqpay_context(self.order)
        decoded = decode_data(result['data'])
        self.assertIsInstance(decoded, dict, 'data должна декодироваться в JSON-объект')

    def test_data_contains_public_key(self):
        decoded = decode_data(get_liqpay_context(self.order)['data'])
        self.assertEqual(
            decoded.get('public_key'),
            PUBLIC_KEY,
            'В data должен быть добавлен public_key из настроек',
        )

    def test_order_id_matches_order(self):
        decoded = decode_data(get_liqpay_context(self.order)['data'])
        self.assertEqual(
            str(decoded.get('order_id')),
            str(self.order.id),
            'order_id в data должен совпадать с Order.id',
        )

    def test_amount_matches_order_total(self):
        decoded = decode_data(get_liqpay_context(self.order)['data'])
        expected = str(self.order.get_total_cost())
        self.assertEqual(
            str(decoded.get('amount')),
            expected,
            f'amount должен быть равен итоговой сумме заказа ({expected})',
        )

    def test_currency_is_uah(self):
        decoded = decode_data(get_liqpay_context(self.order)['data'])
        self.assertEqual(decoded.get('currency'), 'UAH', 'Валюта должна быть UAH')

    def test_action_is_pay(self):
        decoded = decode_data(get_liqpay_context(self.order)['data'])
        self.assertEqual(decoded.get('action'), 'pay', 'action должно быть pay')

    def test_version_is_3(self):
        decoded = decode_data(get_liqpay_context(self.order)['data'])
        self.assertIn(
            decoded.get('version'),
            ('3', 3),
            'version должен быть "3" или 3',
        )

    def test_sandbox_is_1(self):
        decoded = decode_data(get_liqpay_context(self.order)['data'])
        self.assertIn(
            decoded.get('sandbox'),
            (1, '1'),
            'sandbox должен быть 1 или "1"',
        )

    def test_server_url_matches_expected(self):
        decoded = decode_data(get_liqpay_context(self.order)['data'])
        self.assertEqual(
            decoded.get('server_url'),
            EXPECTED_SERVER_URL,
            'server_url должен соответствовать webhook-адресу LiqPay',
        )

    def test_result_url_matches_expected(self):
        decoded = decode_data(get_liqpay_context(self.order)['data'])
        self.assertEqual(
            decoded.get('result_url'),
            EXPECTED_RESULT_URL,
            'result_url должен соответствовать адресу успешной оплаты',
        )


class TestGetLiqpayContextSignature(BaseLiqpayContextTestCase):
    """3. Валидация подписи signature."""

    def test_signature_matches_manual_formula(self):
        result = get_liqpay_context(self.order)
        data = result['data']
        expected = manual_signature(PRIVATE_KEY, data)
        self.assertEqual(
            result['signature'],
            expected,
            'signature должна быть равна base64(sha1(private_key + data + private_key))',
        )

    def test_signature_tied_to_private_key(self):
        context = get_liqpay_context(self.order)
        wrong = manual_signature('wrong_private_key', context['data'])
        self.assertNotEqual(
            context['signature'],
            wrong,
            'Подпись с другим private_key не должна совпадать',
        )

    def test_context_matches_recomputed_values(self):
        context = get_liqpay_context(self.order)
        recomputed = get_liqpay_context(self.order)
        self.assertEqual(
            context,
            recomputed,
            'Повторный вызов должен дать идентичные data и signature',
        )


class TestGetLiqpayContextSideEffects(BaseLiqpayContextTestCase):
    """4. Побочные эффекты вызова функции."""

    def test_order_not_modified_in_db(self):
        before = Order.objects.get(pk=self.order.pk)
        get_liqpay_context(self.order)
        after = Order.objects.get(pk=self.order.pk)

        fields = ('first_name', 'last_name', 'email', 'phone', 'paid', 'created', 'updated')
        for field in fields:
            self.assertEqual(
                getattr(after, field),
                getattr(before, field),
                f'Поле {field} заказа не должно меняться при вызове функции',
            )

    def test_no_payment_records_created(self):
        self.assertEqual(Payment.objects.count(), 0, 'До вызова не должно быть платежей')
        get_liqpay_context(self.order)
        self.assertEqual(
            Payment.objects.count(),
            0,
            'Функция не должна создавать записи Payment',
        )

    def test_order_paid_status_unchanged(self):
        self.order.paid = False
        self.order.save()
        get_liqpay_context(self.order)
        fresh = Order.objects.get(pk=self.order.pk)
        self.assertFalse(
            fresh.paid,
            'Функция не должна менять статус paid заказа',
        )