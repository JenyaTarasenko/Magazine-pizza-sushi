import pytest
from decimal import Decimal
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from orders.models import Order, OrderItem
from shop.models import Category, Product


class TestOrderModel:
    """Тесты для модели Order"""

    def test_create_order(self, db):
        """Тест создания заказа"""
        order = Order.objects.create(
            first_name='Тест',
            last_name='Тестов',
            email='test@example.com',
            phone='+380991234567'
        )
        assert order.id is not None
        assert order.first_name == 'Тест'
        assert order.last_name == 'Тестов'
        assert order.email == 'test@example.com'
        assert order.phone == '+380991234567'
        assert order.paid is False

    def test_order_str_representation(self, order):
        """Тест строкового представления заказа"""
        result = str(order)
        assert 'Order' in result

    def test_order_default_paid_false(self, db):
        """Тест что paid по умолчанию False"""
        order = Order.objects.create(
            first_name='Тест',
            last_name='Тест',
            email='test@test.com',
            phone='+380000000000'
        )
        assert order.paid is False

    def test_order_paid_can_be_true(self, paid_order):
        """Тест что paid можно установить в True"""
        assert paid_order.paid is True

    def test_order_created_auto_now_add(self, order):
        """Тест автоматической даты создания"""
        from django.utils import timezone
        assert order.created is not None
        assert order.created <= timezone.now()

    def test_order_updated_auto_now(self, order):
        """Тест автоматического обновления"""
        from django.utils import timezone
        old_updated = order.updated
        order.first_name = 'Новое имя'
        order.save()
        assert order.updated >= old_updated
        assert order.updated <= timezone.now()

    def test_order_ordering(self, db):
        """Тест сортировки по умолчанию (новые первыми)"""
        order1 = Order.objects.create(
            first_name='Первый',
            last_name='Тест',
            email='test1@test.com',
            phone='+380000000001'
        )
        order2 = Order.objects.create(
            first_name='Второй',
            last_name='Тест',
            email='test2@test.com',
            phone='+380000000002'
        )
        orders = list(Order.objects.all())
        assert orders[0].id == order2.id
        assert orders[1].id == order1.id

    def test_order_first_name_max_length(self, db):
        """Тест максимальной длины имени"""
        order = Order.objects.create(
            first_name='А' * 50,
            last_name='Тест',
            email='test@test.com',
            phone='+380000000000'
        )
        assert order.first_name == 'А' * 50

    def test_order_first_name_exceeds_max_length(self, db):
        """Тест что имя больше 50 символов вызовет ошибку"""
        with pytest.raises(Exception):
            Order.objects.create(
                first_name='А' * 51,
                last_name='Тест',
                email='test@test.com',
                phone='+380000000000'
            )

    def test_order_last_name_max_length(self, db):
        """Тест максимальной длины фамилии"""
        order = Order.objects.create(
            first_name='Тест',
            last_name='А' * 50,
            email='test@test.com',
            phone='+380000000000'
        )
        assert order.last_name == 'А' * 50

    def test_order_last_name_exceeds_max_length(self, db):
        """Тест что фамилия больше 50 символов вызовет ошибку"""
        with pytest.raises(Exception):
            Order.objects.create(
                first_name='Тест',
                last_name='А' * 51,
                email='test@test.com',
                phone='+380000000000'
            )

    def test_order_phone_max_length(self, db):
        """Тест максимальной длины телефона"""
        order = Order.objects.create(
            first_name='Тест',
            last_name='Тест',
            email='test@test.com',
            phone='+' + '1' * 19
        )
        assert len(order.phone) == 20

    def test_order_email_field_type(self, order):
        """Тест что email валиден"""
        assert '@' in order.email
        assert '.' in order.email.split('@')[1]

    def test_order_items_relationship(self, order_with_items, product, product_extra):
        """Тест связи с OrderItem"""
        items = order_with_items.items.all()
        assert items.count() == 2
        assert product in [item.product for item in items]
        assert product_extra in [item.product for item in items]

    def test_order_items_related_name(self, order_with_items, product):
        """Тест обратной связи"""
        assert order_with_items.items.filter(product=product).exists()

    def test_order_with_no_items(self, order):
        """Тест заказа без товаров"""
        assert order.items.count() == 0

    def test_order_items_empty_returns_empty_queryset(self, order):
        """Тест что пустой заказ возвращает пустой QuerySet"""
        items = order.items.all()
        assert len(items) == 0
        assert items.count() == 0

    def test_order_delete_cascades_to_items(self, db, order, product):
        """Тест каскадного удаления"""
        OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('100.00'),
            quantity=1
        )
        order_id = order.id
        order.delete()
        assert OrderItem.objects.filter(order_id=order_id).count() == 0

    def test_order_get_total_cost_empty(self, order):
        """Тест подсчёта стоимости пустого заказа"""
        assert order.get_total_cost() == Decimal('0')

    def test_order_get_total_cost_with_items(self, order_with_items):
        """Тест подсчёта стоимости заказа с товарами"""
        total = order_with_items.get_total_cost()
        expected = Decimal('150.00') * 2 + Decimal('25.00') * 3
        assert total == expected

    def test_order_get_total_cost_single_item(self, db, order, product):
        """Тест подсчёта стоимости с одним товаром"""
        OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('99.99'),
            quantity=3
        )
        total = order.get_total_cost()
        assert total == Decimal('299.97')

    def test_order_get_total_cost_large_quantity(self, db, order, product):
        """Тест подсчёта с большим количеством товара"""
        OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('10.00'),
            quantity=1000
        )
        total = order.get_total_cost()
        assert total == Decimal('10000.00')


