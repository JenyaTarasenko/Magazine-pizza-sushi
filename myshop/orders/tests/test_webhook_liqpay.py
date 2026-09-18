"""
Автоматические тесты webhook LiqPay.

Сценарии:
    1. sandbox  -> paid=True
    2. success  -> paid=True
    3. failure  -> paid=False
    4. неверная signature -> 400
    5. нет data            -> 400
    6. нет signature       -> 400
    7. неизвестный order   -> 404
    8. некорректный data   -> 400
    9. повторный webhook   -> идемпотентно
    10. обновление существующего Payment, без создания нового
"""

import base64

from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from orders.liqpay import LiqPay
from orders.models import Order, Payment

PUBLIC_KEY = "webhook_test_public_key"
PRIVATE_KEY = "webhook_test_private_key"


@override_settings(
    LIQPAY_PUBLIC_KEY=PUBLIC_KEY,
    LIQPAY_PRIVATE_KEY=PRIVATE_KEY,
)
class LiqPayWebhookTestCase(TestCase):
    """Webhook тестируется через реальный класс LiqPay (настоящая подпись)."""

    def setUp(self):
        self.liqpay = LiqPay(PUBLIC_KEY, PRIVATE_KEY)
        self.order = Order.objects.create(
            first_name="Иван",
            last_name="Иванов",
            email="ivan@example.com",
            phone="+380991234567",
            paid=False,
        )
        self.payment = Payment.objects.create(
            order=self.order,
            provider="liqpay",
            amount=Decimal("300.00"),
            currency="UAH",
            status="pending",
        )
        self.webhook_url = reverse("orders:liqpay_webhook")

    def build_payload(self, **params):
        """Формирует корректную пару (data, signature) через класс LiqPay."""
        params.setdefault("order_id", str(self.order.id))
        data = self.liqpay.cnb_data(params)
        signature = self.liqpay.cnb_signature(params)
        return data, signature

    def post_webhook(self, data, signature):
        return self.client.post(
            self.webhook_url,
            {"data": data, "signature": signature},
        )

    def refresh(self):
        self.payment.refresh_from_db()
        self.order.refresh_from_db()

    # --- 1. sandbox -----------------------------------------------------

    def test_webhook_sandbox_marks_order_paid(self):
        """sandbox: 200, статус сохранён, transaction_id сохранён, paid=True."""
        data, signature = self.build_payload(
            status="sandbox",
            transaction_id="TX_SANDBOX",
        )
        response = self.post_webhook(data, signature)

        self.assertEqual(response.status_code, 200)
        self.refresh()
        self.assertEqual(self.payment.status, "sandbox")
        self.assertEqual(self.payment.transaction_id, "TX_SANDBOX")
        self.assertTrue(self.order.paid)

    # --- 2. success -----------------------------------------------------

    def test_webhook_success_marks_order_paid(self):
        """success: 200, статус сохранён, transaction_id сохранён, paid=True."""
        data, signature = self.build_payload(
            status="success",
            transaction_id="TX_SUCCESS",
        )
        response = self.post_webhook(data, signature)

        self.assertEqual(response.status_code, 200)
        self.refresh()
        self.assertEqual(self.payment.status, "success")
        self.assertEqual(self.payment.transaction_id, "TX_SUCCESS")
        self.assertTrue(self.order.paid)

    # --- 3. failure ------------------------------------------------------

    def test_webhook_failure_keeps_order_unpaid(self):
        """failure: 200, статус сохранён, paid остаётся False."""
        data, signature = self.build_payload(
            status="failure",
            transaction_id="TX_FAILURE",
        )
        response = self.post_webhook(data, signature)

        self.assertEqual(response.status_code, 200)
        self.refresh()
        self.assertEqual(self.payment.status, "failure")
        self.assertEqual(self.payment.transaction_id, "TX_FAILURE")
        self.assertFalse(self.order.paid)

    # --- 3b. прочие неуспешные статусы -----------------------------------

    def test_webhook_other_non_success_statuses(self):
        """error/reversed/processing одной транзакции: 200, paid=False."""
        for status in ("error", "reversed", "processing"):
            with self.subTest(status=status):
                data, signature = self.build_payload(
                    status=status,
                    transaction_id="TX_MULTI",
                )
                response = self.post_webhook(data, signature)

                self.assertEqual(response.status_code, 200)
                self.refresh()
                self.assertEqual(self.payment.status, status)
                self.assertEqual(self.payment.transaction_id, "TX_MULTI")
                self.assertFalse(self.order.paid)

    # --- 4. неверная signature ------------------------------------------

    def test_webhook_invalid_signature_returns_400(self):
        """Неверная signature: 400, Payment и Order не меняются."""
        data, _ = self.build_payload(
            status="success",
            transaction_id="TX_BAD_SIG",
        )
        response = self.post_webhook(data, "wrong_signature")

        self.assertEqual(response.status_code, 400)
        self.refresh()
        self.assertEqual(self.payment.status, "pending")
        self.assertEqual(self.payment.transaction_id, "")
        self.assertFalse(self.order.paid)

    # --- 5. отсутствует data ---------------------------------------------

    def test_webhook_without_data_returns_400(self):
        """Webhook без data: 400."""
        response = self.client.post(
            self.webhook_url,
            {"signature": "some_signature"},
        )
        self.assertEqual(response.status_code, 400)

    # --- 6. отсутствует signature ----------------------------------------

    def test_webhook_without_signature_returns_400(self):
        """Webhook без signature: 400."""
        response = self.client.post(
            self.webhook_url,
            {"data": "some_data"},
        )
        self.assertEqual(response.status_code, 400)

    # --- 7. неизвестный Order ---------------------------------------------

    def test_webhook_unknown_order_returns_404(self):
        """Корректно подписанный webhook с неизвестным order_id: 404."""
        data, signature = self.build_payload(
            order_id="999999",
            status="success",
            transaction_id="TX_UNKNOWN",
        )
        response = self.post_webhook(data, signature)

        self.assertEqual(response.status_code, 404)
        self.refresh()
        self.assertEqual(self.payment.status, "pending")
        self.assertFalse(self.order.paid)

    # --- 8. некорректный data ---------------------------------------------

    def test_webhook_invalid_base64_data_returns_400(self):
        """Некорректный base64 с «корректной» подписью: 400, без 500."""
        data = "!!!not_base64!!!"
        signature = self.liqpay.callback_signature(data)
        response = self.post_webhook(data, signature)

        self.assertEqual(response.status_code, 400)
        self.refresh()
        self.assertEqual(self.payment.status, "pending")
        self.assertFalse(self.order.paid)

    def test_webhook_invalid_json_data_returns_400(self):
        """Валидный base64, но не JSON, с корректной подписью: 400."""
        data = base64.b64encode(b"this is not valid json").decode()
        signature = self.liqpay.callback_signature(data)
        response = self.post_webhook(data, signature)

        self.assertEqual(response.status_code, 400)
        self.refresh()
        self.assertEqual(self.payment.status, "pending")
        self.assertFalse(self.order.paid)

    # --- 9. повторный webhook ----------------------------------------------

    def test_webhook_duplicate_is_idempotent(self):
        """Два одинаковых успешных webhook: оба 200, paid=True,
        новый Payment не создаётся, transaction_id сохраняется."""
        data, signature = self.build_payload(
            status="success",
            transaction_id="TX_DUP",
        )
        first = self.post_webhook(data, signature)
        second = self.post_webhook(data, signature)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        self.refresh()
        self.assertTrue(self.order.paid)
        self.assertEqual(self.payment.transaction_id, "TX_DUP")
        self.assertEqual(
            Payment.objects.filter(order=self.order).count(),
            1,
        )

    # --- 10. обновление существующего Payment ------------------------------

    def test_webhook_updates_existing_payment(self):
        """Webhook обновляет существующий pending Payment, не создавая новый."""
        data, signature = self.build_payload(
            status="success",
            transaction_id="TX_ONE",
        )
        payment_id = self.payment.id
        response = self.post_webhook(data, signature)

        self.assertEqual(response.status_code, 200)
        self.refresh()
        self.assertEqual(self.payment.id, payment_id)
        self.assertEqual(self.payment.status, "success")
        self.assertEqual(self.payment.transaction_id, "TX_ONE")
        self.assertTrue(self.order.paid)
        self.assertEqual(
            Payment.objects.filter(order=self.order).count(),
            1,
        )