from django.shortcuts import render



def index(request):
    return render(request, 'shop/product/index.html')

def product_detail(request):
    return render(request, 'shop/product/detail.html')

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