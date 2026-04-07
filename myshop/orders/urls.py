from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('liqpay_webhook/', views.liqpay_webhook, name='liqpay_webhook'),
    path('payment/success/', views.payment_success, name='payment_success'),#Успешная оплата orders/templates/orders/order/payment_success.html
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),#Отмена оплаты orders/templates/orders/order/payment_cancel.html
]