from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    prepopulated_fields = {'slug': ('name',)}



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_extra')
    list_filter = ('category', 'is_extra')
    search_fields = ('name',)

    prepopulated_fields = {'slug': ('name',)}

    filter_horizontal = ('extras',)