class TestOrderItemModel:
    """Тесты для модели OrderItem"""

    def test_create_order_item(self, db, order, product):
        """Тест создания элемента заказа"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('100.00'),
            quantity=2
        )
        assert item.id is not None
        assert item.order == order
        assert item.product == product
        assert item.price == Decimal('100.00')
        assert item.quantity == 2

    def test_order_item_str_representation(self, db, order, product):
        """Тест строкового представления"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('100.00'),
            quantity=1
        )
        result = str(item)
        assert str(item.id) in result

    def test_order_item_default_quantity(self, db, order, product):
        """Тест количества по умолчанию = 1"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('100.00')
        )
        assert item.quantity == 1

    def test_order_item_get_cost(self, db, order, product):
        """Тест расчёта стоимости элемента"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('50.00'),
            quantity=3
        )
        assert item.get_cost() == Decimal('150.00')

    def test_order_item_get_cost_single(self, db, order, product):
        """Тест расчёта стоимости одного элемента"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('75.50'),
            quantity=1
        )
        assert item.get_cost() == Decimal('75.50')

    def test_order_item_get_cost_zero_quantity(self, db, order, product):
        """Тест стоимости с нулём количества"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('100.00'),
            quantity=0
        )
        assert item.get_cost() == Decimal('0')

    def test_order_item_price_decimal_places(self, db, order, product):
        """Тест точности цены"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('99.99'),
            quantity=1
        )
        assert item.price == Decimal('99.99')

    def test_order_item_max_digits_price(self, db, order, product):
        """Тест что цена может быть до 10 цифр"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('1234567890.00'),
            quantity=1
        )
        assert item.price == Decimal('1234567890.00')

    def test_order_item_product_delete_cascade(self, db, order, product):
        """Тест что удаление продукта удаляет OrderItem"""
        OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('100.00'),
            quantity=1
        )
        product_id = product.id
        product.delete()
        assert OrderItem.objects.filter(product_id=product_id).count() == 0

    def test_order_item_multiple_same_product(self, db, order, product):
        """Тест нескольких позиций одного товара"""
        item1 = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('100.00'),
            quantity=2
        )
        item2 = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('100.00'),
            quantity=3
        )
        assert item1.id != item2.id
        assert order.items.count() == 2

    def test_order_item_order_relationship(self, db, order, product):
        """Тест связи с заказом"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('100.00'),
            quantity=1
        )
        assert item.order == order
        assert item in order.items.all()

    def test_order_item_product_relationship(self, db, order, product):
        """Тест связи с продуктом"""
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price=Decimal('100.00'),
            quantity=1
        )
        assert item.product == product
        assert item in product.order_items.all()


class TestOrderModelEdgeCases:
    """Граничные случаи для модели Order"""

    def test_order_special_characters_in_name(self, db):
        """Тест специальных символов в имени"""
        order = Order.objects.create(
            first_name="О'Коннор",
            last_name='ван дер Берг',
            email='test@test.com',
            phone='+380000000000'
        )
        assert order.first_name == "О'Коннор"
        assert order.last_name == 'ван дер Берг'

    def test_order_unicode_in_fields(self, db):
        """Тест unicode символов"""
        order = Order.objects.create(
            first_name='Αλέξανδρος',
            last_name='Максимов',
            email='test@test.com',
            phone='+380000000000'
        )
        assert order.first_name == 'Αλέξανδρος'

    def test_order_empty_string_first_name(self, db):
        """Тест пустого имени"""
        with pytest.raises(Exception):
            Order.objects.create(
                first_name='',
                last_name='Тест',
                email='test@test.com',
                phone='+380000000000'
            )

    def test_order_long_phone_number(self, db):
        """Тест длинного номера телефона"""
        order = Order.objects.create(
            first_name='Тест',
            last_name='Тест',
            email='test@test.com',
            phone='+3805012345678901234567890'
        )
        assert len(order.phone) > 20

    def test_order_email_case_sensitivity(self, db):
        """Тест что email чувствителен к регистру"""
        order1 = Order.objects.create(
            first_name='Тест1',
            last_name='Тест',
            email='Test@Example.COM',
            phone='+380000000001'
        )
        order2 = Order.objects.create(
            first_name='Тест2',
            last_name='Тест',
            email='test@example.com',
            phone='+380000000002'
        )
        assert order1.email != order2.email

    def test_multiple_orders_same_customer(self, db):
        """Тест нескольких заказов одного клиента"""
        for i in range(5):
            Order.objects.create(
                first_name='Клиент',
                last_name='Тестов',
                email='client@test.com',
                phone=f'+38000000000{i}'
            )
        orders = Order.objects.filter(email='client@test.com')
        assert orders.count() == 5
