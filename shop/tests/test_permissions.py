import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from accounts.factories import UserFactory
from shop.factories import (
    CategoryFactory,
    CustomerFactory,
    OrderFactory,
    OrderItemFactory,
    PaymentFactory,
    ProductFactory,
)
from shop.models import Order


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def gestor_user():
    user = UserFactory()
    user.groups.add(Group.objects.get(name="gestores"))
    return user


@pytest.mark.django_db
def test_products_are_readable_to_clients_and_writable_only_by_gestores():
    category = CategoryFactory()
    payload = {
        "category": category.pk,
        "name": "Desk Lamp",
        "sku": "MANAGER-LAMP",
        "price": "20.00",
        "stock": 5,
    }
    client = client_for(UserFactory())
    gestor = client_for(gestor_user())

    assert client.get("/api/v1/products/").status_code == 200
    assert client.post("/api/v1/products/", payload, format="json").status_code == 403
    created = gestor.post("/api/v1/products/", payload, format="json")

    assert created.status_code == 201, created.data


@pytest.mark.django_db
def test_anonymous_users_cannot_read_protected_resources():
    client = APIClient()

    assert client.get("/api/v1/products/").status_code == 401
    assert client.get("/api/v1/customers/").status_code == 401
    assert client.get("/api/v1/orders/").status_code == 401
    assert client.get("/api/v1/payments/").status_code == 401


@pytest.mark.django_db
def test_order_list_is_owner_scoped_and_foreign_pay_is_hidden():
    owner = UserFactory()
    other_user = UserFactory()
    own_order = OrderFactory(customer=CustomerFactory(user=owner))
    foreign_order = OrderFactory(customer=CustomerFactory(user=other_user))
    OrderItemFactory(order=own_order)
    OrderItemFactory(order=foreign_order)
    client = client_for(owner)

    listed = client.get("/api/v1/orders/")
    hidden = client.get(f"/api/v1/orders/{foreign_order.pk}/")
    forbidden_payment = client.post(f"/api/v1/orders/{foreign_order.pk}/pay/")

    assert listed.status_code == 200
    assert listed.data["count"] == 1
    assert listed.data["results"][0]["id"] == own_order.pk
    assert hidden.status_code == 404
    assert forbidden_payment.status_code == 404


@pytest.mark.django_db
def test_gestor_sees_all_orders_and_can_pay_another_customers_order():
    owner = UserFactory()
    order = OrderFactory(customer=CustomerFactory(user=owner))
    OrderItemFactory(order=order)
    gestor = client_for(gestor_user())

    listed = gestor.get("/api/v1/orders/")
    paid = gestor.post(f"/api/v1/orders/{order.pk}/pay/")

    assert listed.status_code == 200
    assert listed.data["count"] == 1
    assert paid.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.Status.PAID


@pytest.mark.django_db
def test_order_creation_uses_authenticated_users_customer_profile():
    user = UserFactory()
    own_customer = CustomerFactory(user=user)
    foreign_customer = CustomerFactory()
    product = ProductFactory(stock=5)
    client = client_for(user)

    response = client.post(
        "/api/v1/orders/",
        {
            "customer": foreign_customer.pk,
            "items": [{"product": product.pk, "quantity": 1}],
        },
        format="json",
    )

    assert response.status_code == 201, response.data
    order = Order.objects.get(pk=response.data["id"])
    assert order.customer == own_customer
    assert response.data["customer"] == own_customer.pk


@pytest.mark.django_db
def test_payment_list_is_owner_scoped():
    owner = UserFactory()
    other_user = UserFactory()
    own_order = OrderFactory(customer=CustomerFactory(user=owner))
    other_order = OrderFactory(customer=CustomerFactory(user=other_user))
    OrderItemFactory(order=own_order)
    OrderItemFactory(order=other_order)
    PaymentFactory(order=own_order)
    PaymentFactory(order=other_order)

    response = client_for(owner).get("/api/v1/payments/")

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["order"] == own_order.pk
