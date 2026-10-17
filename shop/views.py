from django.db import transaction
from django.db.models import Count, Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import decorators, filters, response, status, viewsets
from rest_framework.exceptions import ValidationError

from .models import Category, Customer, Order, OrderItem, Payment, Product
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    OrderSerializer,
    PaymentSerializer,
    ProductSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ["name"]
    ordering_fields = ["name", "id"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category")
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "sku", "description"]
    ordering_fields = ["name", "price", "stock"]


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["email", "last_name", "created_at"]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = (
        Order.objects.select_related("customer")
        .prefetch_related(Prefetch("items", queryset=OrderItem.objects.select_related("product")))
        .annotate(item_count=Count("items"))
    )
    serializer_class = OrderSerializer
    filterset_fields = ["status", "customer"]
    search_fields = ["customer__email"]
    ordering_fields = ["created_at", "status", "item_count"]
    http_method_names = ["get", "post", "head", "options"]

    @decorators.action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.Status.PENDING:
            raise ValidationError("Only pending orders can be cancelled.")
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        for item in order.items.select_related("product"):
            item.product.stock += item.quantity
            item.product.save(update_fields=["stock"])
        return response.Response(self.get_serializer(order).data, status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related("order", "order__customer")
    serializer_class = PaymentSerializer
    filterset_fields = ["status", "method"]
    ordering_fields = ["created_at", "amount"]
