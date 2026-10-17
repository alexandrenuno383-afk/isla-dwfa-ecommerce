from decimal import Decimal

from django.db import transaction
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.exceptions import APIException

from .models import Order, OrderItem, Payment


class OperationConflict(APIException):
    status_code = 409
    default_detail = "The order state does not allow this operation."
    default_code = "order_state_conflict"


@transaction.atomic
def pay_order(order, method=Payment.Method.MBWAY):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PENDING:
        raise OperationConflict("Only pending orders can be paid.")

    total = order.items.aggregate(
        total=Coalesce(
            Sum(
                F("quantity") * F("unit_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )["total"]
    if total <= 0:
        raise OperationConflict("An order without items cannot be paid.")

    Payment.objects.create(
        order=order,
        method=method,
        status=Payment.Status.SUCCEEDED,
        amount=total,
    )
    order.status = Order.Status.PAID
    order.save(update_fields=["status", "updated_at"])
    order.total = total
    return order


@transaction.atomic
def cancel_order(order):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PENDING:
        raise OperationConflict("Only pending orders can be cancelled.")
    items = list(OrderItem.objects.select_related("product").filter(order=order))
    order.total = sum((item.unit_price * item.quantity for item in items), start=Decimal("0.00"))
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    for item in items:
        item.product.stock += item.quantity
        item.product.save(update_fields=["stock"])
    return order
