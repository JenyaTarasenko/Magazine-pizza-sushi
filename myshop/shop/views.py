from django.shortcuts import render
from .models import Product, Category
from django.shortcuts import get_object_or_404


# главная страница 
def index(request):
    # Получаем только категории верхнего уровня
    categories = Category.objects.filter(parent__isnull=True)

    # Новинки: последние 4 пиццы и последние 4 суши
    pizza_category = Category.objects.filter(slug='pizza').first()
    sushi_category = Category.objects.filter(slug='sushi').first()

    new_pizzas = Product.objects.filter(
        category__in=pizza_category.children.all() | Category.objects.filter(id=pizza_category.id),
        is_extra=False
    ).order_by('-created')[:4] if pizza_category else []

    new_sushis = Product.objects.filter(
        category__in=sushi_category.children.all() | Category.objects.filter(id=sushi_category.id),
        is_extra=False
    ).order_by('-created')[:4] if sushi_category else []

    context = {
        'categories': categories,
        'new_pizzas': new_pizzas,
        'new_sushis': new_sushis,
    }
    return render(request, 'shop/product/index.html', context)




# так можно обращатся к категории допустим пицца или суши {% url 'shop:category_detail' 'pizza' %}
#  или {% url 'shop:category_detail' 'sushi' %} а любой части сайта  сама страница постороена одна 
# для пиццы и суши через {% if category.slug == 'pizza' %}  {% endif %} {% if category.slug == 'sushi' %}  {% endif %}
# это дает гибкаость в работе и дает правельную практику 

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)

    # Все дочерние категории (если есть)
    children = category.children.all()

    # Если есть дочерние категории, собираем все продукты в один список
    if children.exists():
        products_main = Product.objects.filter(category__in=children, is_extra=False)
    else:
        products_main = Product.objects.filter(category=category, is_extra=False)

    # Топпинги
    products_extra = Product.objects.filter(category=category, is_extra=True)

    context = {
        'category': category,
        'products_main': products_main,
        'products_extra': products_extra,
    }
    return render(request, 'shop/product/category_detail.html', context)



def product_detail(request, slug):
    # получаем продукт по слагу
    product = get_object_or_404(Product, slug=slug)
    # доп. продукты (сыр, соусы и т.д.)
    extras = product.extras.all()

    context = {
        'product': product,
        'extras': extras,
    }

    return render(request, 'shop/product/product_detail.html', context)



def privacy(request):
    return render(request, 'shop/product/privacy.html')

def uslovia_dostavki(request):
    return render(request, 'shop/product/uslovia-dostavki.html')

def offer(request):
    return render(request, 'shop/product/offer.html')

def obmen(request):
    return render(request, 'shop/product/obmen.html')

def cart(request):
    return render(request, 'shop/product/cart.html')

def product_list_pizza(request):
    return render(request, 'shop/product/product-list-pizza.html')

def product_list_sushi(request):
    return render(request, 'shop/product/product-list-sushi.html')

def additions_list(request):
    return render(request, 'shop/product/product-list-additions.html')