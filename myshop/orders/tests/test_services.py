import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.test import override_settings

from orders.models import Order, OrderItem
from shop.models import Category, Product


@pytest.fixture
def category(db):
    return Category.objects.create(name='Пицца', slug='pizza')

@pytest.fixture
def product(db, category):
    return Product.objects.create(
        name='Пепперони',
        slug='pepperoni',
        category=category,
        price=Decimal('150.00'),
        weight=500,
        description='Вкусная пицца',
        is_extra=False
    )

@pytest.fixture
def order(db):
    return Order.objects.create(
        first_name='Иван',
        last_name='Иванов',
        email='ivan@example.com',
        phone='+380991234567',
        paid=False
    )

@pytest.fixture
def order_with_items(db, order, product):
    OrderItem.objects.create(
        order=order,
        product=product,
        price=Decimal('150.00'),
        quantity=2
    )
    return order


class TestGetLiqpayContext:
    """Тесты для функции get_liqpay_context"""

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_returns_dict_with_data_and_signature(self, mock_settings, mock_liqpay, order):
        """Тест что функция возвращает словарь с data и signature"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay_instance.cnb_data.return_value = 'encoded_data'
        mock_liqpay_instance.cnb_signature.return_value = 'signature_value'
        mock_liqpay.return_value = mock_liqpay_instance

        result = get_liqpay_context(order)

        assert 'data' in result
        assert 'signature' in result
        assert result['data'] == 'encoded_data'
        assert result['signature'] == 'signature_value'

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_calls_liqpay_methods(self, mock_settings, mock_liqpay, order):
        """Тест вызова методов LiqPay"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order)

        mock_liqpay_instance.cnb_data.assert_called_once()
        mock_liqpay_instance.cnb_signature.assert_called_once()

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_cnb_data_receives_correct_params(self, mock_settings, mock_liqpay, order):
        """Тест что в cnb_data передаются правильные параметры"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        assert 'action' in call_args
        assert call_args['action'] == 'pay'
        assert 'amount' in call_args
        assert 'currency' in call_args
        assert 'order_id' in call_args

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_amount_uses_order_total_cost(self, mock_settings, mock_liqpay, order_with_items):
        """Тест что amount берется из get_total_cost"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order_with_items)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        expected_amount = str(order_with_items.get_total_cost())
        assert call_args['amount'] == expected_amount

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_currency_is_uah(self, mock_settings, mock_liqpay, order):
        """Тест что валюта - UAH"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        assert call_args['currency'] == 'UAH'

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_order_id_is_string(self, mock_settings, mock_liqpay, order):
        """Тест что order_id - строка"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        assert isinstance(call_args['order_id'], str)

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_description_contains_order_id(self, mock_settings, mock_liqpay, order):
        """Тест что description содержит номер заказа"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        assert str(order.id) in call_args['description']

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_sandbox_mode(self, mock_settings, mock_liqpay, order):
        """Тест что sandbox установлен"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        assert 'sandbox' in call_args

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_version_present(self, mock_settings, mock_liqpay, order):
        """Тест что version присутствует"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        assert 'version' in call_args


class TestGetLiqpayContextEdgeCases:
    """Граничные случаи для get_liqpay_context"""

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_empty_order_cost(self, mock_settings, mock_liqpay, order):
        """Тест заказа с нулевой стоимостью"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        result = get_liqpay_context(order)

        assert result is not None
        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        assert call_args['amount'] == '0'

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_decimal_amount(self, mock_settings, mock_liqpay, order_with_items):
        """Тест десятичной суммы"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order_with_items)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        amount = Decimal(call_args['amount'])
        assert amount == Decimal('300.00')

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_large_order_amount(self, mock_settings, mock_liqpay, db, product):
        """Тест заказа с большой суммой"""
        from orders.services import get_liqpay_context
        
        order = Order.objects.create(
            first_name='Тест',
            last_name='Тест',
            email='test@test.com',
            phone='+380000000000'
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('10000.00'),
            quantity=10
        )
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        assert Decimal(call_args['amount']) == Decimal('100000.00')


class TestGetLiqpayContextURLs:
    """Тесты URL в get_liqpay_context"""

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_server_url_present(self, mock_settings, mock_liqpay, order):
        """Тест наличия server_url"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        assert 'server_url' in call_args

    @patch('orders.services.LiqPay')
    @patch('orders.services.settings')
    def test_result_url_present(self, mock_settings, mock_liqpay, order):
        """Тест наличия result_url"""
        from orders.services import get_liqpay_context
        
        mock_settings.LIQPAY_PUBLIC_KEY = 'test_public'
        mock_settings.LIQPAY_PRIVATE_KEY = 'test_private'
        
        mock_liqpay_instance = MagicMock()
        mock_liqpay.return_value = mock_liqpay_instance

        get_liqpay_context(order)

        call_args = mock_liqpay_instance.cnb_data.call_args[0][0]
        assert 'result_url' in call_args
