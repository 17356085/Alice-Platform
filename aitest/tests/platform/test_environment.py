"""Environment resource CRUD, default selection and secret-ref tests."""

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aitest.infra.db import Base
from aitest.platform.environment_models import EnvironmentModel  # noqa: F401
from aitest.platform.environment_store import EnvironmentStore


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()


def test_environment_crud_and_default_is_org_scoped(session):
    store = EnvironmentStore(session)
    store.create_environment("dev", "Development", "https://dev.example", org_id="org-a", is_default=True)
    store.create_environment("prod", "Production", "https://prod.example", org_id="org-a")
    store.create_environment("other", "Other", "https://other.example", org_id="org-b", is_default=True)

    store.set_default_environment("prod", org_id="org-a")
    assert store.get_default_environment("org-a").environment_id == "prod"
    assert store.get_default_environment("org-b").environment_id == "other"

    with pytest.raises(ValueError, match="organization"):
        store.set_default_environment("other", org_id="org-a")

    updated = store.update_environment("prod", tags=["release"], variables={"API_URL": "https://api.example"})
    assert updated.tags == ["release"]
    assert store.get_environment("prod").variables["API_URL"] == "https://api.example"
    assert store.delete_environment("dev") is True
    assert store.get_environment("dev") is None


def test_environment_resolves_secret_refs_without_changing_public_values(session):
    store = EnvironmentStore(session)
    store.create_environment(
        "staging",
        "Staging",
        "https://staging.example",
        variables={"TOKEN": "secret:staging-token", "MODE": "staging"},
    )

    with patch("aitest.platform.environment_store.resolve_secret_ref", side_effect=lambda value, _: "resolved-token" if value == "secret:staging-token" else value):
        assert store.resolve_variables("staging") == {"TOKEN": "resolved-token", "MODE": "staging"}

    assert store.get_environment("staging").variables["TOKEN"] == "secret:staging-token"
