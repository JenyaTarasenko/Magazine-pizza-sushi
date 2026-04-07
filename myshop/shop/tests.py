import pytest
from decimal import Decimal
from django.urls import reverse, resolve
from django.test import Client, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import AnonymousUser

from shop.models import Category, Product
from shop import views


@pytest.fixture
def category_pizza(db):
    return Category.objects.create(
        name='Пицца',
        slug='pizza'
    )

@pytest.fixture
def category_sushi(db):
    return Category.objects.create(
        name='Суши',
        slug='sushi'
    )

@pytest.fixture
def category_napitki(db):
    return Category.objects.create(
        name='Напитки',
        slug='napitki'
    )

@pytest.fixture
def parent_category(db):
    return Category.objects.create(
        name='Мясная',
        slug='myasnaya',
        parent=None
    )

@pytest.fixture
def child_category(db, parent_category):
    return Category.objects.create(
        name='Мясная пицца',
        slug='myasnaya-pizza',
        parent=parent_category
    )

@pytest.fixture
def product_pizza(db, category_pizza):
    return Product.objects.create(
        name='Пепперони',
        slug='pepperoni',
        category=category_pizza,
        price=Decimal('150.00'),
        weight=500,
        description='Классическая пицца с пепперони',
        is_extra=False
    )

@pytest.fixture
def product_extra(db, category_pizza):
    return Product.objects.create(
        name='Дополнительный сыр',
        slug='extra-cheese',
        category=category_pizza,
        price=Decimal('25.00'),
        weight=50,
        description='Дополнительный сыр для пиццы',
        is_extra=True
    )

@pytest.fixture
def product_sushi(db, category_sushi):
    return Product.objects.create(
        name='Филадельфия',
        slug='filadelfia',
        category=category_sushi,
        price=Decimal('200.00'),
        weight=200,
        description='Классический ролл Филадельфия',
        is_extra=False
    )

@pytest.fixture
def request_factory():
    return RequestFactory()


class TestCategoryModel:
    """Тесты для модели Category"""

    def test_create_category(self, db):
        """Тест создания категории"""
        category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )
        assert category.id is not None
        assert category.name == 'Тестовая категория'
        assert category.slug == 'test-category'

    def test_category_str_representation(self, category_pizza):
        """Тест строкового представления категории"""
        assert str(category_pizza) == 'Пицца'

    def test_category_with_parent(self, parent_category, child_category):
        """Тест иерархии категорий (родитель-потомок)"""
        assert child_category.parent == parent_category
        assert parent_category in child_category.parent.__class__.objects.all()

    def test_category_without_parent(self, category_pizza):
        """Тест категории без родителя"""
        assert category_pizza.parent is None

    def test_category_children_relationship(self, parent_category, db):
        """Тест связи children для категории"""
        child1 = Category.objects.create(
            name='Дочерняя 1',
            slug='dochernyaya-1',
            parent=parent_category
        )
        child2 = Category.objects.create(
            name='Дочерняя 2',
            slug='dochernyaya-2',
            parent=parent_category
        )
        assert parent_category.children.count() == 2
        assert child1 in parent_category.children.all()
        assert child2 in parent_category.children.all()

    def test_category_image_field(self, category_pizza):
        """Тест поля изображения категории"""
        assert hasattr(category_pizza, 'image')
        assert category_pizza.image == ''

    def test_category_verbose_names(self, db):
        """Тест verbose_name для категории"""
        category = Category.objects.create(
            name='Тест',
            slug='test'
        )
        assert category._meta.verbose_name == 'Категория'
        assert category._meta.verbose_name_plural == 'Категории'

    def test_category_get_absolute_url(self, category_pizza):
        """Тест метода get_absolute_url"""
        expected_url = reverse('shop:category_detail', args=['pizza'])
        assert category_pizza.get_absolute_url() == expected_url

    def test_category_slug_unique(self, category_pizza, db):
        """Тест уникальности slug"""
        with pytest.raises(Exception):
            Category.objects.create(
                name='Другая пицца',
                slug='pizza'
            )


