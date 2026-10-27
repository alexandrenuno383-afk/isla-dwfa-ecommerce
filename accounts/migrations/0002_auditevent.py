from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("at", models.DateTimeField(auto_now_add=True)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("session_login", "Session login"),
                            ("login_failed", "Login failed"),
                            ("jwt_login", "JWT login"),
                        ],
                        max_length=32,
                    ),
                ),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("data", models.JSONField(blank=True, default=dict)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-at", "-pk"]},
        ),
    ]
