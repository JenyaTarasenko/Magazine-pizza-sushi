# from liqpay import LiqPay
from django.conf import settings
from django.urls import reverse
from .liqpay import LiqPay

def get_liqpay_context(order):
    liqpay = LiqPay(settings.LIQPAY_PUBLIC_KEY, settings.LIQPAY_PRIVATE_KEY)
    
    # Параметры платежа
    params = {
        'action': 'pay',
        'amount': str(order.get_total_cost()),
        'currency': 'UAH',
        'description': f'Оплата заказа №{order.id}',
        'order_id': str(order.id),
        'version': '3',
        'sandbox': 1, # Удали эту строку или поставь 0, когда будешь принимать реальные деньги
        'server_url': 'https://твой-домен.com' + reverse('orders:liqpay_webhook'), # Сюда придет ответ от банка
        'result_url': 'https://твой-домен.com' + reverse('orders:payment_success'), # Сюда вернется клиент
    }
    
    # Генерируем данные и подпись (signature)
    data = liqpay.cnb_data(params)
   
    signature = liqpay.cnb_signature(data)
    
    return {'data': data, 'signature': signature}