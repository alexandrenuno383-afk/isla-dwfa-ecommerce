from django.core.management.base import BaseCommand

from shop.factories import CategoryFactory, CustomerFactory, ProductFactory


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
        customer = CustomerFactory(
            email="demo@example.com",
            first_name="Demo",
            last_name="Customer",
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed ready: {category.name}, {len(products)} demo products, {customer.email}."
            )
        )
