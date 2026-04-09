from django.shortcuts import render
from .models import Product, Category
from django.shortcuts import get_object_or_404
from cart.forms import CartAddProductForm
from django.db.models import Q


# главная страница 
def index(request):
    # Получаем только категории верхнего уровня
    categories = Category.objects.filter(parent__isnull=True)

    # Новинки: последние 4 пиццы и последние 4 суши
    pizza_category = Category.objects.filter(slug='pizza').first()
    sushi_category = Category.objects.filter(slug='sushi').first()
    napitki_category = Category.objects.filter(slug='napitki').first()

    new_pizzas = Product.objects.filter(
        category__in=pizza_category.children.all() | Category.objects.filter(id=pizza_category.id),
        is_extra=False
    ).order_by('-created')[:4] if pizza_category else []

    new_sushis = Product.objects.filter(
        category__in=sushi_category.children.all() | Category.objects.filter(id=sushi_category.id),
        is_extra=False
    ).order_by('-created')[:4] if sushi_category else []

    new_napitki = Product.objects.filter(
        category__in=napitki_category.children.all() | Category.objects.filter(id=napitki_category.id),
        is_extra=False
    ).order_by('-created')[:4] if napitki_category else []

    context = {
        'categories': categories,
        'new_pizzas': new_pizzas,
        'new_sushis': new_sushis,
        'new_napitki': new_napitki,
    }
    return render(request, 'shop/product/index.html', context)

# поиск отдельная страница
def product_search(request):
    query = request.GET.get('q', '')  # Получаем текст поиска из GET
    products_main = Product.objects.filter(name__icontains=query) if query else []

    # Для каждого продукта достаем его добавки
    for product in products_main:
        product.extras_main = product.extras.all()  # это добавки к конкретной пицце

    context = {
        'query': query,
        'products_main': products_main,
    }
    return render(request, 'shop/product/product_search.html', context)




# так можно обращатся к категории допустим пицца или суши {% url 'shop:category_detail' 'pizza' %}
#  или {% url 'shop:category_detail' 'sushi' %} а любой части сайта  сама страница постороена одна 
# для пиццы и суши через {% if category.slug == 'pizza' %}  {% endif %} {% if category.slug == 'sushi' %}  {% endif %}
# это дает гибкаость в работе и дает правельную практику 

# def category_detail(request, slug):
#     category = get_object_or_404(Category, slug=slug)

#     # Все дочерние категории (если есть)
#     children = category.children.all()
#     cart_product_form = CartAddProductForm()

#     # вытягиваем категориикроме дочерних
#     categories = Category.objects.filter(parent__isnull=True)
#     products_extra = Product.objects.filter(category=category, is_extra=True)

#     # Если есть дочерние категории, собираем все продукты в один список
#     if children.exists():
#         products_main = Product.objects.filter(category__in=children, is_extra=False)
#     else:
#         products_main = Product.objects.filter(category=category, is_extra=False)

#     # Топпинги
#     products_extra = Product.objects.filter(category=category, is_extra=True)


#     # SEO динамическое
#     if hasattr(category, 'description') and category.description:
#         seo_description = category.description[:150]  # первые 150 символов
#     elif products_main.exists():
#         # если нет описания категории, возьмем описание первого продукта
#         seo_description = products_main.first().description[:150]
#     else:
#         seo_description = f"Купити {category.name} онлайн швидко та зручно"

#     seo_title = category.name
#     seo_keywords = ', '.join(category.name.split())



#     context = {
#         'category': category,
#         'products_main': products_main,
#         'products_extra': products_extra,
#         'cart_product_form': cart_product_form,
#         'categories': categories,
#         'seo_title': seo_title,
#         'seo_description': seo_description,
#         'seo_keywords': seo_keywords,
#         'seo_image': category.image.url if category.image else '', 

#     }
#     return render(request, 'shop/product/category_detail.html', context)
    
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)

    children = category.children.all()
    cart_product_form = CartAddProductForm()
    categories = Category.objects.filter(parent__isnull=True)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if children.exists():
        products_main = Product.objects.filter(category__in=children, is_extra=False)
    else:
        products_main = Product.objects.filter(category=category, is_extra=False)

    # фильтр по цене форма находится в category_detail.html и передает данные через hx-get в _products.html
    if min_price:
        products_main = products_main.filter(price__gte=min_price)
    if max_price:
        products_main = products_main.filter(price__lte=max_price)

    products_extra = Product.objects.filter(category=category, is_extra=True)


    # SEO динамическое
    if hasattr(category, 'description') and category.description:
        seo_description = category.description[:150]  # первые 150 символов
    elif products_main.exists():
        # если нет описания категории, возьмем описание первого продукта
        seo_description = products_main.first().description[:150]
    else:
        seo_description = f"Купити {category.name} онлайн швидко та зручно"

    seo_title = category.name
    seo_keywords = ', '.join(category.name.split())

    context = {
        'category': category,
        'products_main': products_main,
        'products_extra': products_extra,
        'cart_product_form': cart_product_form,
        'categories': categories,
        'seo_title': seo_title,
        'seo_description': seo_description,
        'seo_keywords': seo_keywords,
        'seo_image': category.image.url if category.image else '', 
    }

    if request.headers.get('HX-Request'):
        return render(request, 'include/_products.html', context)

    return render(request, 'shop/product/category_detail.html', context)



def product_detail(request, slug):
    # получаем продукт по слагу
    product = get_object_or_404(Product, slug=slug)
    # доп. продукты (сыр, соусы и т.д.)
    extras = product.extras.all()
    # форма для добавления в корзину
    cart_product_form = CartAddProductForm()
    # вытягиваем категориикроме дочерних
    categories = Category.objects.filter(parent__isnull=True)


    # Динамическое SEO
    seo_title = product.name
    seo_description = product.description[:150] if product.description else f"Купити {product.name} онлайн швидко та зручно"
    seo_keywords = ', '.join(product.name.split())
    seo_image = product.image.url if product.image else ''  # если у продукта есть картинка

    
    context = {
        'product': product,
        'extras': extras,
        'cart_product_form': cart_product_form,
        'categories': categories,
        'seo_title': seo_title,
        'seo_description': seo_description,
        'seo_keywords': seo_keywords,
        'seo_image': seo_image,
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

# def cart(request):
#     return render(request, 'shop/product/cart.html')

# def product_list_pizza(request):
#     return render(request, 'shop/product/product-list-pizza.html')

# def product_list_sushi(request):
#     return render(request, 'shop/product/product-list-sushi.html')

# def additions_list(request):
    # return render(request, 'shop/product/product-list-additions.html')