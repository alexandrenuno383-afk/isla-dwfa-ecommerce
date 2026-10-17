import pytest
from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch

from shop.factories import CategoryFactory, CustomerFactory, OrderFactory, ProductFactory
from shop.models import Order, OrderItem, Product


@pytest.mark.django_db
def test_product_price_constraint_rejects_zero():
    category = CategoryFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.create(category=category, name="Invalid", sku="INVALID", price="0.00")


@pytest.mark.django_db
def test_order_listing_with_items_and_customer_uses_two_queries(django_assert_num_queries):
    order = OrderFactory(customer=CustomerFactory())
    OrderItem.objects.create(order=order, product=ProductFactory(), quantity=2, unit_price="12.50")
    queryset = (
        Order.objects.select_related("customer")
        .prefetch_related(Prefetch("items", queryset=OrderItem.objects.select_related("product")))
        .annotate(item_count=Count("items"))
    )

    with django_assert_num_queries(2):
        orders = list(queryset)
        assert orders[0].item_count == 1
        [(item.product.name, orders[0].customer.email) for item in orders[0].items.all()]


@pytest.mark.django_db(transaction=True)
def test_failed_transaction_does_not_leave_order_row():
    customer = CustomerFactory()
    before = customer.orders.count()
    with pytest.raises(RuntimeError), transaction.atomic():
        OrderFactory(customer=customer)
        raise RuntimeError("rollback")
    assert customer.orders.count() == before


@pytest.mark.django_db
def test_duplicate_order_product_is_rejected():
    order = OrderFactory()
    product = ProductFactory()
    OrderItem.objects.create(order=order, product=product, quantity=1, unit_price="12.50")
    with pytest.raises(IntegrityError), transaction.atomic():
        OrderItem.objects.create(order=order, product=product, quantity=1, unit_price="12.50")