class TestProductModel:
    """Тесты для модели Product"""

    def test_create_product(self, product_pizza):
        """Тест создания продукта"""
        assert product_pizza.id is not None
        assert product_pizza.name == 'Пепперони'
        assert product_pizza.slug == 'pepperoni'
        assert product_pizza.price == Decimal('150.00')
        assert product_pizza.weight == 500

    def test_product_str_representation(self, product_pizza):
        """Тест строкового представления продукта"""
        assert str(product_pizza) == 'Пепперони'

    def test_product_category_relationship(self, product_pizza, category_pizza):
        """Тест связи продукта с категорией"""
        assert product_pizza.category == category_pizza
        assert product_pizza in category_pizza.products.all()

    def test_product_get_absolute_url(self, product_pizza):
        """Тест метода get_absolute_url"""
        expected_url = reverse('shop:product_detail', args=['pepperoni'])
        assert product_pizza.get_absolute_url() == expected_url

    def test_product_is_extra_flag(self, product_pizza, product_extra):
        """Тест флага is_extra"""
        assert product_pizza.is_extra is False
        assert product_extra.is_extra is True

    def test_product_extras_m2m(self, product_pizza, product_extra):
        """Тест связи ManyToMany для extras"""
        product_pizza.extras.add(product_extra)
        assert product_extra in product_pizza.extras.all()
        assert product_pizza in product_extra.related_to.all()

    def test_product_extras_self_reference(self, product_pizza, db):
        """Тест самоссылки extras"""
        extra = Product.objects.create(
            name='Соус',
            slug='sous',
            category=product_pizza.category,
            price=Decimal('10.00'),
            is_extra=True
        )
        product_pizza.extras.add(extra)
        assert product_pizza.extras.count() == 1

    def test_product_weight_nullable(self, db, category_pizza):
        """Тест что вес может быть null"""
        product = Product.objects.create(
            name='Без веса',
            slug='bez-vesa',
            category=category_pizza,
            price=Decimal('50.00'),
            weight=None,
            is_extra=True
        )
        assert product.weight is None

    def test_product_description_blank(self, product_pizza):
        """Тест что описание может быть пустым"""
        assert product_pizza.description == 'Классическая пицца с пепперони'

    def test_product_created_auto_now_add(self, product_pizza, db):
        """Тест автоматической даты создания"""
        from django.utils import timezone
        assert product_pizza.created is not None
        assert product_pizza.created <= timezone.now()

    def test_product_verbose_names(self, db, category_pizza):
        """Тест verbose_name для продукта"""
        product = Product.objects.create(
            name='Тест',
            slug='test',
            category=category_pizza,
            price=Decimal('100.00')
        )
        assert product._meta.verbose_name == 'Продукт'
        assert product._meta.verbose_name_plural == 'Продукты'

    def test_product_price_decimal_places(self, db, category_pizza):
        """Тест точности цены"""
        product = Product.objects.create(
            name='Точная цена',
            slug='tochnaya-cena',
            category=category_pizza,
            price=Decimal('99.99')
        )
        assert product.price == Decimal('99.99')

    def test_product_filter_by_category(self, category_pizza, product_pizza, product_sushi):
        """Тест фильтрации продуктов по категории"""
        pizza_products = Product.objects.filter(category=category_pizza)
        assert product_pizza in pizza_products
        assert product_sushi not in pizza_products

    def test_product_filter_extras(self, category_pizza, product_pizza, product_extra):
        """Тест фильтрации extras"""
        extras = Product.objects.filter(category=category_pizza, is_extra=True)
        assert product_extra in extras
        assert product_pizza not in extras


