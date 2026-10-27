import pytest
from rest_framework.test import APIClient

from accounts.factories import UserFactory
from accounts.models import AuditEvent


@pytest.mark.django_db
def test_successful_session_login_is_audited(client):
    user = UserFactory()

    assert client.login(username=user.username, password="pass1234")
    event = AuditEvent.objects.get(action=AuditEvent.Action.SESSION_LOGIN)
    assert event.user == user
    assert event.ip is None  # Client.login() builds a request without REMOTE_ADDR.
    assert event.data == {}


@pytest.mark.django_db
def test_failed_session_login_is_audited_without_password(client):
    assert not client.login(username="unknown-user", password="secret-password")
    event = AuditEvent.objects.get(action=AuditEvent.Action.LOGIN_FAILED)
    assert event.user is None
    assert event.ip is None
    assert event.data == {"identifier": "unknown-user"}
    assert "password" not in event.data
    assert "secret-password" not in str(event.data)


@pytest.mark.django_db
def test_successful_jwt_login_is_audited():
    user = UserFactory()
    client = APIClient()

    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.username, "password": "pass1234"},
        format="json",
    )

    assert response.status_code == 200
    event = AuditEvent.objects.get(action=AuditEvent.Action.JWT_LOGIN)
    assert event.user == user
    assert event.ip == "127.0.0.1"
    assert event.data == {}
    assert "access" not in event.data
    assert "refresh" not in event.data
