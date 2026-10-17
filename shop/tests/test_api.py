import pytest
from rest_framework.test import APIClient

from shop.factories import CategoryFactory, CustomerFactory, ProductFactory
from shop.models import Order


@pytest.mark.django_db
def test_product_list_supports_filters_search_ordering_and_pagination():
    category = CategoryFactory()
    ProductFactory(category=category, name="Zebra", sku="Z-1")
    ProductFactory(category=category, name="Apple", sku="A-1")
    response = APIClient().get(
        f"/api/v1/products/?category={category.pk}&ordering=name&page_size=1"
    )
    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["results"][0]["name"] == "Apple"
    assert response.data["next"] is not None


@pytest.mark.django_db
def test_order_create_validates_stock_and_cancel_restores_it():
    product = ProductFactory(stock=5)
    customer = CustomerFactory()
    client = APIClient()
    response = client.post(
        "/api/v1/orders/",
        {"customer": customer.pk, "items": [{"product": product.pk, "quantity": 2}]},
        format="json",
    )
    assert response.status_code == 201, response.data
    product.refresh_from_db()
    assert product.stock == 3
    order_id = response.data["id"]
    response = client.post(f"/api/v1/orders/{order_id}/cancel/")
    assert response.status_code == 200
    product.refresh_from_db()
    assert product.stock == 5
    assert Order.objects.get(pk=order_id).status == Order.Status.CANCELLED


@pytest.mark.django_db
def test_openapi_schema_is_available():
    response = APIClient().get("/api/schema/")
    assert response.status_code == 200
    assert "openapi" in response.data
