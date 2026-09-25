from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    """Enable pgvector before any model needs a vector column (Phase 12)."""

    initial = True
    dependencies: list[tuple[str, str]] = []
    operations = [VectorExtension()]  # runs CREATE EXTENSION IF NOT EXISTS vector
