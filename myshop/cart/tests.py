import pytest
from decimal import Decimal
from django.urls import reverse, resolve
from django.test import Client, RequestFactory
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpRequest

from cart.cart import Cart
from cart.forms import CartAddProductForm
from cart import views
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
def session(db):
    """Создание сессии для тестов"""
    session = SessionStore()
    session.create()
    return session

@pytest.fixture
def request_with_session(db, session):
    """RequestFactory с сессией"""
    factory = RequestFactory()
    request = factory.get('/')
    request.session = session
    return request


class TestCartClass:
    """Тесты для класса Cart"""

    def test_cart_initialization_empty(self, request_with_session):
        """Тест инициализации пустой корзины"""
        cart = Cart(request_with_session)
        assert cart.cart == {}

    def test_cart_initialization_existing_session(self, db, request_with_session, product):
        """Тест инициализации с существующей корзиной в сессии"""
        request_with_session.session['cart'] = {
            str(product.id): {'quantity': 2, 'price': '150.00'}
        }
        cart = Cart(request_with_session)
        assert str(product.id) in cart.cart
        assert cart.cart[str(product.id)]['quantity'] == 2

    def test_cart_add_new_product(self, request_with_session, product):
        """Тест добавления нового продукта в корзину"""
        cart = Cart(request_with_session)
        cart.add(product, quantity=1)
        assert str(product.id) in cart.cart
        assert cart.cart[str(product.id)]['quantity'] == 1
        assert cart.cart[str(product.id)]['price'] == '150.00'

    def test_cart_add_existing_product_increment(self, request_with_session, product):
        """Тест увеличения количества существующего продукта"""
        cart = Cart(request_with_session)
        cart.add(product, quantity=2)
        cart.add(product, quantity=3)
        assert cart.cart[str(product.id)]['quantity'] == 5

    def test_cart_add_with_override(self, request_with_session, product):
        """Тест добавления с заменой количества"""
        cart = Cart(request_with_session)
        cart.add(product, quantity=2)
        cart.add(product, quantity=5, override_quantity=True)
        assert cart.cart[str(product.id)]['quantity'] == 5

    def test_cart_add_multiple_products(self, request_with_session, product, product_extra):
        """Тест добавления нескольких продуктов"""
        cart = Cart(request_with_session)
        cart.add(product, quantity=1)
        cart.add(product_extra, quantity=2)
        assert len(cart.cart) == 2

    def test_cart_remove_existing(self, request_with_session, product):
        """Тест удаления продукта из корзины"""
        cart = Cart(request_with_session)
        cart.add(product, quantity=2)
        cart.remove(product)
        assert str(product.id) not in cart.cart

    def test_cart_remove_nonexistent(self, request_with_session, product):
        """Тест удаления несуществующего продукта (не должно вызывать ошибку)"""
        cart = Cart(request_with_session)
        cart.remove(product)
        assert str(product.id) not in cart.cart

    def test_cart_clear(self, request_with_session, product, product_extra):
        """Тест очистки корзины"""
        cart = Cart(request_with_session)
        cart.add(product, quantity=1)
        cart.add(product_extra, quantity=2)
        cart.clear()
        assert len(cart.cart) == 0

    def test_cart_len_empty(self, request_with_session):
        """Тест длины пустой корзины"""
        cart = Cart(request_with_session)
        assert len(cart) == 0

    def test_cart_len_with_items(self, request_with_session, product, product_extra):
        """Тест длины корзины с товарами"""
        cart = Cart(request_with_session)
        cart.add(product, quantity=2)
        cart.add(product_extra, quantity=3)
        assert len(cart) == 5

    def test_cart_get_total_price_empty(self, request_with_session):
        """Тест получения общей цены пустой корзины"""
        cart = Cart(request_with_session)
        assert cart.get_total_price() == Decimal('0')

    def test_cart_get_total_price_with_items(self, request_with_session, product, product_extra):
        """Тест получения общей цены корзины"""
        cart = Cart(request_with_session)
        cart.add(product, quantity=2)
        cart.add(product_extra, quantity=1)
        total = cart.get_total_price()
        assert total == Decimal('325.00')

    def test_cart_iteration(self, request_with_session, product):
        """Тест итерации по корзине"""
        cart = Cart(request_with_session)
        cart.add(product, quantity=2)
        items = list(cart)
        assert len(items) == 1
        assert items[0]['quantity'] == 2
        assert items[0]['price'] == Decimal('150.00')
        assert items[0]['total_price'] == Decimal('300.00')

    def test_cart_save(self, request_with_session, product):
        """Тест сохранения корзины в сессию"""
        cart = Cart(request_with_session)
        cart.add(product, quantity=1)
        assert request_with_session.session.modified is True

    def test_cart_session_persistence(self, db, request_with_session, product):
        """Тест персистентности корзины между запросами"""
        cart1 = Cart(request_with_session)
        cart1.add(product, quantity=1)

        session_key = request_with_session.session.session_key
        session = SessionStore(session_key=session_key)

        cart2 = Cart(request_with_session)
        cart2.session = session
        assert str(product.id) in cart2.cart


