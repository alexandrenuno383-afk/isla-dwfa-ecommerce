from celery.result import AsyncResult
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer
from .permissions import is_gestor
from .serializers import OrdersReportAcceptedSerializer, TaskStatusSerializer
from .tasks import export_orders_report


class OrdersReportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={202: OrdersReportAcceptedSerializer})
    def post(self, request):
        customer_id = None
        if not is_gestor(request.user):
            try:
                customer_id = Customer.objects.only("pk").get(user=request.user).pk
            except Customer.DoesNotExist as exc:
                raise ValidationError(
                    {"customer": "Create a customer profile before exporting orders."}
                ) from exc

        task = export_orders_report.delay(request.user.pk, customer_id)
        status_url = f"/api/v1/tasks/{task.id}/"
        cache.set(f"task:{task.id}:owner", request.user.pk, 3600)
        return Response(
            {"id": str(task.id), "status_url": status_url},
            status=status.HTTP_202_ACCEPTED,
            headers={"Location": status_url},
        )


class TaskStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=TaskStatusSerializer)
    def get(self, request, task_id):
        owner_id = cache.get(f"task:{task_id}:owner")
        if owner_id is None or (owner_id != request.user.pk and not is_gestor(request.user)):
            raise NotFound("Task not found.")

        task = AsyncResult(task_id)
        state = task.state
        progress = task.info if state == "PROGRESS" else None
        result = task.result if state == "SUCCESS" else None
        error = str(task.result) if state in {"FAILURE", "REVOKED"} else None
        return Response(
            {
                "id": task_id,
                "state": state,
                "progress": progress,
                "result": result,
                "error": error,
            }
        )
