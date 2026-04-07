import pytest
from decimal import Decimal
from django.test import Client, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

from orders.models import Order, OrderItem
from orders.forms import OrderCreateForm
from orders.liqpay import LiqPay
from shop.models import Category, Product


@pytest.fixture
def category(db):
    return Category.objects.create(
        name='Пицца',
        slug='pizza'
    )

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
def paid_order(db):
    return Order.objects.create(
        first_name='Пётр',
        last_name='Петров',
        email='petr@example.com',
        phone='+380991234568',
        paid=True
    )

@pytest.fixture
def order_with_items(db, order, product, product_extra):
    OrderItem.objects.create(
        order=order,
        product=product,
        price=Decimal('150.00'),
        quantity=2
    )
    OrderItem.objects.create(
        order=order,
        product=product_extra,
        price=Decimal('25.00'),
        quantity=3
    )
    return order

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def request_factory():
    return RequestFactory()

@pytest.fixture
def liqpay():
    return LiqPay(
        public_key='test_public_key',
        private_key='test_private_key'
    )

@pytest.fixture
def valid_order_data():
    return {
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'email': 'ivan@example.com',
        'phone': '+380991234567'
    }
