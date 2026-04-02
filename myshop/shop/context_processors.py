from .models import Category

#для меню в шапке сайта shop/templates/include/menu.html
#в settings.py в раздел TEMPLATES добавить 'shop.context_processors.categories'
def categories(request):
    categories = Category.objects.filter(parent__isnull=True)
    return {'menu_categories': categories}