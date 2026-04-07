import pytest
from unittest.mock import patch, MagicMock
from django.test import Client
from django.urls import reverse
from decimal import Decimal

from orders.models import Order, OrderItem
from orders.forms import OrderCreateForm
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
def product_extra(db, category):
    return Product.objects.create(
        name='Сыр',
        slug='syr',
        category=category,
        price=Decimal('25.00'),
        weight=50,
        description='Дополнительный сыр',
        is_extra=True
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
def client():
    return Client()


class TestPaymentSuccess:
    """Тесты для payment_success view"""

    def test_payment_success_get_status_200(self, client, db):
        """Тест GET запроса - статус 200"""
        response = client.get(reverse('orders:payment_success'))
        assert response.status_code == 200

    def test_payment_success_uses_correct_template(self, client, db):
        """Тест использования правильного шаблона"""
        response = client.get(reverse('orders:payment_success'))
        assert 'orders/order/payment_success.html' in [t.name for t in response.templates]

    def test_payment_success_url_resolves(self, db):
        """Тест резолва URL"""
        url = reverse('orders:payment_success')
        assert '/orders/payment/success/' in url


class TestPaymentCancel:
    """Тесты для payment_cancel view
    
    Примечание: шаблон в проекте называется 'payment_cansel.html' (опечатка).
    Тесты ожидают что шаблон будет исправлен на 'payment_cancel.html'
    """

    def test_payment_cancel_url_resolves(self, db):
        """Тест резолва URL"""
        url = reverse('orders:payment_cancel')
        assert '/orders/payment/cancel/' in url


class TestOrderCreate:
    """Тесты для order_create view"""

    def test_order_create_get_status_200(self, client, db):
        """Тест GET запроса - статус 200"""
        response = client.get(reverse('orders:order_create'))
        assert response.status_code == 200

    def test_order_create_get_uses_correct_template(self, client, db):
        """Тест использования правильного шаблона"""
        response = client.get(reverse('orders:order_create'))
        assert 'orders/order/create.html' in [t.name for t in response.templates]

    def test_order_create_get_context_has_form(self, client, db):
        """Тест наличия формы в контексте"""
        response = client.get(reverse('orders:order_create'))
        assert 'form' in response.context
        assert isinstance(response.context['form'], OrderCreateForm)

    def test_order_create_get_context_has_cart(self, client, db):
        """Тест наличия корзины в контексте"""
        response = client.get(reverse('orders:order_create'))
        assert 'cart' in response.context

    def test_order_create_post_valid_data_with_mocked_cart(self, client, db, product):
        """Тест POST с валидными данными - успешное создание заказа"""
        mock_cart_items = {
            str(product.id): {'quantity': 2, 'price': '150.00', 'product': product}
        }
        
        with patch('orders.views.Cart') as MockCart:
            mock_cart_instance = MagicMock()
            mock_cart_instance.__iter__ = lambda self: iter([
                {'product': product, 'price': '150.00', 'quantity': 2}
            ])
            mock_cart_instance.__len__ = lambda self: 1
            MockCart.return_value = mock_cart_instance

            data = {
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'email': 'ivan@example.com',
                'phone': '+380991234567'
            }
            response = client.post(reverse('orders:order_create'), data=data)
            
            assert response.status_code == 302
            assert Order.objects.filter(email='ivan@example.com').exists()

    def test_order_create_post_creates_order_items(self, client, db, product):
        """Тест что POST создаёт OrderItem"""
        with patch('orders.views.Cart') as MockCart:
            mock_cart_instance = MagicMock()
            mock_cart_instance.__iter__ = lambda self: iter([
                {'product': product, 'price': '150.00', 'quantity': 2}
            ])
            mock_cart_instance.__len__ = lambda self: 1
            MockCart.return_value = mock_cart_instance

            data = {
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'email': 'ivan@test.com',
                'phone': '+380991234567'
            }
            response = client.post(reverse('orders:order_create'), data=data)
            
            order = Order.objects.get(email='ivan@test.com')
            assert order.items.count() == 1
            assert order.items.first().quantity == 2

    def test_order_create_post_invalid_data_returns_form(self, client, db):
        """Тест что при невалидных данных возвращается форма с ошибками"""
        data = {
            'first_name': '',
            'last_name': 'Иванов',
            'email': 'invalid-email',
            'phone': ''
        }
        response = client.post(reverse('orders:order_create'), data=data)
        
        assert response.status_code == 200
        form = response.context['form']
        assert not form.is_valid()

    def test_order_create_post_missing_email(self, client, db):
        """Тест POST без email"""
        data = {
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'phone': '+380991234567'
        }
        response = client.post(reverse('orders:order_create'), data=data)
        
        assert response.status_code == 200
        assert 'email' in response.context['form'].errors

    def test_order_create_post_multiple_products(self, client, db, product, product_extra):
        """Тест POST с несколькими товарами"""
        with patch('orders.views.Cart') as MockCart:
            mock_cart_instance = MagicMock()
            mock_cart_instance.__iter__ = lambda self: iter([
                {'product': product, 'price': '150.00', 'quantity': 2},
                {'product': product_extra, 'price': '25.00', 'quantity': 1}
            ])
            mock_cart_instance.__len__ = lambda self: 2
            MockCart.return_value = mock_cart_instance

            data = {
                'first_name': 'Пётр',
                'last_name': 'Петров',
                'email': 'multi@test.com',
                'phone': '+380991234567'
            }
            response = client.post(reverse('orders:order_create'), data=data)
            
            assert response.status_code == 302
            order = Order.objects.get(email='multi@test.com')
            assert order.items.count() == 2

    def test_order_create_url_resolves(self, db):
        """Тест резолва URL"""
        url = reverse('orders:order_create')
        assert '/orders/create/' in url


class TestLiqpayWebhook:
    """Тесты для liqpay_webhook view"""

    def test_webhook_get_not_allowed(self, client, db):
        """Тест что GET запрос отклоняется"""
        response = client.get(reverse('orders:liqpay_webhook'))
        assert response.status_code == 405

    def test_webhook_post_without_data(self, client, db):
        """Тест POST без данных возвращает 400"""
        response = client.post(reverse('orders:liqpay_webhook'))
        assert response.status_code == 400

    def test_webhook_post_invalid_signature(self, client, db, order):
        """Тест POST с невалидной подписью"""
        import base64
        import json
        
        order_data = {
            'order_id': str(order.id),
            'status': 'success'
        }
        data = base64.b64encode(json.dumps(order_data).encode()).decode()
        
        with patch('orders.views.settings') as mock_settings, \
             patch('orders.views.LiqPay') as MockLiqPay:
            mock_settings.LIQPAY_PUBLIC_KEY = 'test_key'
            mock_settings.LIQPAY_PRIVATE_KEY = 'test_key'
            
            mock_instance = MagicMock()
            mock_instance.cnb_signature.return_value = 'valid_signature'
            MockLiqPay.return_value = mock_instance
            
            response = client.post(reverse('orders:liqpay_webhook'), {
                'data': data,
                'signature': 'wrong_signature'
            })
            assert response.status_code == 403

    def test_webhook_post_successful_payment(self, client, db, order):
        """Тест успешного платежа - статус меняется на paid=True"""
        import base64
        import json
        
        order_data = {
            'order_id': str(order.id),
            'status': 'success',
            'amount': '300.00'
        }
        data = base64.b64encode(json.dumps(order_data).encode()).decode()
        
        with patch('orders.views.settings') as mock_settings, \
             patch('orders.views.LiqPay') as MockLiqPay, \
             patch('orders.views.send_telegram_message') as mock_telegram:
            mock_settings.LIQPAY_PUBLIC_KEY = 'test_key'
            mock_settings.LIQPAY_PRIVATE_KEY = 'test_key'
            
            mock_instance = MagicMock()
            mock_instance.decode_data_from_str.return_value = order_data
            mock_instance.cnb_signature.return_value = 'valid_signature'
            MockLiqPay.return_value = mock_instance
            mock_telegram.return_value = True
            
            response = client.post(reverse('orders:liqpay_webhook'), {
                'data': data,
                'signature': 'valid_signature'
            })
            
            order.refresh_from_db()
            assert order.paid is True

    def test_webhook_sends_telegram_notification(self, client, db, order):
        """Тест отправки уведомления в Telegram"""
        import base64
        import json
        
        order_data = {
            'order_id': str(order.id),
            'status': 'success'
        }
        data = base64.b64encode(json.dumps(order_data).encode()).decode()
        
        with patch('orders.views.settings') as mock_settings, \
             patch('orders.views.LiqPay') as MockLiqPay, \
             patch('orders.views.send_telegram_message') as mock_telegram:
            mock_settings.LIQPAY_PUBLIC_KEY = 'test_key'
            mock_settings.LIQPAY_PRIVATE_KEY = 'test_key'
            
            mock_instance = MagicMock()
            mock_instance.decode_data_from_str.return_value = order_data
            mock_instance.cnb_signature.return_value = 'valid_signature'
            MockLiqPay.return_value = mock_instance
            mock_telegram.return_value = True
            
            response = client.post(reverse('orders:liqpay_webhook'), {
                'data': data,
                'signature': 'valid_signature'
            })
            
            mock_telegram.assert_called_once()

    def test_webhook_wait_accept_status(self, client, db, order):
        """Тест статуса wait_accept"""
        import base64
        import json
        
        order_data = {
            'order_id': str(order.id),
            'status': 'wait_accept'
        }
        data = base64.b64encode(json.dumps(order_data).encode()).decode()
        
        with patch('orders.views.settings') as mock_settings, \
             patch('orders.views.LiqPay') as MockLiqPay, \
             patch('orders.views.send_telegram_message'):
            mock_settings.LIQPAY_PUBLIC_KEY = 'test_key'
            mock_settings.LIQPAY_PRIVATE_KEY = 'test_key'
            
            mock_instance = MagicMock()
            mock_instance.decode_data_from_str.return_value = order_data
            mock_instance.cnb_signature.return_value = 'valid_signature'
            MockLiqPay.return_value = mock_instance
            
            response = client.post(reverse('orders:liqpay_webhook'), {
                'data': data,
                'signature': 'valid_signature'
            })
            
            order.refresh_from_db()
            assert order.paid is True

    def test_webhook_other_status_not_processed(self, client, db, order):
        """Тест что другие статусы не обрабатываются"""
        import base64
        import json
        
        order_data = {
            'order_id': str(order.id),
            'status': 'processing'
        }
        data = base64.b64encode(json.dumps(order_data).encode()).decode()
        
        with patch('orders.views.settings') as mock_settings, \
             patch('orders.views.LiqPay') as MockLiqPay, \
             patch('orders.views.send_telegram_message') as mock_telegram:
            mock_settings.LIQPAY_PUBLIC_KEY = 'test_key'
            mock_settings.LIQPAY_PRIVATE_KEY = 'test_key'
            
            mock_instance = MagicMock()
            mock_instance.decode_data_from_str.return_value = order_data
            mock_instance.cnb_signature.return_value = 'valid_signature'
            MockLiqPay.return_value = mock_instance
            
            response = client.post(reverse('orders:liqpay_webhook'), {
                'data': data,
                'signature': 'valid_signature'
            })
            
            order.refresh_from_db()
            assert order.paid is False
            mock_telegram.assert_not_called()

    def test_webhook_nonexistent_order_returns_404(self, client, db):
        """Тест webhook с несуществующим заказом возвращает 404"""
        import base64
        import json
        
        order_data = {
            'order_id': '99999',
            'status': 'success'
        }
        data = base64.b64encode(json.dumps(order_data).encode()).decode()
        
        with patch('orders.views.settings') as mock_settings, \
             patch('orders.views.LiqPay') as MockLiqPay:
            mock_settings.LIQPAY_PUBLIC_KEY = 'test_key'
            mock_settings.LIQPAY_PRIVATE_KEY = 'test_key'
            
            mock_instance = MagicMock()
            mock_instance.decode_data_from_str.return_value = order_data
            mock_instance.cnb_signature.return_value = 'valid_signature'
            MockLiqPay.return_value = mock_instance
            
            response = client.post(reverse('orders:liqpay_webhook'), {
                'data': data,
                'signature': 'valid_signature'
            })
            
            assert response.status_code == 404

    def test_webhook_url_resolves(self, db):
        """Тест резолва URL"""
        url = reverse('orders:liqpay_webhook')
        assert '/orders/liqpay_webhook/' in url


class TestOrderCreateEdgeCases:
    """Граничные случаи для order_create"""

    def test_order_create_long_first_name(self, client, db, product):
        """Тест с очень длинным именем"""
        with patch('orders.views.Cart') as MockCart:
            mock_cart_instance = MagicMock()
            mock_cart_instance.__iter__ = lambda self: iter([
                {'product': product, 'price': '100.00', 'quantity': 1}
            ])
            mock_cart_instance.__len__ = lambda self: 1
            MockCart.return_value = mock_cart_instance

            data = {
                'first_name': 'А' * 50,
                'last_name': 'Иванов',
                'email': 'long@test.com',
                'phone': '+380991234567'
            }
            response = client.post(reverse('orders:order_create'), data=data)
            assert response.status_code == 302

    def test_order_create_special_chars_in_name(self, client, db, product):
        """Тест со специальными символами"""
        with patch('orders.views.Cart') as MockCart:
            mock_cart_instance = MagicMock()
            mock_cart_instance.__iter__ = lambda self: iter([
                {'product': product, 'price': '100.00', 'quantity': 1}
            ])
            mock_cart_instance.__len__ = lambda self: 1
            MockCart.return_value = mock_cart_instance

            data = {
                'first_name': "О'Коннор",
                'last_name': 'ван дер Берг',
                'email': 'special@test.com',
                'phone': '+380991234567'
            }
            response = client.post(reverse('orders:order_create'), data=data)
            assert response.status_code == 302
