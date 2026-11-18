import pytest
from django.core import mail

from shop.factories import CustomerFactory, OrderFactory, OrderItemFactory, PaymentFactory
from shop.models import Order
from shop.services import pay_order
from shop.tasks import send_order_receipt


@pytest.mark.django_db
def test_send_order_receipt_is_idempotent(mailoutbox):
    customer = CustomerFactory(email="receipt@example.com")
    order = OrderFactory(customer=customer, status=Order.Status.PAID)
    OrderItemFactory(order=order, quantity=2, unit_price="12.50")
    payment = PaymentFactory(order=order, amount="25.00")

    assert send_order_receipt.delay(order.pk).get() == "sent"
    payment.refresh_from_db()
    assert payment.receipt_sent_at is not None
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [customer.email]
    assert "Total: 25.00 €" in mail.outbox[0].body

    assert send_order_receipt.delay(order.pk).get() == "already-sent"
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_payment_schedules_receipt_after_transaction_commit(
    django_capture_on_commit_callbacks, mailoutbox
):
    customer = CustomerFactory(email="after-commit@example.com")
    order = OrderFactory(customer=customer)
    OrderItemFactory(order=order)

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        paid_order = pay_order(order)

    assert len(callbacks) == 1
    assert paid_order.status == Order.Status.PAID
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [customer.email]
