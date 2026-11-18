from django.urls import path
from rest_framework.routers import DefaultRouter

from .report_views import OrdersReportView, TaskStatusView
from .views import CategoryViewSet, CustomerViewSet, OrderViewSet, PaymentViewSet, ProductViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("customers", CustomerViewSet)
router.register("orders", OrderViewSet)
router.register("payments", PaymentViewSet)

urlpatterns = [
    path("reports/orders/", OrdersReportView.as_view(), name="orders-report"),
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),
] + router.urls
