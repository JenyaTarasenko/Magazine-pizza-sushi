from django.urls import path
from . import views

app_name = 'shop'


urlpatterns = [
  
    path('', views.index, name='index'),#Главная страница
    path('search/', views.product_search, name='product_search'),#Поиск
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),#Страница товара
    path('privacy/', views.privacy, name='privacy'),#Политика конфиденциальности
    path('uslovia-dostavki/', views.uslovia_dostavki, name='uslovia-dostavki'),#Условия доставки
    path('offer/', views.offer, name='offer'),#Публичная оферта
    path('obmen/', views.obmen, name='obmen'),#Обмен и возврат
    path('about/', views.about, name='about'),#О нас
    path('contact/', views.contact, name='contact'),#Контакты
    # path('cart/', views.cart, name='cart'),#Корзина
    
    # path('product-list-pizza/', views.product_list_pizza, name='product-list-pizza'),#Список пицц
    # path('product-list-sushi/', views.product_list_sushi, name='product-list-sushi'),#Список суши
    # path('additions-list/', views.additions_list, name='additions-list'),#Список суши
]