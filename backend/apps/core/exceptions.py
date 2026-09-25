"""One error envelope for every API error.

    { "error": { "code": "...", "message": "...", "field": "..." | null,
                 "details": {...} } }       # details only for validation errors

See docs/api.md.
"""

from typing import Any

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import exception_handler


def error_body(
    code: str,
    message: str,
    field: str | None = None,
    details: Any = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message, "field": field}
    if details is not None:
        error["details"] = details
    return {"error": error}


def _first_error(detail: Any, field: str | None = None) -> tuple[str | None, Any]:
    """Walk nested validation errors and return (field path, first ErrorDetail)."""
    if isinstance(detail, dict):
        for key, value in detail.items():
            if key == api_settings.NON_FIELD_ERRORS_KEY:
                child = field
            else:
                child = f"{field}.{key}" if field else str(key)
            return _first_error(value, child)
    if isinstance(detail, list) and detail:
        return _first_error(detail[0], field)
    return field, detail


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)  # let DRF pick the status code first
    if response is None:
        return None  # unhandled: becomes a 500, reported to Sentry

    if isinstance(exc, exceptions.ValidationError):
        field, first = _first_error(exc.detail)
        code = getattr(first, "code", None) or "invalid"
        response.data = error_body(code, str(first), field, details=response.data)
    elif isinstance(exc, exceptions.APIException):
        codes = exc.get_codes()
        code = codes if isinstance(codes, str) else exc.default_code
        response.data = error_body(str(code), str(exc.detail))
    return response
