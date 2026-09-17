import pytest
from decimal import Decimal
from django.db.models import ProtectedError

from orders.models import Order, Payment


@pytest.fixture
def order(db):
    return Order.objects.create(
        first_name='Иван',
        last_name='Иванов',
        email='ivan@example.com',
        phone='+380991234567',
        paid=False
    )


class TestPaymentModel:
    """Тесты для модели Payment"""

    def test_create_payment(self, db, order):
        """Тест создания платежа"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('150.00')
        )
        assert payment.id is not None
        assert payment.order == order
        assert payment.amount == Decimal('150.00')

    def test_payment_order_relationship(self, db, order):
        """Тест связи Payment -> Order"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('99.99')
        )
        assert payment.order == order
        assert payment.order_id == order.id

    def test_payment_related_name(self, db, order):
        """Тест обратной связи order.payments"""
        Payment.objects.create(order=order, amount=Decimal('100.00'))
        Payment.objects.create(order=order, amount=Decimal('200.00'))
        assert order.payments.count() == 2

    def test_payment_provider_default(self, db, order):
        """Тест значения provider по умолчанию"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('100.00')
        )
        assert payment.provider == 'liqpay'

    def test_payment_currency_default(self, db, order):
        """Тест значения currency по умолчанию"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('100.00')
        )
        assert payment.currency == 'UAH'

    def test_payment_status_default(self, db, order):
        """Тест значения status по умолчанию"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('100.00')
        )
        assert payment.status == 'pending'

    def test_payment_amount(self, db, order):
        """Тест поля amount"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('1234.56')
        )
        assert payment.amount == Decimal('1234.56')

    def test_payment_amount_zero(self, db, order):
        """Тест amount равного нулю"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('0.00')
        )
        assert payment.amount == Decimal('0.00')

    def test_payment_transaction_id_empty_by_default(self, db, order):
        """Тест что transaction_id по умолчанию пустой"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('100.00')
        )
        assert payment.transaction_id == ''

    def test_payment_transaction_id_blank_allowed(self, db, order):
        """Тест что transaction_id можно оставить пустым"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('100.00'),
            transaction_id=''
        )
        assert payment.transaction_id == ''

    def test_payment_transaction_id_can_be_set(self, db, order):
        """Тест установки transaction_id"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('100.00'),
            transaction_id='abc123'
        )
        assert payment.transaction_id == 'abc123'

    def test_payment_str(self, db, order):
        """Тест строкового представления"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('100.00')
        )
        result = str(payment)
        assert f'Payment {payment.id}' in result
        assert f'Order {order.id}' in result

    def test_payment_order_delete_protected(self, db, order):
        """Тест что удаление Order с Payment вызывает ProtectedError"""
        Payment.objects.create(
            order=order,
            amount=Decimal('100.00')
        )
        with pytest.raises(ProtectedError):
            order.delete()

    def test_payment_multiple_for_order(self, db, order):
        """Тест нескольких платежей для одного заказа"""
        Payment.objects.create(order=order, amount=Decimal('50.00'))
        Payment.objects.create(order=order, amount=Decimal('60.00'))
        Payment.objects.create(order=order, amount=Decimal('70.00'))
        assert Payment.objects.filter(order=order).count() == 3

    def test_payment_created_auto_now_add(self, db, order):
        """Тест автоматической даты создания"""
        from django.utils import timezone
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('100.00')
        )
        assert payment.created is not None
        assert payment.created <= timezone.now()

    def test_payment_updated_auto_now(self, db, order):
        """Тест автоматического обновления"""
        payment = Payment.objects.create(
            order=order,
            amount=Decimal('100.00')
        )
        old_updated = payment.updated
        payment.amount = Decimal('150.00')
        payment.save()
        assert payment.updated >= old_updated