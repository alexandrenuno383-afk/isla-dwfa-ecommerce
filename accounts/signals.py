from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from .models import AuditEvent


def _request_ip(request):
    if request is None:
        return None
    # REMOTE_ADDR is supplied by the server; forwarded headers are client-controlled.
    return request.META.get("REMOTE_ADDR") or None


@receiver(user_logged_in)
def record_session_login(sender, request, user, **kwargs):
    AuditEvent.objects.create(
        user=user,
        action=AuditEvent.Action.SESSION_LOGIN,
        ip=_request_ip(request),
        data={},
    )


@receiver(user_login_failed)
def record_login_failure(sender, credentials, request, **kwargs):
    identifier = credentials.get("username") or credentials.get("email")
    AuditEvent.objects.create(
        user=None,
        action=AuditEvent.Action.LOGIN_FAILED,
        ip=_request_ip(request),
        data={"identifier": str(identifier)[:254]} if identifier else {},
    )
