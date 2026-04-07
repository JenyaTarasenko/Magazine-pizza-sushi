# """
# Views для приложения orders.

# Исправления:
# - Добавлены отсутствующие импорты (LiqPay, settings, Order, HttpResponse)
# - Исправлен метод подписи: str_to_sign -> cnb_signature
# - Добавлена обработка ошибок: try-except для Order.DoesNotExist
# - Добавлено логирование через logging
# - Оптимизированы запросы: select_related/prefetch_related
# - Добавлена обработка ошибок для Telegram-бота
# - Защита от timing attack: hmac.compare_digest
# """

# import hmac
# import logging
# from decimal import Decimal

# from django.shortcuts import render
# from django.http import HttpResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_http_methods
# from django.conf import settings

# from .models import Order, OrderItem
# from .forms import OrderCreateForm
# from .liqpay import LiqPay
# from .services import get_liqpay_context
# from .telegram_bot import send_telegram_message
# from cart.cart import Cart


# logger = logging.getLogger(__name__)


# def payment_success(request):
#     """Страница успешной оплаты."""
#     return render(request, 'orders/order/payment_success.html')


# def payment_cancel(request):
#     """Страница отмены оплаты."""
#     return render(request, 'orders/order/payment_cancel.html')


# @csrf_exempt
# @require_http_methods(["POST"])
# def liqpay_webhook(request):
#     """Webhook для обработки ответов от LiqPay.
    
#     LiqPay присылает POST-запрос без CSRF-токена.
#     Проверяет подпись, обрабатывает успешные платежи и отправляет уведомление в Telegram.
#     """
#     logger.info("LiqPay webhook called")
    
#     data = request.POST.get('data')
#     signature = request.POST.get('signature')
    
#     if not data or not signature:
#         logger.warning("LiqPay webhook called without data or signature")
#         return HttpResponse(status=400)
    
#     try:
#         liqpay = LiqPay(
#             public_key=settings.LIQPAY_PUBLIC_KEY,
#             private_key=settings.LIQPAY_PRIVATE_KEY
#         )
        
#         expected_signature = liqpay.cnb_signature(data)
        
#         if not hmac.compare_digest(expected_signature, signature):
#             logger.warning("LiqPay webhook: invalid signature")
#             return HttpResponse(status=403)
        
#         response_data = liqpay.decode_data_from_str(data)
#         logger.info(f"LiqPay webhook response: {response_data}")
        
#         if response_data.get('status') in ['success', 'wait_accept']:
#             order_id = response_data.get('order_id')
            
#             if not order_id:
#                 logger.error("LiqPay webhook: missing order_id in response")
#                 return HttpResponse(status=400)
            
#             try:
#                 order = Order.objects.select_related().get(id=order_id)
                
#                 if order.paid:
#                     logger.info(f"Order {order_id} already marked as paid")
#                     return HttpResponse()
                
#                 order.paid = True
#                 order.save(update_fields=['paid'])
                
#                 order.refresh_from_db()
                
#                 message = _format_telegram_message(order)
#                 telegram_sent = send_telegram_message(message)
                
#                 if telegram_sent:
#                     logger.info(f"Telegram notification sent for order {order_id}")
#                 else:
#                     logger.warning(f"Failed to send Telegram notification for order {order_id}")
                
#             except Order.DoesNotExist:
#                 logger.error(f"LiqPay webhook: order {order_id} not found")
#                 return HttpResponse(status=404)
#             except Exception as e:
#                 logger.exception(f"Error processing order {order_id}: {e}")
#                 return HttpResponse(status=500)
        
#         return HttpResponse()
        
#     except Exception as e:
#         logger.exception(f"LiqPay webhook critical error: {e}")
#         return HttpResponse(status=500)


# def _format_telegram_message(order):
#     """Формирует сообщение для Telegram."""
#     total_cost = order.get_total_cost()
    
#     items_info = ""
#     if order.items.exists():
#         items = order.items.select_related('product').all()
#         items_list = [
#             f"  - {item.product.name} x{item.quantity} = {item.get_cost()} грн"
#             for item in items
#         ]
#         items_info = "\n".join(items_list)
    
#     message = f"""✅ <b>Новый оплаченный заказ!</b>

# 📦 Заказ №{order.id}
# 👤 Клиент: {order.first_name} {order.last_name}
# 📧 Email: {order.email}
# 📱 Телефон: {order.phone}
# 💰 Сумма: {total_cost} UAH"""

