import logging

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from cart.cart import Cart

from .forms import OrderCreateForm
from .liqpay import LiqPay
from .models import Order, OrderItem
from .services import create_payment, get_liqpay_context


logger = logging.getLogger(__name__)


def payment_success(request):
    """
    Страница успешного возврата пользователя
    после оплаты через LiqPay.
    """

    return render(
        request,
        "orders/order/payment_success.html",
    )


def payment_cancel(request):
    """
    Страница отмены оплаты.
    """

    return render(
        request,
        "orders/order/payment_cancel.html",
    )


def order_create(request):
    """
    Создание заказа и подготовка оплаты через LiqPay.

    Поток:

        Cart
          ↓
        Order
          ↓
        OrderItem
          ↓
        Payment
          ↓
        LiqPay context
          ↓
        created.html
    """

    cart = Cart(request)

    if request.method == "POST":
        form = OrderCreateForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                "orders/order/create.html",
                {
                    "cart": cart,
                    "form": form,
                },
            )

        try:
            with transaction.atomic():
                # 1. Создаём Order
                order = form.save()

                # 2. Создаём OrderItem
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item["product"],
                        price=item["price"],
                        quantity=item["quantity"],
                    )

                # 3. Создаём внутреннюю запись платежа
                create_payment(order)

                # 4. Формируем данные для LiqPay
                liqpay_context = get_liqpay_context(order)

                # 5. Очищаем корзину только после
                # успешного создания всех данных
                cart.clear()

            # 6. Показываем страницу с оплатой
            return render(
                request,
                "orders/order/created.html",
                {
                    "order": order,
                    "liqpay": liqpay_context,
                },
            )

        except Exception:
            logger.exception(
                "Ошибка при создании заказа"
            )

            return render(
                request,
                "orders/order/create.html",
                {
                    "cart": cart,
                    "form": form,
                    "error": (
                        "Не удалось создать заказ. "
                        "Попробуйте ещё раз."
                    ),
                },
            )

    form = OrderCreateForm()

    return render(
        request,
        "orders/order/create.html",
        {
            "cart": cart,
            "form": form,
        },
    )


@csrf_exempt
@require_POST
def liqpay_webhook(request):
    """
    Webhook LiqPay.

    LiqPay отправляет POST-запрос с:
        data
        signature

    Здесь:
        1. Получаем данные.
        2. Проверяем подпись.
        3. Декодируем data.
        4. Находим Order.
        5. Находим соответствующий Payment.
        6. Обновляем Payment.
        7. При успешной оплате отмечаем Order как paid.

    Telegram здесь пока НЕ вызываем.
    """

    data = request.POST.get("data")
    signature = request.POST.get("signature")

    if not data or not signature:
        logger.warning(
            "LiqPay webhook: отсутствуют data или signature"
        )
        return HttpResponse(status=400)

    try:
        liqpay = LiqPay(
            settings.LIQPAY_PUBLIC_KEY,
            settings.LIQPAY_PRIVATE_KEY,
        )
        
        expected_signature = liqpay.callback_signature(data)

        # expected_signature = liqpay.cnb_signature(
        #     liqpay.decode_data_from_str(data)
        # )

    except Exception:
        logger.exception(
            "LiqPay webhook: ошибка обработки подписи"
        )
        return HttpResponse(status=400)

    if expected_signature != signature:
        logger.warning(
            "LiqPay webhook: неверная signature"
        )
        return HttpResponse(status=400)

    try:
        response = liqpay.decode_data_from_str(data)

    except Exception:
        logger.exception(
            "LiqPay webhook: невозможно декодировать data"
        )
        return HttpResponse(status=400)

    order_id = response.get("order_id")
    status = response.get("status")
    transaction_id = response.get("transaction_id")

    if not order_id:
        logger.warning(
            "LiqPay webhook: отсутствует order_id"
        )
        return HttpResponse(status=400)

    try:
        with transaction.atomic():
            order = (
                Order.objects
                .select_for_update()
                .get(id=order_id)
            )

            payment = (
                order.payments
                .select_for_update()
                .filter(
                    provider="liqpay",
                    status="pending",
                )
                .order_by("-created")
                .first()
            )

            if payment is None:
                logger.warning(
                    "LiqPay webhook: Payment не найден "
                    "для Order %s",
                    order.id,
                )
                return HttpResponse(status=404)

            payment.status = status or payment.status

            if transaction_id:
                payment.transaction_id = transaction_id

            payment.save(
                update_fields=[
                    "status",
                    "transaction_id",
                    "updated",
                ]
            )

            if status == "success":
                order.paid = True
                order.save(
                    update_fields=[
                        "paid",
                        "updated",
                    ]
                )

    except Order.DoesNotExist:
        logger.warning(
            "LiqPay webhook: Order %s не найден",
            order_id,
        )
        return HttpResponse(status=404)

    except Exception:
        logger.exception(
            "LiqPay webhook: ошибка обработки Order %s",
            order_id,
        )
        return HttpResponse(status=500)

    logger.info(
        "LiqPay webhook успешно обработан: "
        "order_id=%s status=%s transaction_id=%s",
        order_id,
        status,
        transaction_id,
    )

    return HttpResponse(status=200)

