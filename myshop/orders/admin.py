from django.contrib import admin
from .models import Order, OrderItem, Payment

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    readonly_fields = ['price', 'quantity', 'get_cost']
    extra = 0

    def get_cost(self, obj):
        return obj.get_cost()
    get_cost.short_description = 'Стоимость'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'paid', 'created', 'get_total_cost']
    list_filter = ['paid', 'created', 'updated']
    search_fields = ['first_name', 'last_name', 'email']
    inlines = [OrderItemInline]

    def get_total_cost(self, obj):
        return obj.get_total_cost()
    get_total_cost.short_description = 'Общая сумма заказа'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "provider",
        "amount",
        "currency",
        "status",
        "transaction_id",
        "created",
        "updated",
    )

    list_filter = (
        "provider",
        "status",
        "currency",
    )

    search_fields = (
        "transaction_id",
        "order__id",
        "order__email",
    )

    ordering = ("-created",)
