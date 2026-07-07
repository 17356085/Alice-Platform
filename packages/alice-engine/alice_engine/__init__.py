"""Alice Engine — AI 测试自动化 SDK。

三层架构 (ADR-002):
  - Runtime Capability: Engine 主动调用，参与控制流
  - Extension: 被动监听，不影响执行

快速开始:
    from alice_engine import Engine, Project
    from alice_engine.runtime import InMemoryKnowledgeStore, InMemoryMemoryStore

    project = Project("./my-project")
    engine = Engine(
        project=project,
        knowledge=InMemoryKnowledgeStore(),
        memory=InMemoryMemoryStore(),
    )
    result = engine.run("equipment", pages=["alarm-config"])
"""

from importlib import import_module
from typing import Any

__version__ = "1.0.0"

_LAZY_EXPORTS = {
    # 核心
    "Engine": ("alice_engine.engine", "Engine"),
    "RunResult": ("alice_engine.engine", "RunResult"),
    "Project": ("alice_engine.project", "Project"),
    "ProjectConfig": ("alice_engine.project", "ProjectConfig"),
    "ValidationResult": ("alice_engine.project", "ValidationResult"),
    # 行为包
    "BehaviorPack": ("alice_engine.behavior", "BehaviorPack"),
    "load_behavior_pack": ("alice_engine.behavior", "load_behavior_pack"),
    # Router + Compiler
    "GovernanceRouter": ("alice_engine.router", "GovernanceRouter"),
    "ResolvedSkill": ("alice_engine.router", "ResolvedSkill"),
    "ResolvedAgent": ("alice_engine.router", "ResolvedAgent"),
    "GovernanceCompiler": ("alice_engine.compiler", "GovernanceCompiler"),
    "ExecutionGraph": ("alice_engine.compiler", "ExecutionGraph"),
    "PhaseBinding": ("alice_engine.compiler", "PhaseBinding"),
    "DriftDetector": ("alice_engine.drift_detector", "DriftDetector"),
    "DriftReport": ("alice_engine.drift_detector", "DriftReport"),
    # 事件
    "EventBus": ("alice_engine.events", "EventBus"),
    "ExecutionContext": ("alice_engine.contracts", "ExecutionContext"),
    "ExecutionResult": ("alice_engine.contracts", "ExecutionResult"),
    "ExecutionKernel": ("alice_engine.kernel", "ExecutionKernel"),
    "InlineExecutionKernel": ("alice_engine.kernel", "InlineExecutionKernel"),
    "KernelExecutionRequest": ("alice_engine.kernel", "KernelExecutionRequest"),
    "KernelExecutionResult": ("alice_engine.kernel", "KernelExecutionResult"),
    "KernelKind": ("alice_engine.kernel", "KernelKind"),
    "RuntimeExecutionKernel": ("alice_engine.kernel", "RuntimeExecutionKernel"),
    "SOPGraphExecutionKernel": ("alice_engine.kernel", "SOPGraphExecutionKernel"),
    # Runtime Capabilities
    "KnowledgeItem": ("alice_engine.runtime", "KnowledgeItem"),
    "KnowledgeStore": ("alice_engine.runtime", "KnowledgeStore"),
    "InMemoryKnowledgeStore": ("alice_engine.runtime", "InMemoryKnowledgeStore"),
    "MemoryRecord": ("alice_engine.runtime", "MemoryRecord"),
    "MemoryStore": ("alice_engine.runtime", "MemoryStore"),
    "InMemoryMemoryStore": ("alice_engine.runtime", "InMemoryMemoryStore"),
    # Discovery
    "PageDiscoverer": ("alice_engine.discovery", "PageDiscoverer"),
    "PageStructure": ("alice_engine.discovery", "PageStructure"),
    "ComponentInfo": ("alice_engine.discovery", "ComponentInfo"),
    "RouteInfo": ("alice_engine.discovery", "RouteInfo"),
    # Extensions
    "EngineExtension": ("alice_engine.extension", "EngineExtension"),
    "AuditExtension": ("alice_engine.extensions", "AuditExtension"),
    "ComplexityExtension": ("alice_engine.extensions", "ComplexityExtension"),
    # Provider
    "LLMProvider": ("alice_engine.providers", "LLMProvider"),
    "LLMResponse": ("alice_engine.providers", "LLMResponse"),
    "MockProvider": ("alice_engine.providers", "MockProvider"),
    "get_provider": ("alice_engine.providers", "get_provider"),
    "list_providers": ("alice_engine.providers", "list_providers"),
    "register_provider": ("alice_engine.providers", "register_provider"),
    # 接口 (Protocol)
    "PathResolver": ("alice_engine.core.interfaces", "PathResolver"),
    "EventEmitter": ("alice_engine.core.interfaces", "EventEmitter"),
    "Logger": ("alice_engine.core.interfaces", "Logger"),
    "LLMProviderProtocol": ("alice_engine.core.interfaces", "LLMProviderProtocol"),
    "ContextInjector": ("alice_engine.core.interfaces", "ContextInjector"),
    # 默认实现
    "SimplePathResolver": ("alice_engine.core.interfaces", "SimplePathResolver"),
    "SimpleLogger": ("alice_engine.core.interfaces", "SimpleLogger"),
    "NullEventEmitter": ("alice_engine.core.interfaces", "NullEventEmitter"),
    "NullContextInjector": ("alice_engine.core.interfaces", "NullContextInjector"),
    # 异常
    "AliceError": ("alice_engine.exceptions", "AliceError"),
    "ConfigError": ("alice_engine.exceptions", "ConfigError"),
    "ExecutionError": ("alice_engine.exceptions", "ExecutionError"),
    "ExtensionError": ("alice_engine.exceptions", "ExtensionError"),
    "LLMProviderError": ("alice_engine.exceptions", "LLMProviderError"),
    "ModuleNotFoundError": ("alice_engine.exceptions", "ModuleNotFoundError"),
    "ProjectNotFoundError": ("alice_engine.exceptions", "ProjectNotFoundError"),
}


