from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import AuditEvent
from .serializers import MeSerializer


class AuditedTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        token_pair = super().validate(attrs)
        request = self.context.get("request")
        AuditEvent.objects.create(
            user=self.user,
            action=AuditEvent.Action.JWT_LOGIN,
            ip=request.META.get("REMOTE_ADDR") if request else None,
            data={},
        )
        return token_pair


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
    serializer_class = AuditedTokenObtainPairSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        return Response(
            {
                "id": request.user.pk,
                "username": request.user.get_username(),
                "groups": list(request.user.groups.values_list("name", flat=True)),
            }
        )
