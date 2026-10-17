from http import HTTPStatus

from rest_framework import serializers
from rest_framework.views import exception_handler


class ProblemDetailsSerializer(serializers.Serializer):
    type = serializers.CharField()
    title = serializers.CharField()
    status = serializers.IntegerField()
    errors = serializers.JSONField()


def problem_details_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = response.data
    errors = details if isinstance(details, (dict, list)) else {"detail": details}
    if isinstance(details, dict) and set(details) == {"detail"}:
        errors = {"detail": details["detail"]}

    response.data = {
        "type": "about:blank",
        "title": HTTPStatus(response.status_code).phrase,
        "status": response.status_code,
        "errors": errors,
    }
    response.content_type = "application/problem+json"
    return response
