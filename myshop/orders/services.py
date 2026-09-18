from django.conf import settings
from django.urls import reverse

from .liqpay import LiqPay
from .models import Payment


def get_liqpay_context(order):
    """
    Формирует данные для оплаты заказа через LiqPay.

    Возвращает:
        {
            "data": "...",
            "signature": "..."
        }
    """

    liqpay = LiqPay(
        settings.LIQPAY_PUBLIC_KEY,
        settings.LIQPAY_PRIVATE_KEY,
    )

    params = {
        "action": "pay",
        "amount": str(order.get_total_cost()),
        "currency": "UAH",
        "description": f"Оплата заказа №{order.id}",
        "order_id": str(order.id),
        "version": "3",
        "sandbox": 1,
        "server_url": (
            "https://sushipizza.pythonanywhere.com"
            + reverse("orders:liqpay_webhook")
        ),
        "result_url": (
            "https://sushipizza.pythonanywhere.com"
            + reverse("orders:payment_success")
        ),
    }

    data = liqpay.cnb_data(params)
    signature = liqpay.cnb_signature(params)

    return {
        "data": data,
        "signature": signature,
    }



def create_payment(order):
    return Payment.objects.create(
            order=order,
            provider="liqpay",
            amount=order.get_total_cost(),
            currency="UAH",
            status="pending",
    )

#функция обработки статуса 
def is_successful_liqpay_status(status):
    if status == "success":
        return True

    if status == "sandbox":
        return True

    return False