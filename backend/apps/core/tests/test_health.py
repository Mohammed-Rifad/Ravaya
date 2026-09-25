import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_returns_ok_after_database_round_trip(client: Client) -> None:
    response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_returns_error_envelope(client: Client) -> None:
    response = client.get("/api/does-not-exist/")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Not found.", "field": None}
    }
