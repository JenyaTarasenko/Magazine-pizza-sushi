from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from orders.models import Order, Payment
from orders.liqpay import LiqPay
from shop.models import Category, Product


@override_settings(
    LIQPAY_PUBLIC_KEY='pk', LIQPAY_PRIVATE_KEY='sk',
    SECURE_SSL_REDIRECT=False, SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False,
)
class ProbeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='C', slug='c')
        cls.product = Product.objects.create(
            name='P', slug='p', category=cls.category,
            price=Decimal('150.00'), weight=500,
            description='d', is_extra=False,
        )

    def test_probe_01_payment_cancel(self):
        try:
            resp = self.client.get(reverse('orders:payment_cancel'), secure=True)
            print('PAYMENT_CANCEL status:', resp.status_code)
            print('PAYMENT_CANCEL templates:', [t.name for t in resp.templates])
        except Exception as e:
            print('PAYMENT_CANCEL EXC:', type(e).__name__, str(e)[:300])

    def test_probe_02_atomic_error(self):
        session = self.client.session
        session[settings.CART_SESSION_ID] = {str(self.product.id): {'quantity': 2, 'price': '150.00'}}
        session.save()
        data = {'first_name': 'Иван', 'last_name': 'Иванов',
                'email': 'error@test.com', 'phone': '+380991234567'}
        with patch('orders.views.create_payment', side_effect=RuntimeError('boom')):
            try:
                resp = self.client.post(reverse('orders:order_create'), data=data, secure=True)
                print('ATOMIC_ERR status:', resp.status_code)
                print('ATOMIC_ERR templates:', [t.name for t in resp.templates])
                print('ATOMIC_ERR order count:', Order.objects.count())
                print('ATOMIC_ERR payment count:', Payment.objects.count())
            except Exception as e:
                print('ATOMIC_ERR EXC:', type(e).__name__, str(e)[:300])

    def test_probe_03_webhook_signature(self):
        order = Order.objects.create(
            first_name='Ф', last_name='Л', email='f@l.com', phone='+380991234567')
        lp = LiqPay('pk', 'sk')
        params = {'order_id': str(order.id), 'status': 'success', 'transaction_id': 'TX1'}
        data = lp.cnb_data(params)
        signature = lp.cnb_signature(params)
        from orders.views import liqpay_webhook
        resp = self.client.post(reverse('orders:liqpay_webhook'),
                                {'data': data, 'signature': signature}, secure=True)
        print('WEBHOOK status:', resp.status_code, 'order.paid:', Order.objects.get(pk=order.pk).paid)
        print('      payments:', list(Payment.objects.filter(order=order).values('status', 'transaction_id')))

    def test_probe_04_webhook_wait_accept(self):
        order = Order.objects.create(
            first_name='Ф', last_name='Л', email='f2@l.com', phone='+380991234568')
        Payment.objects.create(order=order, amount=Decimal('300.00'),
                               provider='liqpay', currency='UAH', status='pending')
        lp = LiqPay('pk', 'sk')
        params = {'order_id': str(order.id), 'status': 'wait_accept', 'transaction_id': 'TX2'}
        data = lp.cnb_data(params)
        signature = lp.cnb_signature(params)
        resp = self.client.post(reverse('orders:liqpay_webhook'),
                                {'data': data, 'signature': signature}, secure=True)
        fresh = Order.objects.get(pk=order.pk)
        print('WAIT_ACCEPT status:', resp.status_code)
        print('     paid:', fresh.paid, 'payments:',
              list(Payment.objects.filter(order=order).values('status', 'transaction_id')))

    def test_probe_05_repeat_webhook(self):
        order = Order.objects.create(
            first_name='Ф', last_name='Л', email='f3@l.com', phone='+380991234569')
        Payment.objects.create(order=order, amount=Decimal('300.00'),
                               provider='liqpay', currency='UAH', status='pending')
        lp = LiqPay('pk', 'sk')
        params = {'order_id': str(order.id), 'status': 'success', 'transaction_id': 'TX3'}
        data = lp.cnb_data(params)
        signature = lp.cnb_signature(params)
        r1 = self.client.post(reverse('orders:liqpay_webhook'),
                              {'data': data, 'signature': signature}, secure=True)
        r2 = self.client.post(reverse('orders:liqpay_webhook'),
                              {'data': data, 'signature': signature}, secure=True)
        print('REPEAT r1:', r1.status_code, 'r2:', r2.status_code,
              'paid:', Order.objects.get(pk=order.pk).paid,
              'pmt_count:', Payment.objects.filter(order=order).count())

    def test_probe_06_multiple_payments(self):
        order = Order.objects.create(
            first_name='Ф', last_name='Л', email='f4@l.com', phone='+380991234560')
        Payment.objects.create(order=order, amount=Decimal('300.00'),
                               provider='liqpay', currency='UAH', status='failed')
        Payment.objects.create(order=order, amount=Decimal('300.00'),
                               provider='liqpay', currency='UAH', status='pending')
        lp = LiqPay('pk', 'sk')
        params = {'order_id': str(order.id), 'status': 'success', 'transaction_id': 'TX4'}
        data = lp.cnb_data(params)
        signature = lp.cnb_signature(params)
        resp = self.client.post(reverse('orders:liqpay_webhook'),
                                {'data': data, 'signature': signature}, secure=True)
        print('MULTI status:', resp.status_code, 'paid:', Order.objects.get(pk=order.pk).paid)
        print('      payments:', list(Payment.objects.filter(order=order).order_by('id').values('status', 'transaction_id')))