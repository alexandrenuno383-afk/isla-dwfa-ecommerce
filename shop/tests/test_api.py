from decimal import Decimal

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from shop.factories import (
    CategoryFactory,
    CustomerFactory,
    OrderFactory,
    OrderItemFactory,
    PaymentFactory,
    ProductFactory,
)
from shop.models import Order, Payment


@pytest.mark.django_db
def test_order_list_is_paginated():
    OrderFactory.create_batch(25)

    response = APIClient().get("/api/v1/orders/")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"count", "next", "previous", "results"}
    assert body["count"] == 25
    assert len(body["results"]) == 20


@pytest.mark.django_db
def test_order_create_validates_stock_and_persists_order():
    product = ProductFactory(stock=5, price="12.50")
    customer = CustomerFactory()
    client = APIClient()

    response = client.post(
        "/api/v1/orders/",
        {"customer": customer.pk, "items": [{"product": product.pk, "quantity": 2}]},
        format="json",
    )

    assert response.status_code == 201, response.data
    assert Order.objects.filter(pk=response.data["id"]).exists()
    assert response.data["total"] == "25.00"
    product.refresh_from_db()
    assert product.stock == 3

    invalid = client.post(
        "/api/v1/orders/",
        {"customer": customer.pk, "items": [{"product": product.pk, "quantity": 4}]},
        format="json",
    )
    assert invalid.status_code == 400
    assert invalid["Content-Type"].startswith("application/problem+json")
    assert invalid.data["status"] == 400
    assert "quantity" in str(invalid.data["errors"]["items"])


@pytest.mark.django_db
def test_invalid_nested_item_does_not_leave_order_or_change_stock():
    customer = CustomerFactory()
    valid_product = ProductFactory(stock=5)
    short_product = ProductFactory(stock=1)
    before = Order.objects.count()

    response = APIClient().post(
        "/api/v1/orders/",
        {
            "customer": customer.pk,
            "items": [
                {"product": valid_product.pk, "quantity": 1},
                {"product": short_product.pk, "quantity": 2},
            ],
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.data["status"] == 400
    assert set(response.data) == {"type", "title", "status", "errors"}
    assert Order.objects.count() == before
    valid_product.refresh_from_db()
    short_product.refresh_from_db()
    assert valid_product.stock == 5
    assert short_product.stock == 1


@pytest.mark.django_db
def test_order_list_with_nested_items_has_no_n_plus_one(django_assert_max_num_queries):
    orders = OrderFactory.create_batch(20)
    for order in orders:
        OrderItemFactory.create_batch(3, order=order)

    with django_assert_max_num_queries(3):
        response = APIClient().get("/api/v1/orders/")
        body = response.json()
        assert body["count"] == 20
        assert len(body["results"]) == 20
        assert len(body["results"][0]["items"]) == 3


@pytest.mark.django_db
def test_order_list_query_baseline_without_prefetch(monkeypatch, django_assert_num_queries):
    orders = OrderFactory.create_batch(20)
    for order in orders:
        OrderItemFactory.create_batch(3, order=order)

    from shop.views import OrderViewSet

    original_get_queryset = OrderViewSet.get_queryset

    def without_prefetch(view):
        return original_get_queryset(view).prefetch_related(None)

    monkeypatch.setattr(OrderViewSet, "get_queryset", without_prefetch)
    with django_assert_num_queries(82):
        response = APIClient().get("/api/v1/orders/")
        assert response.status_code == 200
        assert len(response.data["results"]) == 20


@pytest.mark.django_db
def test_product_price_range_search_and_ordering_filters():
    category = CategoryFactory()
    ProductFactory(category=category, name="Desk Lamp", sku="LAMP-1", price="25.00")
    ProductFactory(category=category, name="Table Lamp", sku="LAMP-2", price="15.00")
    ProductFactory(category=category, name="Desk", sku="DESK-1", price="30.00")

    response = APIClient().get(
        "/api/v1/products/?min_price=10&max_price=25&search=lamp&ordering=-price&page=1"
    )

    assert response.status_code == 200
    assert [row["name"] for row in response.data["results"]] == ["Desk Lamp", "Table Lamp"]


@pytest.mark.django_db
def test_product_page_two_has_seeded_results():
    category = CategoryFactory()
    for index in range(25):
        ProductFactory(category=category, sku=f"PAGED-{index:03d}")

    response = APIClient().get("/api/v1/products/?page=2")

    assert response.status_code == 200
    assert response.data["count"] == 25
    assert len(response.data["results"]) == 5


@pytest.mark.django_db
def test_pay_action_updates_state_and_repeated_payment_conflicts():
    order = OrderFactory()
    OrderItemFactory(order=order, quantity=2, unit_price="12.50")
    client = APIClient()

    response = client.post(f"/api/v1/orders/{order.pk}/pay/")

    assert response.status_code == 200
    assert response.data["status"] == Order.Status.PAID
    assert response.data["total"] == "25.00"
    assert Payment.objects.get(order=order).amount == Decimal("25.00")

    repeated = client.post(f"/api/v1/orders/{order.pk}/pay/")
    assert repeated.status_code == 409


@pytest.mark.django_db
def test_cancel_action_restores_stock():
    product = ProductFactory(stock=3)
    order = OrderFactory()
    OrderItemFactory(order=order, product=product, quantity=2)

    response = APIClient().post(f"/api/v1/orders/{order.pk}/cancel/")

    assert response.status_code == 200
    assert response.data["status"] == Order.Status.CANCELLED
    product.refresh_from_db()
    assert product.stock == 5


@pytest.mark.django_db
def test_openapi_schema_is_available():
    response = APIClient().get("/api/schema/")
    assert response.status_code == 200
    assert "openapi" in response.data


@pytest.mark.django_db
def test_payment_cursor_pagination_uses_one_query(django_assert_max_num_queries):
    PaymentFactory.create_batch(25)

    with django_assert_max_num_queries(1):
        response = APIClient().get("/api/v1/payments/")
        body = response.json()
        assert len(body["results"]) == 20
        assert body["next"] is not None


@pytest.mark.django_db
def test_pay_action_uses_its_scoped_throttle(monkeypatch):
    cache.clear()
    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"order-pay": "1/minute"})
    first_order = OrderFactory()
    OrderItemFactory(order=first_order)
    second_order = OrderFactory()
    OrderItemFactory(order=second_order)
    client = APIClient()

    first = client.post(f"/api/v1/orders/{first_order.pk}/pay/")
    second = client.post(f"/api/v1/orders/{second_order.pk}/pay/")

    assert first.status_code == 200
    assert second.status_code == 429
