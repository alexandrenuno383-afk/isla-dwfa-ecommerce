import pytest
from django.contrib.auth.models import Group
from django.core.cache import cache
from rest_framework.test import APIClient

from accounts.factories import UserFactory
from shop.factories import CategoryFactory, CustomerFactory, OrderFactory
from shop.models import Order


@pytest.fixture
def actors(db):
    gestor = UserFactory()
    gestor.groups.add(Group.objects.get(name="gestores"))
    return {"anon": None, "customer": UserFactory(), "gestor": gestor}


def as_(user):
    api = APIClient()
    if user:
        api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_order_list_requires_authentication():
    response = APIClient().get("/api/v1/orders/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_user_can_obtain_jwt_pair():
    user = UserFactory(username="ana")

    response = APIClient().post(
        "/api/v1/auth/token/",
        {"username": user.username, "password": "pass1234"},
        format="json",
    )

    assert response.status_code == 200
    assert set(response.data) == {"access", "refresh"}


@pytest.mark.django_db
def test_me_returns_authenticated_user_and_groups():
    user = UserFactory(username="ana")
    client = APIClient()
    pair = client.post(
        "/api/v1/auth/token/",
        {"username": user.username, "password": "pass1234"},
        format="json",
    )

    response = APIClient().get("/api/v1/me/", HTTP_AUTHORIZATION=f"Bearer {pair.data['access']}")

    assert pair.status_code == 200
    assert response.status_code == 200
    assert response.data == {"id": user.pk, "username": "ana", "groups": []}


@pytest.mark.django_db
def test_rotated_refresh_token_is_blacklisted_after_use():
    user = UserFactory(username="ana")
    client = APIClient()
    pair = client.post(
        "/api/v1/auth/token/",
        {"username": user.username, "password": "pass1234"},
        format="json",
    )

    refreshed = client.post(
        "/api/v1/auth/token/refresh/", {"refresh": pair.data["refresh"]}, format="json"
    )
    repeated = client.post(
        "/api/v1/auth/token/refresh/", {"refresh": pair.data["refresh"]}, format="json"
    )

    assert refreshed.status_code == 200
    assert set(refreshed.data) == {"access", "refresh"}
    assert repeated.status_code == 401


@pytest.mark.django_db
def test_login_endpoint_is_throttled_after_ten_attempts():
    cache.clear()
    client = APIClient()
    credentials = {"username": "unknown", "password": "invalid"}

    responses = [client.post("/api/v1/auth/token/", credentials, format="json") for _ in range(10)]
    blocked = client.post("/api/v1/auth/token/", credentials, format="json")

    assert all(response.status_code == 401 for response in responses)
    assert blocked.status_code == 429


@pytest.mark.django_db
def test_vite_origin_is_allowed_for_api_preflight():
    response = APIClient().options(
        "/api/v1/orders/",
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
    )

    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == "http://localhost:5173"


@pytest.mark.parametrize(
    ("role", "expected"),
    [("anon", 401), ("customer", 403), ("gestor", 201)],
)
def test_create_product_by_role(actors, role, expected):
    category = CategoryFactory()
    body = {
        "name": "Lamp",
        "sku": f"LAMP-{role}",
        "price": "9.90",
        "stock": 3,
        "category": category.pk,
    }

    response = as_(actors[role]).post("/api/v1/products/", body, format="json")

    assert response.status_code == expected


@pytest.mark.parametrize(
    ("role", "expected_status", "expected_count"),
    [("anon", 401, 0), ("customer", 200, 1), ("gestor", 200, 2)],
)
def test_order_list_by_role(actors, role, expected_status, expected_count):
    customer = CustomerFactory(user=actors["customer"])
    own_order = OrderFactory(customer=customer)
    other_order = OrderFactory(customer=CustomerFactory(user=UserFactory()))

    response = as_(actors[role]).get("/api/v1/orders/")

    assert response.status_code == expected_status
    if expected_status == 200:
        ids = {row["id"] for row in response.data["results"]}
        assert response.data["count"] == expected_count
        if role == "customer":
            assert ids == {own_order.pk}
        else:
            assert ids == {own_order.pk, other_order.pk}


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/api/v1/orders/{order_id}/", "get"),
        ("/api/v1/orders/{order_id}/pay/", "post"),
    ],
)
def test_customer_gets_404_for_another_customers_order(actors, path, method):
    order = OrderFactory(customer=CustomerFactory(user=UserFactory()))
    url = path.format(order_id=order.pk)

    response = getattr(as_(actors["customer"]), method)(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_order_status_is_read_only_for_owner(actors):
    customer = CustomerFactory(user=actors["customer"])
    order = OrderFactory(customer=customer, status=Order.Status.PENDING)

    response = as_(actors["customer"]).patch(
        f"/api/v1/orders/{order.pk}/",
        {"status": "paid"},
        format="json",
    )

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.Status.PENDING
