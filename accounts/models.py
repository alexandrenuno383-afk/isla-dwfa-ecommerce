from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Modelo de utilizador do projeto · the project's user model.

    PT: vazio por agora, de propósito. Trocar o modelo de utilizador *depois* da
    primeira migração é doloroso; declará-lo no dia zero é grátis. Os outros
    modelos referem-no via `settings.AUTH_USER_MODEL`, nunca `User` diretamente.
    EN: empty on purpose. Swapping the user model *after* the first migration is
    painful; declaring it on day zero is free. Other models refer to it through
    `settings.AUTH_USER_MODEL`, never `User` directly.
    """

    class Meta(AbstractUser.Meta):
        db_table = "accounts_user"


class AuditEvent(models.Model):
    """Append-only record of authentication events; credentials are never stored."""

    class Action(models.TextChoices):
        SESSION_LOGIN = "session_login", "Session login"
        LOGIN_FAILED = "login_failed", "Login failed"
        JWT_LOGIN = "jwt_login", "JWT login"

    at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    ip = models.GenericIPAddressField(null=True, blank=True)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-at", "-pk"]

    def __str__(self):
        return f"{self.action} at {self.at:%Y-%m-%d %H:%M:%S}"