class TestCartAddProductForm:
    """Тесты для формы CartAddProductForm"""

    def test_form_valid_data(self):
        """Тест валидных данных формы"""
        form = CartAddProductForm(data={'quantity': '5', 'override': False})
        assert form.is_valid()
        assert form.cleaned_data['quantity'] == 5
        assert form.cleaned_data['override'] is False

    def test_form_valid_override_true(self):
        """Тест формы с override=True"""
        form = CartAddProductForm(data={'quantity': '10', 'override': True})
        assert form.is_valid()
        assert form.cleaned_data['override'] is True

    def test_form_invalid_quantity_zero(self):
        """Тест некорректного количества (0)"""
        form = CartAddProductForm(data={'quantity': '0', 'override': False})
        assert not form.is_valid()

    def test_form_invalid_quantity_negative(self):
        """Тест некорректного количества (отрицательное)"""
        form = CartAddProductForm(data={'quantity': '-1', 'override': False})
        assert not form.is_valid()

    def test_form_invalid_quantity_too_large(self):
        """Тест некорректного количества (больше 20)"""
        form = CartAddProductForm(data={'quantity': '25', 'override': False})
        assert not form.is_valid()

    def test_form_quantity_coerce_to_int(self):
        """Тест преобразования количества в int"""
        form = CartAddProductForm(data={'quantity': '7', 'override': False})
        assert form.is_valid()
        assert isinstance(form.cleaned_data['quantity'], int)
        assert form.cleaned_data['quantity'] == 7

    def test_form_override_required_false(self):
        """Тест что override не обязателен"""
        form = CartAddProductForm(data={'quantity': '1'})
        assert form.is_valid()
        assert form.cleaned_data['override'] is False

    def test_form_choices_range(self):
        """Тест диапазона выбора количества"""
        choices = CartAddProductForm().fields['quantity'].choices
        values = [c[0] for c in choices]
        assert min(values) == 1
        assert max(values) == 20

    def test_form_widget_attrs(self):
        """Тест атрибутов виджета"""
        form = CartAddProductForm()
        widget = form.fields['quantity'].widget
        assert 'class' in widget.attrs
        assert 'border' in widget.attrs['class']


