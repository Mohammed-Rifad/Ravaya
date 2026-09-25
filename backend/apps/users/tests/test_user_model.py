import pytest
from django.db import IntegrityError, transaction

from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_email_is_stored_lowercased() -> None:
    user = User.objects.create_user("  Layla@Example.COM ", "s3cure-pass-123")

    assert user.email == "layla@example.com"
    assert user.check_password("s3cure-pass-123")
    assert not user.is_staff


def test_email_uniqueness_is_case_insensitive() -> None:
    User.objects.create_user("layla@example.com", "s3cure-pass-123")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user("LAYLA@example.com", "s3cure-pass-123")


def test_database_rejects_mixed_case_email_that_bypasses_save() -> None:
    user = User.objects.create_user("omar@example.com", "s3cure-pass-123")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=user.pk).update(email="Omar@example.com")


def test_login_lookup_ignores_case() -> None:
    User.objects.create_user("noor@example.com", "s3cure-pass-123")

    assert User.objects.get_by_natural_key("NOOR@Example.com").email == "noor@example.com"


def test_create_superuser_sets_flags() -> None:
    admin = User.objects.create_superuser("admin@example.com", "s3cure-pass-123")

    assert admin.is_staff and admin.is_superuser
