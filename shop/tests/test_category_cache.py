import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from shop.models import Category
from shop.signals import CATEGORY_CACHE_VERSION_KEY


@pytest.mark.django_db
def test_category_list_cache_hits_and_invalidates_after_category_save():
    cache.clear()
    category = Category.objects.create(name="Coffee", slug="coffee")
    client = APIClient()

    first = client.get("/api/v1/categories/")
    second = client.get("/api/v1/categories/")

    assert first.status_code == 200
    assert first["X-Cache"] == "MISS"
    assert second["X-Cache"] == "HIT"
    assert second.data == first.data

    category.name = "Coffee and tea"
    category.save(update_fields=["name"])
    third = client.get("/api/v1/categories/")

    assert cache.get(CATEGORY_CACHE_VERSION_KEY) == 2
    assert third["X-Cache"] == "MISS"
    assert third.data["results"][0]["name"] == "Coffee and tea"
    assert client.get("/api/v1/categories/")["X-Cache"] == "HIT"
