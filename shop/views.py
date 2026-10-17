from django.db.models import DecimalField, F, Prefetch, Sum, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import decorators, filters, response, viewsets

from .filters import ProductFilter
from .models import Category, Customer, Order, OrderItem, Payment, Product
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    OrderSerializer,
    PaymentSerializer,
    ProductSerializer,
)
from .services import cancel_order, pay_order


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "sku", "description"]
    ordering_fields = ["name", "price", "stock"]
    ordering = ["name"]

    def get_queryset(self):
        return Product.objects.select_related("category")


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["email", "last_name", "created_at"]
    ordering = ["last_name", "first_name"]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ["status", "customer"]
    search_fields = ["customer__email"]
    ordering_fields = ["created_at", "status", "total"]
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        items = OrderItem.objects.select_related("product")
        line_total = F("items__quantity") * F("items__unit_price")
        total = Coalesce(
            Sum(line_total, output_field=DecimalField(max_digits=12, decimal_places=2)),
            Value("0.00", output_field=DecimalField(max_digits=12, decimal_places=2)),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        return (
            Order.objects.select_related("customer__user")
            .prefetch_related(Prefetch("items", queryset=items))
            .annotate(total=total)
            .order_by(*self.ordering)
        )

    @extend_schema(
        request=None,
        responses={
            200: OrderSerializer,
            409: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="The order is not pending or has no items.",
            ),
        },
    )
    @decorators.action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        order = pay_order(self.get_object())
        return response.Response(self.get_serializer(order).data)

    @extend_schema(
        request=None,
        responses={
            200: OrderSerializer,
            409: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Only pending orders can be cancelled.",
            ),
        },
    )
    @decorators.action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = cancel_order(self.get_object())
        return response.Response(self.get_serializer(order).data)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.select_related("order", "order__customer")
    serializer_class = PaymentSerializer
    filterset_fields = ["status", "method"]
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]
