from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Category

CATEGORY_CACHE_VERSION_KEY = "catalog:categories:version"


def bump_category_cache_version():
    cache.add(CATEGORY_CACHE_VERSION_KEY, 0, timeout=None)
    cache.incr(CATEGORY_CACHE_VERSION_KEY)


@receiver(post_save, sender=Category, dispatch_uid="shop.category_cache_version_on_save")
def category_saved(sender, **kwargs):
    bump_category_cache_version()


@receiver(post_delete, sender=Category, dispatch_uid="shop.category_cache_version_on_delete")
def category_deleted(sender, **kwargs):
    bump_category_cache_version()
