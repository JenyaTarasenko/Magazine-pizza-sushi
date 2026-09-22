from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название категории")
    slug = models.SlugField(unique=True, verbose_name="URL категории")

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительская категория"
    )

    image = models.ImageField(upload_to='categories/', blank=True, verbose_name="Изображение категории")

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:category_detail', args=[self.slug])





class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название продукта")
    slug = models.SlugField(unique=True, verbose_name="URL продукта")

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Категория"
    )

    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Цена")
    weight = models.IntegerField(null=True, blank=True, help_text="Вес в граммах", verbose_name="Вес")

    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(upload_to='products/', verbose_name="Изображение продукта")

    is_extra = models.BooleanField(default=False, verbose_name="Дополнительный товар")

    extras = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        limit_choices_to={'is_extra': True},
        related_name='related_to',
        verbose_name="Дополнительные опции"
    )

    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.slug])