class TestCartViews:
    """Тесты для views корзины"""

    @pytest.fixture
    def client(self):
        return Client()

    def test_cart_detail_view_200(self, client, db):
        """Тест страницы корзины - статус 200"""
        response = client.get(reverse('cart:cart_detail'))
        assert response.status_code == 200

    def test_cart_detail_view_template(self, client, db):
        """Тест использования правильного шаблона"""
        response = client.get(reverse('cart:cart_detail'))
        assert 'cart/detail.html' in [t.name for t in response.templates]

    def test_cart_detail_view_context(self, client, db):
        """Тест контекста страницы корзины"""
        response = client.get(reverse('cart:cart_detail'))
        assert 'cart' in response.context

    def test_cart_detail_view_empty_cart(self, client, db):
        """Тест пустой корзины"""
        response = client.get(reverse('cart:cart_detail'))
        cart = response.context['cart']
        assert len(cart) == 0

    def test_cart_add_view_post_only(self, client, product, db):
        """Тест что cart_add принимает только POST"""
        response = client.get(reverse('cart:cart_add', args=[product.id]))
        assert response.status_code == 405

    def test_cart_add_view_success(self, client, product, db):
        """Тест успешного добавления в корзину"""
        response = client.post(
            reverse('cart:cart_add', args=[product.id]),
            data={'quantity': '2', 'override': 'False'}
        )
        assert response.status_code == 302
        assert response.url == reverse('cart:cart_detail')

    def test_cart_add_view_invalid_product(self, client, db):
        """Тест добавления несуществующего продукта"""
        response = client.post(
            reverse('cart:cart_add', args=[99999]),
            data={'quantity': '1', 'override': 'False'}
        )
        assert response.status_code == 404

    def test_cart_add_view_invalid_quantity(self, client, product, db):
        """Тест добавления с некорректным количеством"""
        response = client.post(
            reverse('cart:cart_add', args=[product.id]),
            data={'quantity': '25', 'override': 'False'}
        )
        assert response.status_code == 200

    def test_cart_add_view_with_session(self, client, product, db):
        """Тест добавления в корзину с созданием сессии"""
        session = client.session
        session.save()

        response = client.post(
            reverse('cart:cart_add', args=[product.id]),
            data={'quantity': '1', 'override': 'False'}
        )
        assert response.status_code == 302

    def test_cart_remove_view_post_only(self, client, product, db):
        """Тест что cart_remove принимает только POST"""
        response = client.get(reverse('cart:cart_remove', args=[product.id]))
        assert response.status_code == 405

    def test_cart_remove_view_success(self, client, product, db):
        """Тест успешного удаления из корзины"""
        client.post(
            reverse('cart:cart_add', args=[product.id]),
            data={'quantity': '1', 'override': 'False'}
        )
        response = client.post(
            reverse('cart:cart_remove', args=[product.id])
        )
        assert response.status_code == 302
        assert response.url == reverse('cart:cart_detail')

    def test_cart_remove_nonexistent_product(self, client, db):
        """Тест удаления несуществующего продукта из корзины"""
        response = client.post(
            reverse('cart:cart_remove', args=[99999])
        )
        assert response.status_code == 404

    def test_cart_remove_not_in_cart(self, client, product, db):
        """Тест удаления продукта, которого нет в корзине"""
        response = client.post(
            reverse('cart:cart_remove', args=[product.id])
        )
        assert response.status_code == 302


class TestCartUrls:
    """Тесты для URL маршрутов корзины"""

    def test_cart_detail_url_resolve(self):
        """Тест резолва URL детальной корзины"""
        url = reverse('cart:cart_detail')
        assert url == '/cart/'
        match = resolve('/cart/')
        assert match.func == views.cart_detail
        assert match.app_name == 'cart'

    def test_cart_add_url_resolve(self):
        """Тест резолва URL добавления в корзину"""
        url = reverse('cart:cart_add', args=[1])
        assert url == '/cart/add/1/'
        match = resolve('/cart/add/1/')
        assert match.func == views.cart_add
        assert match.kwargs['product_id'] == 1

    def test_cart_remove_url_resolve(self):
        """Тест резолва URL удаления из корзины"""
        url = reverse('cart:cart_remove', args=[1])
        assert url == '/cart/remove/1/'
        match = resolve('/cart/remove/1/')
        assert match.func == views.cart_remove
        assert match.kwargs['product_id'] == 1


class TestCartContextProcessors:
    """Тесты для контекст-процессора корзины"""

    def test_cart_context_processor(self, client, db):
        """Тест контекст-процессора корзины"""
        response = client.get(reverse('shop:index'))
        assert 'cart' in response.context
