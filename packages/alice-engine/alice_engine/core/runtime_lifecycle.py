"""Internal lifecycle collaborators for AgentLoop runtime services."""

from __future__ import annotations

import asyncio
from typing import Any, Callable


class ProviderRuntimeLifecycle:
    """Own provider/model/reliability/window initialization outside AgentLoop."""

    def __init__(
        self,
        *,
        agent_name: str,
        log_fn: Callable[[str], None],
        resolve_agent_definition_fn: Callable[[str], dict[str, Any]] | None = None,
        resolve_model_for_tier_fn: Callable[[str, str], dict[str, str]] | None = None,
        resolve_provider_model_fn: Callable[[str], str] | None = None,
        get_reliable_provider_fn: Callable[..., Any] | None = None,
        context_window_monitor_cls: type | None = None,
    ) -> None:
        self.agent_name = agent_name
        self._log = log_fn
        self._resolve_agent_definition_fn = resolve_agent_definition_fn
        self._resolve_model_for_tier_fn = resolve_model_for_tier_fn
        self._resolve_provider_model_fn = resolve_provider_model_fn
        self._get_reliable_provider_fn = get_reliable_provider_fn
        self._context_window_monitor_cls = context_window_monitor_cls

    def initialize(
        self,
        *,
        provider: str,
        requested_model: str | None,
        use_reliable_provider: bool,
        use_window_monitor: bool,
    ) -> dict[str, Any]:
        model_tier = "balanced"
        try:
            resolve_agent_definition = self._require(
                self._resolve_agent_definition_fn,
                "resolve_agent_definition_fn",
            )
            agent_def = resolve_agent_definition(self.agent_name)
            model_tier = agent_def.get("model_tier", "balanced")
        except Exception as exc:
            self._log(f"[warn] model_tier fallback: {exc}")

        resolved_provider = provider
        resolved_model = requested_model
        if resolved_model is None:
            resolve_model_for_tier = self._resolve_model_for_tier_fn
            if resolve_model_for_tier is None:
                self._log("[warn] resolve_model_for_tier_fn missing; keep provider/model fallback")
            else:
                tier_cfg = resolve_model_for_tier(model_tier, resolved_provider)
                resolved_model = tier_cfg["model"]
                resolved_provider = tier_cfg["provider"]

        reliable_provider = None
        if use_reliable_provider:
            resolve_provider_model = self._require(
                self._resolve_provider_model_fn,
                "resolve_provider_model_fn",
            )
            get_reliable_provider = self._get_reliable_provider_fn
            if get_reliable_provider is None:
                from alice_engine.runtime.core.retry import get_reliable_provider as _get_reliable_provider

                get_reliable_provider = _get_reliable_provider
            chain_override = None
            if resolved_model and resolved_model != resolve_provider_model(resolved_provider):
                chain_override = [{"provider": resolved_provider, "model": resolved_model}]
            try:
                reliable_provider = get_reliable_provider(
                    primary=resolved_provider,
                    fallback_chain=chain_override,
                )
            except Exception as exc:
                reliable_provider = get_reliable_provider(primary="mock")
                self._log(f"[warn] reliable provider disabled: {exc}")

        window_monitor = None
        if use_window_monitor:
            context_window_monitor_cls = self._context_window_monitor_cls
            if context_window_monitor_cls is None:
                from alice_engine.runtime.core.context_window import ContextWindowMonitor

                context_window_monitor_cls = ContextWindowMonitor
            resolved_window_model = resolved_model
            if resolved_window_model is None:
                resolve_provider_model = self._require(
                    self._resolve_provider_model_fn,
                    "resolve_provider_model_fn",
                )
                resolved_window_model = resolve_provider_model(resolved_provider)
            window_monitor = context_window_monitor_cls(model=resolved_window_model)

        return {
            "provider": resolved_provider,
            "model": resolved_model,
            "model_tier": model_tier,
            "reliable_provider": reliable_provider,
            "window_monitor": window_monitor,
        }

    @staticmethod
    def _require(value: Any, name: str):
        if value is None:
            raise RuntimeError(f"{name} is required")
        return value


class MCPClientLifecycle:
    """Own MCP client connect/close behavior outside AgentLoop."""

    def __init__(
        self,
        *,
        agent_name: str,
        log_fn: Callable[[str], None],
        create_clients_fn: Callable[[str], tuple[list[Any], dict[str, Any]]] | None = None,
    ) -> None:
        self.agent_name = agent_name
        self._log = log_fn
        self._create_clients_fn = create_clients_fn

    def connect(self) -> tuple[list[Any], dict[str, Any]]:
        try:
            create_clients = self._create_clients_fn
            if create_clients is None:
                from alice_engine.platform_bridge import create_mcp_clients_for_agent

                create_clients = create_mcp_clients_for_agent
            clients, tools = create_clients(self.agent_name)
            return clients or [], tools or {}
        except Exception as exc:
            self._log(f"[warn] MCP init skipped: {exc}")
            return [], {}

    def close_all(self, clients: list[Any]) -> None:
        for client in clients:
            try:
                if hasattr(client, "close"):
                    close_result = client.close()
                    if asyncio.iscoroutine(close_result):
                        asyncio.run(close_result)
            except Exception:
                pass
        clients.clear()


class ReplayStepSink:
    """Own replay step begin/record/finalize behavior outside AgentLoop."""

    def __init__(
        self,
        *,
        recorder: Any,
    ) -> None:
        self.recorder = recorder

    def begin_skill_step(
        self,
        *,
        skill_id: str,
        skill_index: int,
        module: str,
        page: str,
        agent_name: str,
    ) -> Any | None:
        if self.recorder is None:
            return None
        try:
            return self.recorder.begin_step(
                "skill",
                skill_id,
                input_data={
                    "module": module,
                    "page": page,
                    "agent": agent_name,
                },
                metadata={"skill_index": skill_index},
            )
        except Exception:
            return None

    def record_skill_response(
        self,
        *,
        replay_step: Any | None,
        response: Any,
        provider: str,
    ) -> None:
        if replay_step is None or self.recorder is None:
            return
        try:
            self.recorder.record_llm_call(
                replay_step.id,
                getattr(response, "model", ""),
                provider,
                [],
                response.content or "",
                usage=getattr(response, "usage", {}) or {},
            )
            self.recorder.end_step(
                replay_step.id,
                output_data={
                    "finish_reason": response.finish_reason,
                    "tool_calls": getattr(response, "tool_calls", []) or [],
                    "tool_results": getattr(response, "tool_results", []) or [],
                },
                status="error" if response.finish_reason == "error" else "success",
                error_message=(response.content[:200] if response.finish_reason == "error" else ""),
            )
        except Exception:
            pass
