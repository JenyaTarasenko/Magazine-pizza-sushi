from django.urls import path
from . import views

app_name = 'shop'


urlpatterns = [
  
    path('', views.index, name='index'),#Главная страница
    path('detail/', views.product_detail, name='product_detail'),#Страница товара
    path('privacy/', views.privacy, name='privacy'),#Политика конфиденциальности
    path('uslovia-dostavki/', views.uslovia_dostavki, name='uslovia-dostavki'),#Условия доставки
    path('offer/', views.offer, name='offer'),#Публичная оферта
    path('obmen/', views.obmen, name='obmen'),#Обмен и возврат
    path('cart/', views.cart, name='cart'),#Корзина
    
    path('product-list-pizza/', views.product_list_pizza, name='product-list-pizza'),#Список пицц
]