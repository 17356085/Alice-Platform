"""核心接口 — 5 个抽象接口解耦 6000 行代码。

这些接口由 SDK 定义，平台层实现。Engine 通过接口调用平台能力，
不直接依赖平台模块。

用法:
    from alice_engine.core.interfaces import (
        PathResolver, EventEmitter, Logger, LLMProviderProtocol, ContextInjector
    )
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


# ═══════════════════════════════════════════════════════════
#  1. PathResolver — 路径解析
# ═══════════════════════════════════════════════════════════

@runtime_checkable
class PathResolver(Protocol):
    """路径解析接口。

    平台层实现此接口，提供项目路径、行为包路径等解析能力。
    SDK 通过此接口获取文件路径，不直接依赖平台路径模块。

    用法:
        class MyPathResolver:
            def get_workstudy(self) -> Path:
                return Path("./my-project")
            def get_behavior_path(self) -> Path:
                return self.get_workstudy() / "governance"
    """

    def get_workstudy(self) -> Path:
        """获取工作目录。"""
        ...

    def get_behavior_path(self) -> Path:
        """获取行为包路径（原 get_governance）。"""
        ...

    def get_test_project_root(self) -> Path | None:
        """获取测试项目根目录。"""
        ...

    def get_context_modules(self) -> Path:
        """获取模块上下文目录。"""
        ...

    def get_project_dir(self) -> Path:
        """获取项目目录。"""
        ...


# ═══════════════════════════════════════════════════════════
#  2. EventEmitter — 事件发射
# ═══════════════════════════════════════════════════════════

@runtime_checkable
class EventEmitter(Protocol):
    """事件发射接口。

    SDK 通过此接口发射事件，不直接依赖平台事件总线。

    用法:
        class MyEventEmitter:
            def emit(self, event_type, data, **kwargs):
                print(f"Event: {event_type} {data}")
    """

    def emit(self, event_type: str, data: dict = None, **kwargs) -> None:
        """发射事件。

        Args:
            event_type: 事件类型
            data: 事件数据
            **kwargs: 额外参数 (agent_name, module, page 等)
        """
        ...


# ═══════════════════════════════════════════════════════════
#  3. Logger — 结构化日志
# ═══════════════════════════════════════════════════════════

@runtime_checkable
class Logger(Protocol):
    """结构化日志接口。

    SDK 通过此接口输出日志，不直接依赖平台日志模块。

    用法:
        class MyLogger:
            def info(self, msg, **kwargs):
                print(f"[INFO] {msg}")
            def warning(self, msg, **kwargs):
                print(f"[WARN] {msg}")
            def error(self, msg, **kwargs):
                print(f"[ERROR] {msg}")
    """

    def debug(self, msg: str, **kwargs) -> None:
        """调试日志。"""
        ...

    def info(self, msg: str, **kwargs) -> None:
        """信息日志。"""
        ...

    def warning(self, msg: str, **kwargs) -> None:
        """警告日志。"""
        ...

    def error(self, msg: str, **kwargs) -> None:
        """错误日志。"""
        ...

    def bind(self, **kwargs) -> "Logger":
        """绑定上下文，返回新的 Logger 实例。"""
        ...


class SimpleLogger:
    """简单 Logger 实现 — 用于测试和演示。"""

    def __init__(self, name: str = "alice"):
        self.name = name
        self._bindings: dict = {}

    def debug(self, msg: str, **kwargs) -> None:
        print(f"[{self.name}] DEBUG: {msg}")

    def info(self, msg: str, **kwargs) -> None:
        print(f"[{self.name}] INFO: {msg}")

    def warning(self, msg: str, **kwargs) -> None:
        print(f"[{self.name}] WARN: {msg}")

    def error(self, msg: str, **kwargs) -> None:
        print(f"[{self.name}] ERROR: {msg}")

    def bind(self, **kwargs) -> "SimpleLogger":
        new = SimpleLogger(self.name)
        new._bindings = {**self._bindings, **kwargs}
        return new


# ═══════════════════════════════════════════════════════════
#  4. LLMProvider — LLM 调用
# ═══════════════════════════════════════════════════════════

from alice_engine.providers.base import LLMResponse  # noqa: F401 — canonical definition


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """LLM Provider 接口。

    SDK 通过此接口调用 LLM，不直接依赖平台 Provider 模块。

    用法:
        class MyProvider:
            def complete(self, system_prompt, user_prompt, **kwargs):
                return LLMResponse(content="response")
    """

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> LLMResponse:
        """发送 completion 请求。"""
        ...

    def supports_tools(self) -> bool:
        """是否支持 tool calling。"""
        ...


# ═══════════════════════════════════════════════════════════
#  5. ContextInjector — 上下文注入
# ═══════════════════════════════════════════════════════════

@runtime_checkable
class ContextInjector(Protocol):
    """上下文注入接口。

    SDK 通过此接口注入上下文到 Skill prompt，不直接依赖平台上下文模块。

    用法:
        class MyInjector:
            def inject(self, skill_id, context_vars, prompt):
                return prompt + "\n" + str(context_vars)
    """

    def inject(
        self,
        skill_id: str,
        context_vars: dict,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[str, str]:
        """注入上下文到 prompt。

        Args:
            skill_id: Skill ID
            context_vars: 上下文变量
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            (system_prompt, user_prompt) 注入后的提示词
        """
        ...


# ═══════════════════════════════════════════════════════════
#  默认实现（用于测试和独立运行）
# ═══════════════════════════════════════════════════════════

class SimplePathResolver:
    """简单路径解析器 — 基于工作目录的默认实现。"""

    def __init__(self, workstudy: Path = None):
        self._workstudy = workstudy or Path.cwd()

    def get_workstudy(self) -> Path:
        return self._workstudy

    def get_behavior_path(self) -> Path:
        return self._workstudy / "governance"

    def get_test_project_root(self) -> Path | None:
        return None

    def get_context_modules(self) -> Path:
        return self._workstudy / "governance" / "context" / "modules"

    def get_project_dir(self) -> Path:
        return self._workstudy / "governance" / "context" / "projects"


class NullEventEmitter:
    """空事件发射器 — 不做任何事。"""

    def emit(self, event_type: str, data: dict = None, **kwargs) -> None:
        pass


class NullContextInjector:
    """空上下文注入器 — 直接返回原始 prompt。"""

    def inject(self, skill_id: str, context_vars: dict,
               system_prompt: str, user_prompt: str) -> tuple[str, str]:
        return system_prompt, user_prompt
