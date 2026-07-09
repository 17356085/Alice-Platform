from __future__ import annotations

from alice_engine.core.runtime_lifecycle import ProviderRuntimeLifecycle


class _WindowMonitor:
    def __init__(self, *, model):
        self.model = model


def test_provider_runtime_lifecycle_resolves_tier_and_overrides_provider():
    reliable_calls: list[tuple] = []

    lifecycle = ProviderRuntimeLifecycle(
        agent_name="automation-agent",
        log_fn=lambda _msg: None,
        resolve_agent_definition_fn=lambda _agent: {"model_tier": "max"},
        resolve_model_for_tier_fn=lambda tier, provider: {"model": "max-model", "provider": "deepseek"},
        resolve_provider_model_fn=lambda provider: {"deepseek": "deepseek-default"}.get(provider, "default-model"),
        get_reliable_provider_fn=lambda **kwargs: reliable_calls.append(kwargs) or {"provider": kwargs["primary"]},
        context_window_monitor_cls=_WindowMonitor,
    )

    result = lifecycle.initialize(
        provider="anthropic",
        requested_model=None,
        use_reliable_provider=True,
        use_window_monitor=True,
    )

    assert result["model_tier"] == "max"
    assert result["provider"] == "deepseek"
    assert result["model"] == "max-model"
    assert result["reliable_provider"] == {"provider": "deepseek"}
    assert result["window_monitor"].model == "max-model"
    assert reliable_calls == [
        {
            "primary": "deepseek",
            "fallback_chain": [{"provider": "deepseek", "model": "max-model"}],
        }
    ]


def test_provider_runtime_lifecycle_can_disable_reliable_and_window():
    lifecycle = ProviderRuntimeLifecycle(
        agent_name="project-agent",
        log_fn=lambda _msg: None,
        resolve_agent_definition_fn=lambda _agent: {"model_tier": "balanced"},
        resolve_model_for_tier_fn=lambda tier, provider: {"model": "fallback-model", "provider": provider},
        resolve_provider_model_fn=lambda provider: "default-model",
    )

    result = lifecycle.initialize(
        provider="mock",
        requested_model="explicit-model",
        use_reliable_provider=False,
        use_window_monitor=False,
    )

    assert result["provider"] == "mock"
    assert result["model"] == "explicit-model"
    assert result["reliable_provider"] is None
    assert result["window_monitor"] is None


def test_provider_runtime_lifecycle_falls_back_to_mock_reliable_provider_on_error():
    calls: list[dict] = []

    def fake_get_reliable_provider(**kwargs):
        calls.append(kwargs)
        if kwargs["primary"] != "mock":
            raise RuntimeError("boom")
        return {"provider": "mock"}

    lifecycle = ProviderRuntimeLifecycle(
        agent_name="project-agent",
        log_fn=lambda _msg: None,
        resolve_agent_definition_fn=lambda _agent: {"model_tier": "balanced"},
        resolve_provider_model_fn=lambda provider: "default-model",
        get_reliable_provider_fn=fake_get_reliable_provider,
        context_window_monitor_cls=_WindowMonitor,
    )

    result = lifecycle.initialize(
        provider="anthropic",
        requested_model="custom-model",
        use_reliable_provider=True,
        use_window_monitor=True,
    )

    assert result["reliable_provider"] == {"provider": "mock"}
    assert result["window_monitor"].model == "custom-model"
    assert calls == [
        {
            "primary": "anthropic",
            "fallback_chain": [{"provider": "anthropic", "model": "custom-model"}],
        },
        {
            "primary": "mock",
        },
    ]


def test_provider_runtime_lifecycle_logs_and_falls_back_when_required_dependencies_missing():
    logs: list[str] = []
    lifecycle = ProviderRuntimeLifecycle(
        agent_name="project-agent",
        log_fn=logs.append,
        resolve_provider_model_fn=lambda provider: "default-model",
    )

    result = lifecycle.initialize(
        provider="anthropic",
        requested_model=None,
        use_reliable_provider=False,
        use_window_monitor=False,
    )

    assert result["model_tier"] == "balanced"
    assert result["provider"] == "anthropic"
    assert result["model"] is None
    assert any("resolve_agent_definition_fn is required" in item for item in logs)
