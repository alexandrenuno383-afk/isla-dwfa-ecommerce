from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from shop.factories import (
    CategoryFactory,
    CustomerFactory,
    OrderFactory,
    OrderItemFactory,
    ProductFactory,
)
from shop.models import Order


class Command(BaseCommand):
    help = "Create a small, repeatable demo catalogue and customer."

    def handle(self, *args, **options):
        category = CategoryFactory(slug="demo", name="Demo", description="Seed catalogue")
        products = []
        for sku, name, price in (
            ("DEMO-001", "Coffee", "8.50"),
            ("DEMO-002", "Tea", "6.25"),
        ):
            products.append(
                ProductFactory(
                    sku=sku,
                    category=category,
                    name=name,
                    price=price,
                    stock=25,
                )
            )
        for index in range(1, 26):
            name = "Desk Lamp" if index == 1 else f"Demo Accessory {index:02d}"
            products.append(
                ProductFactory(
                    sku=f"DEMO-PAGE-{index:03d}",
                    category=category,
                    name=name,
                    price=f"{10 + index}.00",
                    stock=25,
                )
            )
        # Add thirteen stable SKUs so the catalogue has forty items in a fresh DB,
        # and the documented SKU-0000 search returns exactly ten results.
        for index in range(13):
            products.append(
                ProductFactory(
                    sku=f"SKU-{index:05d}",
                    category=category,
                    name="Desk Lamp" if index == 0 else f"Seed Product {index:02d}",
                    price=f"{20 + index}.00",
                    stock=25,
                )
            )
        User = get_user_model()
        ana, created = User.objects.get_or_create(
            username="ana",
            defaults={"email": "ana@example.com", "first_name": "Ana"},
        )
        if created:
            ana.set_password("pass1234")
            ana.save(update_fields=["password"])

        customer = CustomerFactory(
            email="demo@example.com",
            first_name="Demo",
            last_name="Customer",
        )
        if customer.user_id != ana.pk:
            customer.user = ana
            customer.save(update_fields=["user"])

        order_count = Order.objects.filter(customer=customer).count()
        for index in range(order_count, 10):
            order = OrderFactory(customer=customer)
            first_product = products[(index * 2) % len(products)]
            second_product = products[(index * 2 + 1) % len(products)]
            for product in (first_product, second_product):
                OrderItemFactory(
                    order=order,
                    product=product,
                    quantity=1,
                    unit_price=product.price,
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed ready: {category.name}, {len(products)} demo products, "
                f"{customer.email}, {Order.objects.filter(customer=customer).count()} orders "
                "for ana (password: pass1234)."
            )
        )
