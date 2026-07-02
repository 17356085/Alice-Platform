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

from alice_engine.engine import Engine, RunResult
from alice_engine.project import Project, ProjectConfig, ValidationResult
from alice_engine.behavior import BehaviorPack, load_behavior_pack
from alice_engine.router import GovernanceRouter, ResolvedSkill, ResolvedAgent
from alice_engine.compiler import GovernanceCompiler, ExecutionGraph, PhaseBinding
from alice_engine.drift_detector import DriftDetector, DriftReport
from alice_engine.events import EventBus
from alice_engine.extension import EngineExtension
from alice_engine.extensions import AuditExtension, ComplexityExtension
from alice_engine.runtime import (
    KnowledgeItem,
    KnowledgeStore,
    InMemoryKnowledgeStore,
    MemoryRecord,
    MemoryStore,
    InMemoryMemoryStore,
)
from alice_engine.exceptions import (
    AliceError,
    ConfigError,
    ExecutionError,
    ExtensionError,
    LLMProviderError,
    ModuleNotFoundError,
    ProjectNotFoundError,
)
from alice_engine.providers import (
    LLMProvider,
    LLMResponse,
    MockProvider,
    get_provider,
    list_providers,
    register_provider,
)
from alice_engine.discovery import (
    PageDiscoverer,
    PageStructure,
    ComponentInfo,
    RouteInfo,
)

__version__ = "0.3.0"

__all__ = [
    # 核心
    "Engine",
    "Project",
    "RunResult",
    "ValidationResult",
    # 行为包
    "BehaviorPack",
    "load_behavior_pack",
    # Router
    "GovernanceRouter",
    "ResolvedSkill",
    "ResolvedAgent",
    # 配置
    "ProjectConfig",
    # 事件
    "EventBus",
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
    # 异常
    "AliceError",
    "ConfigError",
    "ExecutionError",
    "ExtensionError",
    "LLMProviderError",
    "ModuleNotFoundError",
    "ProjectNotFoundError",
]
