import time
from decimal import Decimal

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from .models import Order, OrderItem, Payment


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_order_receipt(order_id: int) -> str:
    """Send the receipt for a paid order once, using only its database id."""
    with transaction.atomic():
        payment = (
            Payment.objects.select_for_update()
            .select_related("order__customer")
            .filter(order_id=order_id)
            .first()
        )
        if payment is None:
            return "payment-not-found"
        if payment.receipt_sent_at is not None:
            return "already-sent"

        order = payment.order
        items = list(order.items.select_related("product").all())
        item_lines = [
            f"{item.quantity} × {item.product.name} — {item.unit_price:.2f} €"
            for item in items
        ]
        message = "\n".join(
            [
                f"Encomenda #{order.pk}",
                "",
                *item_lines,
                "",
                f"Total: {payment.amount:.2f} €",
            ]
        )
        send_mail(
            subject=f"Recibo da encomenda #{order.pk}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            fail_silently=False,
        )
        payment.receipt_sent_at = timezone.now()
        payment.save(update_fields=["receipt_sent_at"])

    return "sent"


@shared_task(bind=True)
def export_orders_report(self, user_id: int, customer_id: int | None) -> dict:
    """Build an order summary for one customer, or all orders for a gestor."""
    user = get_user_model().objects.get(pk=user_id)
    is_manager = user.groups.filter(name="gestores").exists()

    orders = Order.objects.prefetch_related(
        Prefetch(
            "items",
            queryset=OrderItem.objects.select_related("product").order_by("pk"),
        )
    ).order_by("pk")
    if not is_manager:
        orders = orders.filter(customer_id=customer_id, customer__user_id=user_id)

    total = orders.count()
    by_status = {value: 0 for value, _label in Order.Status.choices}
    amount = Decimal("0.00")

    for current, order in enumerate(orders, start=1):
        by_status[order.status] += 1
        amount += sum(
            (item.unit_price * item.quantity for item in order.items.all()),
            start=Decimal("0.00"),
        )
        self.update_state(
            state="PROGRESS",
            meta={"current": current, "total": total},
        )
        time.sleep(0.2)

    return {
        "orders": total,
        "amount": f"{amount:.2f}",
        "by_status": by_status,
    }
