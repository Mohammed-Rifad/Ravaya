import uuid
from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class UserManager(BaseUserManager["User"]):
    """Creates users with email as the login instead of a username."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra: Any) -> "User":
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=email, **extra)
        user.set_password(password)  # hashes; never stores the raw password
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra: Any) -> "User":
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra: Any) -> "User":
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if not extra["is_staff"] or not extra["is_superuser"]:
            raise ValueError("A superuser must have is_staff and is_superuser set.")
        return self._create_user(email, password, **extra)

    def get_by_natural_key(self, username: str | None) -> "User":
        # Login lookups ignore case: "Layla@X.com" finds "layla@x.com"
        return self.get(email=(username or "").strip().lower())


class User(AbstractBaseUser, PermissionsMixin):
    """Email is the login. Stored lowercased, so `unique` is case-insensitive."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254, unique=True)
    full_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=20, blank=True)  # normalised +9665XXXXXXXX
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []  # createsuperuser asks only for email + password

    class Meta:
        constraints = [
            # Database-level guarantee: even a raw UPDATE can't store "Layla@X.com"
            models.CheckConstraint(
                condition=models.Q(email=Lower("email")),
                name="users_user_email_lowercase",
            ),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.email
