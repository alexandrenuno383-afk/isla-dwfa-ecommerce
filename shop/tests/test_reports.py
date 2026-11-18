from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Group
from django.core.cache import cache
from rest_framework.test import APIClient

from accounts.factories import UserFactory
from shop.factories import CustomerFactory, OrderFactory, OrderItemFactory
from shop.models import Order
from shop.tasks import export_orders_report


@pytest.mark.django_db
def test_export_orders_report_accumulates_totals_and_progress(monkeypatch):
    user = UserFactory()
    customer = CustomerFactory(user=user)
    first = OrderFactory(customer=customer, status=Order.Status.PENDING)
    OrderItemFactory(order=first, quantity=2, unit_price="10.50")
    second = OrderFactory(customer=customer, status=Order.Status.PAID)
    OrderItemFactory(order=second, quantity=1, unit_price="4.00")
    other_customer = CustomerFactory()
    other_order = OrderFactory(customer=other_customer)
    OrderItemFactory(order=other_order, quantity=1, unit_price="90.00")
    progress = []
    monkeypatch.setattr(
        export_orders_report,
        "update_state",
        lambda **state: progress.append(state),
    )
    monkeypatch.setattr("shop.tasks.time.sleep", lambda _seconds: None)

    result = export_orders_report.run(user.pk, customer.pk)

    assert result == {
        "orders": 2,
        "amount": "25.00",
        "by_status": {"pending": 1, "paid": 1, "shipped": 0, "cancelled": 0},
    }
    assert progress == [
        {"state": "PROGRESS", "meta": {"current": 1, "total": 2}},
        {"state": "PROGRESS", "meta": {"current": 2, "total": 2}},
    ]


@pytest.mark.django_db
def test_gestor_report_includes_every_customers_orders(monkeypatch):
    gestor = UserFactory()
    gestor.groups.add(Group.objects.get(name="gestores"))
    first = OrderFactory()
    OrderItemFactory(order=first, unit_price="10.00")
    second = OrderFactory()
    OrderItemFactory(order=second, unit_price="20.00")
    monkeypatch.setattr(export_orders_report, "update_state", lambda **_state: None)
    monkeypatch.setattr("shop.tasks.time.sleep", lambda _seconds: None)

    result = export_orders_report.run(gestor.pk, None)

    assert result["orders"] == 2
    assert result["amount"] == "30.00"


@pytest.mark.django_db
def test_report_endpoint_returns_202_and_records_owner(monkeypatch):
    user = UserFactory()
    customer = CustomerFactory(user=user)
    cache.clear()
    monkeypatch.setattr(
        "shop.report_views.export_orders_report.delay",
        lambda user_id, customer_id: SimpleNamespace(id="report-123"),
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.post("/api/v1/reports/orders/")

    assert response.status_code == 202
    assert response.data == {"id": "report-123", "status_url": "/api/v1/tasks/report-123/"}
    assert response["Location"] == "/api/v1/tasks/report-123/"
    assert cache.get("task:report-123:owner") == user.pk
    assert customer.pk is not None


@pytest.mark.django_db
def test_report_status_shows_progress_for_owner(monkeypatch):
    user = UserFactory()
    cache.set("task:report-456:owner", user.pk, 3600)
    monkeypatch.setattr(
        "shop.report_views.AsyncResult",
        lambda task_id: SimpleNamespace(
            id=task_id, state="PROGRESS", info={"current": 2, "total": 10}, result=None
        ),
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/v1/tasks/report-456/")

    assert response.status_code == 200
    assert response.data == {
        "id": "report-456",
        "state": "PROGRESS",
        "progress": {"current": 2, "total": 10},
        "result": None,
        "error": None,
    }


@pytest.mark.django_db
def test_other_customer_and_unknown_task_both_return_404(monkeypatch):
    owner = UserFactory()
    stranger = UserFactory()
    cache.set("task:owned-task:owner", owner.pk, 3600)
    monkeypatch.setattr(
        "shop.report_views.AsyncResult",
        lambda _task_id: pytest.fail("A task belonging to another user must not be loaded"),
    )
    client = APIClient()
    client.force_authenticate(stranger)

    assert client.get("/api/v1/tasks/owned-task/").status_code == 404
    assert client.get("/api/v1/tasks/unknown-task/").status_code == 404
