from .cart import Cart

# добавить в settings.py в раздел TEMPLATES 'cart.context_processors.cart',
def cart(request):
    return {'cart': Cart(request)}