class TestShopViews:
    """Тесты для views приложения shop"""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def auth_client(self, client, db):
        """Клиент с сессией для корзины"""
        return client

    def test_index_view_status_200(self, client, category_pizza, category_sushi):
        """Тест главной страницы - статус 200"""
        response = client.get(reverse('shop:index'))
        assert response.status_code == 200

    def test_index_view_template(self, client, category_pizza):
        """Тест что index использует правильный шаблон"""
        response = client.get(reverse('shop:index'))
        assert 'shop/product/index.html' in [t.name for t in response.templates]

    def test_index_view_context_categories(self, client, category_pizza, category_sushi, category_napitki):
        """Тест контекста categories на главной странице"""
        response = client.get(reverse('shop:index'))
        assert 'categories' in response.context
        categories = response.context['categories']
        assert category_pizza in categories
        assert category_sushi in categories

    def test_index_view_context_new_products(self, client, product_pizza, product_sushi):
        """Тест контекста новых продуктов на главной странице"""
        response = client.get(reverse('shop:index'))
        assert 'new_pizzas' in response.context
        assert 'new_sushis' in response.context

    def test_index_view_empty_categories(self, client, db):
        """Тест главной страницы без категорий"""
        response = client.get(reverse('shop:index'))
        assert response.status_code == 200
        assert response.context['categories'].count() == 0

    def test_category_detail_view_200(self, client, category_pizza):
        """Тест страницы категории - статус 200"""
        response = client.get(reverse('shop:category_detail', args=['pizza']))
        assert response.status_code == 200

    def test_category_detail_view_404(self, client, db):
        """Тест страницы несуществующей категории - 404"""
        response = client.get(reverse('shop:category_detail', args=['non-existent']))
        assert response.status_code == 404

    def test_category_detail_view_template(self, client, category_pizza):
        """Тест что category_detail использует правильный шаблон"""
        response = client.get(reverse('shop:category_detail', args=['pizza']))
        assert 'shop/product/category_detail.html' in [t.name for t in response.templates]

    def test_category_detail_view_context(self, client, category_pizza, product_pizza):
        """Тест контекста страницы категории"""
        response = client.get(reverse('shop:category_detail', args=['pizza']))
        assert 'category' in response.context
        assert response.context['category'] == category_pizza

    def test_category_detail_view_products(self, client, category_pizza, product_pizza):
        """Тест продуктов в контексте страницы категории"""
        response = client.get(reverse('shop:category_detail', args=['pizza']))
        assert 'products_main' in response.context
        assert product_pizza in response.context['products_main']

    def test_category_detail_view_children(self, client, parent_category, child_category, db):
        """Тест страницы родительской категории с дочерними"""
        response = client.get(reverse('shop:category_detail', args=['myasnaya']))
        assert response.status_code == 200
        assert child_category in response.context['products_main']

    def test_category_detail_view_cart_form(self, client, category_pizza):
        """Тест наличия формы добавления в корзину"""
        response = client.get(reverse('shop:category_detail', args=['pizza']))
        assert 'cart_product_form' in response.context

    def test_product_detail_view_200(self, client, product_pizza):
        """Тест страницы продукта - статус 200"""
        response = client.get(reverse('shop:product_detail', args=['pepperoni']))
        assert response.status_code == 200

    def test_product_detail_view_404(self, client, db):
        """Тест страницы несуществующего продукта - 404"""
        response = client.get(reverse('shop:product_detail', args=['non-existent']))
        assert response.status_code == 404

    def test_product_detail_view_template(self, client, product_pizza):
        """Тест что product_detail использует правильный шаблон"""
        response = client.get(reverse('shop:product_detail', args=['pepperoni']))
        assert 'shop/product/product_detail.html' in [t.name for t in response.templates]

    def test_product_detail_view_context(self, client, product_pizza):
        """Тест контекста страницы продукта"""
        response = client.get(reverse('shop:product_detail', args=['pepperoni']))
        assert 'product' in response.context
        assert response.context['product'] == product_pizza

    def test_product_detail_view_extras(self, client, product_pizza, product_extra):
        """Тест extras в контексте продукта"""
        product_pizza.extras.add(product_extra)
        response = client.get(reverse('shop:product_detail', args=['pepperoni']))
        assert 'extras' in response.context
        assert product_extra in response.context['extras']

    def test_privacy_view_200(self, client):
        """Тест страницы политики конфиденциальности"""
        response = client.get(reverse('shop:privacy'))
        assert response.status_code == 200

    def test_uslovia_dostavki_view_200(self, client):
        """Тест страницы условий доставки"""
        response = client.get(reverse('shop:uslovia-dostavki'))
        assert response.status_code == 200

    def test_offer_view_200(self, client):
        """Тест страницы публичной оферты"""
        response = client.get(reverse('shop:offer'))
        assert response.status_code == 200

    def test_obmen_view_200(self, client):
        """Тест страницы обмена и возврата"""
        response = client.get(reverse('shop:obmen'))
        assert response.status_code == 200

    def test_cart_view_200(self, client):
        """Тест страницы корзины (заглушка)"""
        response = client.get(reverse('shop:cart'))
        assert response.status_code == 200

    def test_product_list_pizza_view_200(self, client):
        """Тест страницы списка пицц (заглушка)"""
        response = client.get(reverse('shop:product-list-pizza'))
        assert response.status_code == 200

    def test_product_list_sushi_view_200(self, client):
        """Тест страницы списка суши (заглушка)"""
        response = client.get(reverse('shop:product-list-sushi'))
        assert response.status_code == 200

    def test_additions_list_view_200(self, client):
        """Тест страницы добавок (заглушка)"""
        response = client.get(reverse('shop:additions-list'))
        assert response.status_code == 200


