"""Typed page configuration loaded by the execution orchestration layer."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aitest.platform.artifacts import ArtifactStore


_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")


class PageAction(BaseModel):
    """One declarative browser action in a page execution plan."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["goto", "click", "fill", "select", "press", "wait_for", "wait", "screenshot"]
    target: str | None = Field(default=None, max_length=512)
    value: str | None = Field(default=None, max_length=4000)
    timeout_ms: int = Field(default=30000, ge=100, le=120000)

    @model_validator(mode="after")
    def validate_requirements(self) -> "PageAction":
        if self.action in {"click", "fill", "select", "press", "wait_for"} and not (self.target or "").strip():
            raise ValueError(f"page action '{self.action}' requires target")
        if self.action in {"fill", "select", "press", "goto"} and self.value is None:
            raise ValueError(f"page action '{self.action}' requires value")
        if self.action == "wait" and self.target:
            raise ValueError("page action 'wait' does not accept target")
        return self


class PageExecutionPlan(BaseModel):
    """Validated, provider-neutral browser orchestration metadata."""

    model_config = ConfigDict(extra="forbid")

    wait_for: list[str] = Field(default_factory=list, max_length=32)
    actions: list[PageAction] = Field(default_factory=list, max_length=64)
    navigation_timeout_ms: int = Field(default=30000, ge=100, le=180000)
    action_timeout_ms: int = Field(default=30000, ge=100, le=120000)
    retry: int = Field(default=0, ge=0, le=3)

    @field_validator("wait_for")
    @classmethod
    def validate_wait_for(cls, value: list[str]) -> list[str]:
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError("wait_for entries must be non-empty locator names")
        return value


class PageConfig(BaseModel):
    """Stable execution-facing shape for a persisted page definition."""

    page_id: str = Field(min_length=1, max_length=128)
    url: str = Field(default="", max_length=2000)
    config: dict[str, Any] = Field(default_factory=dict)
    locators: dict[str, Any] = Field(default_factory=dict)
    execution: PageExecutionPlan = Field(default_factory=PageExecutionPlan)
    enabled: bool = True

    @field_validator("locators")
    @classmethod
    def validate_locators(cls, value: dict[str, Any]) -> dict[str, Any]:
        for name, locator in value.items():
            if not str(name).strip():
                raise ValueError("locator names must not be empty")
            if isinstance(locator, str):
                if not locator.strip():
                    raise ValueError(f"locator '{name}' must not be empty")
                continue
            if not isinstance(locator, dict):
                raise ValueError(f"locator '{name}' must be a string or object")
            strategy = locator.get("strategy", "css")
            target = locator.get("value")
            if strategy not in {"css", "xpath", "text", "role", "testid", "id", "name", "link_text"}:
                raise ValueError(f"locator '{name}' has unsupported strategy '{strategy}'")
            if not isinstance(target, str) or not target.strip():
                raise ValueError(f"locator '{name}' requires a non-empty value")
        return value

    @classmethod
    def from_payload(cls, page_id: str, payload: Mapping[str, Any] | None) -> "PageConfig":
        raw = dict(payload or {})
        execution = raw.get("execution", {})
        if execution is None:
            execution = {}
        if not isinstance(execution, dict):
            raise ValueError("page execution must be a JSON object")
        return cls(
            page_id=page_id,
            url=str(raw.get("url", "") or ""),
            config=raw.get("config") if isinstance(raw.get("config"), dict) else {},
            locators=raw.get("locators") if isinstance(raw.get("locators"), dict) else {},
            execution=execution,
            enabled=bool(raw.get("enabled", True)),
        )

    def resolved(self, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
        """Resolve `${NAME}` / `${NAME:-fallback}` without mutating stored JSON."""
        env = environ or os.environ
        return {
            "page_id": self.page_id,
            "url": _resolve_value(self.url, env),
            "config": _resolve_value(self.config, env),
            "locators": _resolve_value(self.locators, env),
            "execution": _resolve_value(self.execution.model_dump(mode="json"), env),
            "enabled": self.enabled,
        }


def _resolve_value(value: Any, environ: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            name, fallback = match.group(1), match.group(2)
            if name in environ:
                return str(environ[name])
            if fallback is not None:
                return fallback
            raise ValueError(f"Missing required page environment variable: {name}")

        return _ENV_PATTERN.sub(replace, value)
    if isinstance(value, list):
        return [_resolve_value(item, environ) for item in value]
    if isinstance(value, dict):
        return {str(key): _resolve_value(item, environ) for key, item in value.items()}
    return value


def load_page_configs(
    project_id: str,
    module: str,
    pages: list[str],
    *,
    environ: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Load and resolve persisted page configs for an execution request.

    Missing legacy page.json files intentionally produce a backwards-compatible
    default config. Persisted disabled pages are rejected before a run starts.
    """
    store = ArtifactStore(project_id.strip() or "web-automation")
    result: list[dict[str, Any]] = []
    for page_id in pages:
        raw = store.read(module, "pages", page_id, "page.json")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid page configuration for '{module}/{page_id}': {exc}") from exc
        config = PageConfig.from_payload(page_id, payload)
        if not config.enabled:
            raise ValueError(f"Page '{module}/{page_id}' is disabled")
        result.append(config.resolved(environ))
    return result


__all__ = ["PageAction", "PageExecutionPlan", "PageConfig", "load_page_configs"]