#     if items_info:
#         message += f"\n\n🛒 Состав заказа:\n{items_info}"
    
#     return message


# def order_create(request):
#     """Создание заказа.
    
#     GET: Отображает форму заказа и корзину.
#     POST: Обрабатывает данные формы, создаёт заказ и OrderItem'ы.
#     """
#     cart = Cart(request)
    
#     if request.method == 'POST':
#         form = OrderCreateForm(request.POST)
        
#         if not form.is_valid():
#             logger.warning(f"Order form validation failed: {form.errors}")
#             return render(request, 'orders/order/create.html', {
#                 'cart': cart,
#                 'form': form
#             })
        
#         try:
#             order = form.save(commit=False)
            
#             order_items_data = []
#             for item in cart:
#                 order_items_data.append(OrderItem(
#                     product=item['product'],
#                     price=Decimal(str(item['price'])),
#                     quantity=item['quantity']
#                 ))
            
#             order.save()
            
#             for order_item in order_items_data:
#                 order_item.order = order
#                 order_item.save()
            
#             cart.clear()
            
#             order_with_items = Order.objects.select_related().prefetch_related('items__product').get(id=order.id)
            
#             liqpay_context = get_liqpay_context(order_with_items)
            
#             logger.info(f"Order {order.id} created successfully, total: {order.get_total_cost()}")
            
#             return render(request, 'orders/order/created.html', {
#                 'order': order_with_items,
#                 'liqpay': liqpay_context
#             })
            
#         except Exception as e:
#             logger.exception(f"Error creating order: {e}")
#             return render(request, 'orders/order/create.html', {
#                 'cart': cart,
#                 'form': form,
#                 'error': 'Произошла ошибка при создании заказа. Попробуйте ещё раз.'
#             })
    
#     form = OrderCreateForm()
#     return render(request, 'orders/order/create.html', {
#         'cart': cart,
#         'form': form
#     })


from django.shortcuts import render
from django.shortcuts import render
from .models import OrderItem
from .forms import OrderCreateForm
# from .tasks import order_created
from cart.cart import Cart
from django.views.decorators.csrf import csrf_exempt
from .services import get_liqpay_context
from .telegram_bot import send_telegram_message

def payment_success(request):
    #страница успеха оплаты 
    return render(request, 'orders/order/payment_success.html')


def payment_cancel(request):
    #страница отмены оплаты
    return render(request, 'orders/order/payment_cansel.html')


@csrf_exempt # LiqPay присылает POST-запрос без нашего CSRF-токена
def liqpay_webhook(request):
    print("WEBHOOK CALLED")
    liqpay = LiqPay(settings.LIQPAY_PUBLIC_KEY, settings.LIQPAY_PRIVATE_KEY)
    data = request.POST.get('data')
    signature = request.POST.get('signature')
    
    # Проверяем подпись, чтобы никто не подделал ответ
    sign = liqpay.str_to_sign(settings.LIQPAY_PRIVATE_KEY + data + settings.LIQPAY_PRIVATE_KEY)
    
    if sign == signature:
        response = liqpay.decode_data_from_str(data)
        # Если статус 'success' или 'wait_accept' (деньги в обработке)
        if response['status'] in ['success', 'wait_accept']:
            order_id = response['order_id']
            order = Order.objects.get(id=order_id)
            order.paid = True
            order.save()
            # 🔥 Формируем красивое сообщение
            message = f"""
                ✅ <b>Новый оплаченный заказ!</b>

                📦 Заказ №{order.id}
                👤 Имя: {order.first_name} {order.last_name}
                📧 Email: {order.email}
                💰 Сумма: {order.get_total_cost()} UAH
                """

            send_telegram_message(message)
            
    return HttpResponse()

# для формы заказа 
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order,
                                        product=item['product'],
                                        price=item['price'],
                                        quantity=item['quantity'])
            # clear the cart
            cart.clear()
            # Получаем данные для кнопки LiqPay
            res = get_liqpay_context(order)
            print(f"DEBUG DATA: {res}")
            return render(request,
                          'orders/order/created.html',
                          {'order': order, 'liqpay': res})
    else:
        form = OrderCreateForm()
    return render(request,
                  'orders/order/create.html',
                  {'cart': cart, 'form': form})
