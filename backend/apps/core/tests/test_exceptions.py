from rest_framework import exceptions
from rest_framework.exceptions import ErrorDetail

from apps.core.exceptions import api_exception_handler


def test_validation_error_uses_first_field_and_its_code() -> None:
    exc = exceptions.ValidationError(
        {"quantity": [ErrorDetail("Only 3 left in stock.", code="out_of_stock")]}
    )

    response = api_exception_handler(exc, {})

    assert response is not None
    assert response.status_code == 400
    error = response.data["error"]
    assert error["code"] == "out_of_stock"
    assert error["message"] == "Only 3 left in stock."
    assert error["field"] == "quantity"
    assert "quantity" in error["details"]


def test_nested_validation_error_reports_dotted_field_path() -> None:
    exc = exceptions.ValidationError({"address": {"city": ["This field is required."]}})

    response = api_exception_handler(exc, {})

    assert response is not None
    assert response.data["error"]["field"] == "address.city"
    assert response.data["error"]["code"] == "invalid"


def test_api_exception_keeps_its_code_and_status() -> None:
    response = api_exception_handler(exceptions.NotAuthenticated(), {})

    assert response is not None
    assert response.status_code == 401
    assert response.data["error"]["code"] == "not_authenticated"
    assert response.data["error"]["field"] is None
    assert "details" not in response.data["error"]


def test_unhandled_exception_is_left_to_django() -> None:
    assert api_exception_handler(ValueError("boom"), {}) is None
