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
    list_display = ['id', 'first_name', 'last_name', 'email', 'phone', 'paid', 'created', 'get_total_cost','items_list']
    list_filter = ['paid', 'created', 'updated']
    search_fields = ['first_name', 'last_name', 'email']
    inlines = [OrderItemInline]

    # общая сумма заказа в админке 
    def get_total_cost(self, obj):
        return obj.get_total_cost()
    get_total_cost.short_description = 'Общая сумма заказа'

    #перечень заказа в админке 
    @admin.display(description="Товары")
    def items_list(self, obj):
        return ", ".join(
            f"{item.product.name} × {item.quantity}"
            for item in obj.items.select_related("product").all()
        )


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
        "items_list",
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

    #перечень заказа в админке у платежей 
    @admin.display(description="Товары")
    def items_list(self, obj):
        return ", ".join(
            f"{item.product.name} × {item.quantity}"
            for item in obj.order.items.select_related("product").all()
        )