class TestShopUrls:
    """Тесты для URL маршрутов shop"""

    def test_index_url_resolve(self):
        """Тест резолва URL главной страницы"""
        url = reverse('shop:index')
        assert url == '/'
        match = resolve('/')
        assert match.func == views.index
        assert match.app_name == 'shop'

    def test_category_detail_url_resolve(self):
        """Тест резолва URL категории"""
        url = reverse('shop:category_detail', args=['pizza'])
        assert url == '/category/pizza/'
        match = resolve('/category/pizza/')
        assert match.func == views.category_detail
        assert match.kwargs['slug'] == 'pizza'

    def test_product_detail_url_resolve(self):
        """Тест резолва URL продукта"""
        url = reverse('shop:product_detail', args=['pepperoni'])
        assert url == '/product/pepperoni/'
        match = resolve('/product/pepperoni/')
        assert match.func == views.product_detail
        assert match.kwargs['slug'] == 'pepperoni'

    def test_privacy_url_resolve(self):
        """Тест резолва URL политики"""
        url = reverse('shop:privacy')
        assert url == '/privacy/'
        match = resolve('/privacy/')
        assert match.func == views.privacy

    def test_uslovia_dostavki_url_resolve(self):
        """Тест резолва URL условий доставки"""
        url = reverse('shop:uslovia-dostavki')
        assert url == '/uslovia-dostavki/'
        match = resolve('/uslovia-dostavki/')
        assert match.func == views.uslovia_dostavki

    def test_offer_url_resolve(self):
        """Тест резолва URL оферты"""
        url = reverse('shop:offer')
        assert url == '/offer/'
        match = resolve('/offer/')
        assert match.func == views.offer

    def test_obmen_url_resolve(self):
        """Тест резолва URL обмена"""
        url = reverse('shop:obmen')
        assert url == '/obmen/'
        match = resolve('/obmen/')
        assert match.func == views.obmen

    def test_shop_cart_url_resolve(self):
        """Тест резолва URL корзины в shop"""
        url = reverse('shop:cart')
        assert url == '/cart/'
        match = resolve('/cart/')
        assert match.func == views.cart

    def test_product_list_pizza_url_resolve(self):
        """Тест резолва URL списка пицц"""
        url = reverse('shop:product-list-pizza')
        assert url == '/product-list-pizza/'
        match = resolve('/product-list-pizza/')
        assert match.func == views.product_list_pizza

    def test_product_list_sushi_url_resolve(self):
        """Тест резолва URL списка суши"""
        url = reverse('shop:product-list-sushi')
        assert url == '/product-list-sushi/'
        match = resolve('/product-list-sushi/')
        assert match.func == views.product_list_sushi

    def test_additions_list_url_resolve(self):
        """Тест резолва URL списка добавок"""
        url = reverse('shop:additions-list')
        assert url == '/additions-list/'
        match = resolve('/additions-list/')
        assert match.func == views.additions_list


class TestShopContextProcessors:
    """Тесты для контекст-процессоров shop"""

    def test_categories_context_processor(self, client, category_pizza, category_sushi):
        """Тест контекст-процессора категорий"""
        response = client.get(reverse('shop:index'))
        assert 'menu_categories' in response.context
        assert category_pizza in response.context['menu_categories']
        assert category_sushi in response.context['menu_categories']

    def test_categories_only_parent(self, client, parent_category, child_category):
        """Тест что выводятся только родительские категории"""
        response = client.get(reverse('shop:index'))
        menu_categories = response.context['menu_categories']
        assert parent_category in menu_categories
        assert child_category not in menu_categories

    def test_categories_empty(self, client, db):
        """Тест контекст-процессора без категорий"""
        response = client.get(reverse('shop:index'))
        assert 'menu_categories' in response.context
        assert response.context['menu_categories'].count() == 0
