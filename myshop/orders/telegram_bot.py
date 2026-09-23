import requests
from django.conf import settings


def send_telegram_message(message):
    url = (
        f"https://api.telegram.org/"
        f"bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def send_payment_notification(payment):
    order = payment.order

    message = (
        "🍕 НОВЫЙ ОПЛАЧЕННЫЙ ЗАКАЗ\n\n"
        f"Заказ №{order.id}\n"
        f"Платёж №{payment.id}\n\n"
        f"👤 Имя: {order.first_name}\n"
        f"👤 Фамилия: {order.last_name}\n"
        f"📞 Телефон: {order.phone}\n\n"
        f"💰 Сумма: {payment.amount} {payment.currency}\n"
        f"💳 Статус: {payment.status}\n"
        f"🔑 Transaction ID: {payment.transaction_id or '—'}"
    )

    return send_telegram_message(message)