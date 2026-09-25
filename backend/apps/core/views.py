from django.db import connection
from django.http import HttpRequest, JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .exceptions import error_body


@api_view(["GET"])
@authentication_classes([])  # public: Railway's health checker has no login
@permission_classes([AllowAny])
def health(request: Request) -> Response:
    """Liveness plus a database round-trip. Used by the platform health check."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return Response(error_body("database_unavailable", "Database is unreachable."), status=503)
    return Response({"status": "ok"})


def not_found(request: HttpRequest, exception: Exception) -> JsonResponse:
    return JsonResponse(error_body("not_found", "Not found."), status=404)


def server_error(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        error_body("server_error", "Something went wrong. Please try again."), status=500
    )
