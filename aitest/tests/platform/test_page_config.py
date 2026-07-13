import pytest

from aitest.platform import page_config


class _Store:
    def __init__(self, payload):
        self.payload = payload

    def read(self, *parts):
        assert parts == ("catalog", "pages", "products", "page.json")
        return self.payload


def test_page_config_validates_locators_and_resolves_environment(monkeypatch):
    monkeypatch.setattr(
        page_config,
        "ArtifactStore",
        lambda project_id: _Store(
            '{"url":"${BASE_URL}/products","locators":{"search":"#search"},"config":{"tenant":"${TENANT:-demo}"},"execution":{"wait_for":["search"],"actions":[{"action":"click","target":"search"}]}}'
        ),
    )

    result = page_config.load_page_configs(
        "project-a",
        "catalog",
        ["products"],
        environ={"BASE_URL": "https://example.test", "TENANT": "blue"},
    )

    assert result == [{
        "page_id": "products",
        "url": "https://example.test/products",
        "locators": {"search": "#search"},
        "config": {"tenant": "blue"},
        "execution": {
            "wait_for": ["search"],
            "actions": [{"action": "click", "target": "search", "value": None, "timeout_ms": 30000}],
            "navigation_timeout_ms": 30000,
            "action_timeout_ms": 30000,
            "retry": 0,
        },
        "enabled": True,
    }]


def test_page_config_rejects_missing_environment_and_disabled_page(monkeypatch):
    monkeypatch.setattr(
        page_config,
        "ArtifactStore",
        lambda project_id: _Store('{"url":"${BASE_URL}/products"}'),
    )
    with pytest.raises(ValueError, match="Missing required page environment variable"):
        page_config.load_page_configs("project-a", "catalog", ["products"], environ={})

    monkeypatch.setattr(
        page_config,
        "ArtifactStore",
        lambda project_id: _Store('{"enabled":false}'),
    )
    with pytest.raises(ValueError, match="is disabled"):
        page_config.load_page_configs("project-a", "catalog", ["products"])


def test_page_config_accepts_explicit_locator_strategy():
    config = page_config.PageConfig(
        page_id="login",
        locators={"submit": {"strategy": "role", "value": "button"}},
    )
    assert config.locators["submit"]["strategy"] == "role"

    with pytest.raises(ValueError, match="unsupported strategy"):
        page_config.PageConfig(
            page_id="login",
            locators={"submit": {"strategy": "regex", "value": "submit"}},
        )

    plan = page_config.PageExecutionPlan(
        wait_for=["submit"],
        actions=[{"action": "fill", "target": "search", "value": "hello"}],
    )
    assert plan.actions[0].action == "fill"

    with pytest.raises(ValueError, match="requires target"):
        page_config.PageExecutionPlan(actions=[{"action": "click"}])