def __getattr__(name: str) -> Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module 'alice_engine' has no attribute {name!r}")
    module_name, attr_name = _LAZY_EXPORTS[name]
    module = import_module(module_name)
    return getattr(module, attr_name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_EXPORTS))


__all__ = [
    # 核心
    "Engine",
    "Project",
    "RunResult",
    "ValidationResult",
    # 行为包
    "BehaviorPack",
    "load_behavior_pack",
    # Router + Compiler
    "GovernanceRouter",
    "ResolvedSkill",
    "ResolvedAgent",
    "GovernanceCompiler",
    "ExecutionGraph",
    "PhaseBinding",
    "DriftDetector",
    "DriftReport",
    # 配置
    "ProjectConfig",
    # 事件
    "EventBus",
    "ExecutionContext",
    "ExecutionResult",
    "ExecutionKernel",
    "InlineExecutionKernel",
    "KernelExecutionRequest",
    "KernelExecutionResult",
    "KernelKind",
    "RuntimeExecutionKernel",
    "SOPGraphExecutionKernel",
    # Runtime Capabilities
    "KnowledgeItem",
    "KnowledgeStore",
    "InMemoryKnowledgeStore",
    "MemoryRecord",
    "MemoryStore",
    "InMemoryMemoryStore",
    # Discovery
    "PageDiscoverer",
    "PageStructure",
    "ComponentInfo",
    "RouteInfo",
    # Extensions
    "EngineExtension",
    "AuditExtension",
    "ComplexityExtension",
    # Provider
    "LLMProvider",
    "LLMResponse",
    "MockProvider",
    "get_provider",
    "list_providers",
    "register_provider",
    # 接口 (Protocol)
    "PathResolver",
    "EventEmitter",
    "Logger",
    "LLMProviderProtocol",
    "ContextInjector",
    # 默认实现
    "SimplePathResolver",
    "SimpleLogger",
    "NullEventEmitter",
    "NullContextInjector",
    # 异常
    "AliceError",
    "ConfigError",
    "ExecutionError",
    "ExtensionError",
    "LLMProviderError",
    "ModuleNotFoundError",
    "ProjectNotFoundError",
]
