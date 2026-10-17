from django.contrib import admin

from .models import Category, Customer, Order, OrderItem, Payment, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "category", "price", "stock", "is_active"]
    list_select_related = ["category"]
    search_fields = ["name", "sku"]
    list_filter = ["category", "is_active"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["email", "first_name", "last_name", "created_at"]
    search_fields = ["email", "first_name", "last_name"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ["product"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "status", "created_at"]
    list_select_related = ["customer"]
    search_fields = ["customer__email"]
    list_filter = ["status", "created_at"]
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["order", "method", "status", "amount", "created_at"]
    list_select_related = ["order", "order__customer"]
    list_filter = ["status", "method"]
