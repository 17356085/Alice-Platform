"""Tests for the production PostgreSQL migration entry point."""

import pytest

from aitest.infra.postgres_migrations import normalize_database_url


def test_normalize_postgres_async_url_for_sync_runner():
    assert normalize_database_url(
        "postgresql+asyncpg://user:pass@db:5432/app"
    ) == "postgresql+psycopg://user:pass@db:5432/app"


def test_normalize_plain_postgres_url_adds_psycopg():
    assert normalize_database_url(
        "postgresql://user:pass@db:5432/app"
    ) == "postgresql+psycopg://user:pass@db:5432/app"


def test_normalize_rejects_non_postgres_url():
    with pytest.raises(ValueError, match="PostgreSQL URL"):
        normalize_database_url("sqlite:///tmp/test.db")
