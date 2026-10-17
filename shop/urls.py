from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, CustomerViewSet, OrderViewSet, PaymentViewSet, ProductViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("customers", CustomerViewSet)
router.register("orders", OrderViewSet)
router.register("payments", PaymentViewSet)

urlpatterns = router.urls
