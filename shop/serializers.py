from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import Category, Customer, Order, OrderItem, Payment, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]
        read_only_fields = ["id"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "sku",
            "description",
            "price",
            "stock",
            "is_active",
        ]
        read_only_fields = ["id"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "email", "first_name", "last_name", "created_at"]
        read_only_fields = ["id", "created_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "unit_price"]
        read_only_fields = ["id", "unit_price"]

    def validate_quantity(self, quantity):
        if quantity < 1:
            raise serializers.ValidationError("Quantity must be positive.")
        return quantity

    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None))
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        if product and quantity is not None and quantity > product.stock:
            raise serializers.ValidationError(
                {"quantity": f"Only {product.stock} in stock for {product.name}."}
            )
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order", "method", "status", "amount", "created_at"]
        read_only_fields = ["id", "order", "status", "amount", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_email = serializers.EmailField(source="customer.email", read_only=True)
    total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, coerce_to_string=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "customer_email",
            "status",
            "items",
            "total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "total", "created_at", "updated_at"]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("An order must contain at least one item.")
        products = [item["product"].pk for item in items]
        if len(products) != len(set(products)):
            raise serializers.ValidationError("A product can only appear once per order.")
        return items

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        product_ids = {item["product"].pk for item in items_data}
        products = Product.objects.select_for_update().filter(pk__in=product_ids).in_bulk()
        order = Order.objects.create(**validated_data)
        total = Decimal("0.00")
        for item in items_data:
            product = products[item["product"].pk]
            if item["quantity"] > product.stock:
                raise serializers.ValidationError(
                    {"items": f"Insufficient stock for {product.name}."}
                )
            product.stock -= item["quantity"]
            product.save(update_fields=["stock"])
            OrderItem.objects.create(order=order, unit_price=product.price, **item)
            total += product.price * item["quantity"]
        order.total = total
        return order
