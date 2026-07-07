"""Backward-compatible skill executor entrypoint for legacy imports/tests."""

from __future__ import annotations

from pathlib import Path

from alice_engine.behavior import resolve_governance_pack_path
from alice_engine.core.agent_definitions import AgentDefinitions, FALLBACK_AGENT_SKILL_MAP
from alice_engine.core.skill_executor_impl import SkillExecutorImpl
from alice_engine.core.skill_loader import SkillLoader
from alice_engine.providers.base import LLMResponse
from alice_engine.providers import get_provider

_defs: AgentDefinitions | None = None
_FALLBACK_AGENT_SKILL_MAP = FALLBACK_AGENT_SKILL_MAP.copy()
DEV_AGENT_SKILL_MAP: dict[str, list[str]] = {}


def _get_governance_root() -> Path:
    root = resolve_governance_pack_path(project_root=Path.cwd())
    if root is None:
        root = Path(__file__).resolve().parents[2] / "packages" / "alice-engine" / "alice_engine" / "governance_default"
    return root


def _get_defs() -> AgentDefinitions:
    global _defs
    if _defs is None:
        _defs = AgentDefinitions(governance_path=_get_governance_root())
    return _defs


def _load_agent_definitions() -> dict[str, dict]:
    return _get_defs()._load_definitions()


def _load_dev_agent_definitions() -> dict[str, dict]:
    return {}


def _get_all_definitions() -> dict[str, dict]:
    definitions = dict(_load_agent_definitions())
    definitions.update(_load_dev_agent_definitions())
    return definitions


AGENT_SKILL_MAP: dict[str, list[str]] = _get_defs()._load_skill_map() or _FALLBACK_AGENT_SKILL_MAP.copy()
_ALL_SKILL_MAP: dict[str, list[str]] = {**AGENT_SKILL_MAP, **DEV_AGENT_SKILL_MAP}


def get_agent_definition(agent_name: str) -> dict:
    return _get_defs().get_definition(agent_name)


def run_skill(skill_id: str, user_input: str, provider=None, context_vars=None, **kwargs):
    loader = SkillLoader(governance_path=_get_governance_root())
    try:
        llm = get_provider(provider or "mock")
    except Exception:
        llm = get_provider("mock")
    executor = SkillExecutorImpl(skill_loader=loader, provider=llm)
    response = executor.execute(skill_id, user_input, context_vars=context_vars, **kwargs)
    if getattr(response, "finish_reason", "") == "error" and "LLM 调用失败" in getattr(response, "content", ""):
        response = LLMResponse(
            content=response.content.replace("[LLM 调用失败]", "[Provider 初始化失败]"),
            tool_calls=list(getattr(response, "tool_calls", []) or []),
            usage=dict(getattr(response, "usage", {}) or getattr(response, "token_usage", {}) or {}),
            model=getattr(response, "model", "none"),
            finish_reason="error",
            latency_ms=getattr(response, "latency_ms", 0),
        )
    return response
