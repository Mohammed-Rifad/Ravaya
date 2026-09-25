from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"  # Python import path
    label = "core"  # short name used in migrations and AUTH_USER_MODEL
