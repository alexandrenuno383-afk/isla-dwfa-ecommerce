import hashlib

from django.core.cache import cache
from django.db.models import DecimalField, F, Prefetch, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.cache import patch_vary_headers
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import decorators, filters, response, viewsets
from rest_framework import permissions as drf_permissions
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import ScopedRateThrottle

from .api import ProblemDetailsSerializer
from .filters import ProductFilter
from .models import Category, Customer, Order, OrderItem, Payment, Product
from .pagination import PaymentCursorPagination
from .permissions import (
    IsCustomerOwnerOrGestor,
    IsGestorOrReadOnly,
    IsOwnerOrGestor,
    for_owner_or_gestor,
)
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    OrderCreateRequestSerializer,
    OrderSerializer,
    PaymentSerializer,
    ProductSerializer,
)
from .services import cancel_order, pay_order
from .signals import CATEGORY_CACHE_VERSION_KEY


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]
    # O catálogo é público para permitir navegação antes do login.
    permission_classes = [drf_permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        cache.add(CATEGORY_CACHE_VERSION_KEY, 0, timeout=None)
        version = cache.get(CATEGORY_CACHE_VERSION_KEY, 0)
        representation = f"{request.get_full_path()}|{request.accepted_renderer.media_type}"
        digest = hashlib.sha256(representation.encode()).hexdigest()
        cache_key = f"catalog:categories:v{version}:{digest}"
        data = cache.get(cache_key)

        if data is not None:
            cached_response = response.Response(data)
            cached_response["X-Cache"] = "HIT"
            patch_vary_headers(cached_response, ("Accept",))
            return cached_response

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            result = response.Response(serializer.data)

        cache.set(cache_key, result.data, timeout=300)
        result["X-Cache"] = "MISS"
        patch_vary_headers(result, ("Accept",))
        return result


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "sku", "description"]
    ordering_fields = ["name", "price", "stock"]
    ordering = ["name"]
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        return Product.objects.select_related("category")


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["email", "last_name", "created_at"]
    ordering = ["last_name", "first_name"]
    permission_classes = [IsCustomerOwnerOrGestor]

    def get_queryset(self):
        return for_owner_or_gestor(Customer.objects.all(), self.request.user, "user")

    def perform_create(self, serializer):
        if Customer.objects.filter(user=self.request.user).exists():
            raise ValidationError({"detail": "This account already has a customer profile."})
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ["status", "customer"]
    search_fields = ["customer__email"]
    ordering_fields = ["created_at", "status", "total"]
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    throttle_scope = "order-pay"
    permission_classes = [IsOwnerOrGestor]

    @extend_schema(request=OrderCreateRequestSerializer)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        items = OrderItem.objects.select_related("product")
        line_total = F("items__quantity") * F("items__unit_price")
        total = Coalesce(
            Sum(line_total, output_field=DecimalField(max_digits=12, decimal_places=2)),
            Value("0.00", output_field=DecimalField(max_digits=12, decimal_places=2)),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        queryset = (
            Order.objects.select_related("customer__user")
            .prefetch_related(Prefetch("items", queryset=items))
            .annotate(total=total)
            .order_by(*self.ordering)
        )
        # O filtro oculta encomendas alheias com 404; a permission class é a 2.ª camada.
        return for_owner_or_gestor(queryset, self.request.user, "customer__user")

    def perform_create(self, serializer):
        try:
            customer = Customer.objects.get(user=self.request.user)
        except Customer.DoesNotExist as exc:
            raise ValidationError(
                {"customer": "Create a customer profile before placing an order."}
            ) from exc
        serializer.save(customer=customer)

    @extend_schema(
        request=None,
        responses={
            200: OrderSerializer,
            409: OpenApiResponse(
                response=ProblemDetailsSerializer,
                description="The order is not pending or has no items.",
            ),
        },
    )
    @decorators.action(detail=True, methods=["post"], throttle_classes=[ScopedRateThrottle])
    def pay(self, request, pk=None):
        order = pay_order(self.get_object())
        return response.Response(self.get_serializer(order).data)

    @extend_schema(
        request=None,
        responses={
            200: OrderSerializer,
            409: OpenApiResponse(
                response=ProblemDetailsSerializer,
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
    filter_backends = [DjangoFilterBackend]
    pagination_class = PaymentCursorPagination

    def get_queryset(self):
        queryset = Payment.objects.select_related("order", "order__customer")
        return for_owner_or_gestor(queryset, self.request.user, "order__customer__user")
