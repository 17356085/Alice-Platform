"""Runtime — Engine 运行时能力。

三层架构:
  - Core Runtime: 执行基础 (Retry, Checkpoint, Security, ContextWindow)
  - Intelligence Runtime: 智能能力 (Knowledge, Memory)
  - Observability Runtime: 可观测性 (Safety, FailureAttributor)
"""

# Core Runtime
from alice_engine.runtime.core.retry import ReliableProvider, get_reliable_provider, UsageTracker  # noqa: F401
from alice_engine.runtime.core.checkpoint import CheckpointManager  # noqa: F401
from alice_engine.runtime.core.security import PromptInjectionGuard  # noqa: F401
from alice_engine.runtime.core.context_window import ContextWindowMonitor, SessionCompactor  # noqa: F401
from alice_engine.runtime.core.circuit_breaker import CircuitBreaker  # noqa: F401

# Intelligence Runtime
from alice_engine.runtime.intelligence.knowledge import (  # noqa: F401
    KnowledgeStore, KnowledgeItem, InMemoryKnowledgeStore,
)
from alice_engine.runtime.intelligence.memory import (  # noqa: F401
    MemoryStore, MemoryRecord, InMemoryMemoryStore, FileMemoryStore,
)

# Observability Runtime
from alice_engine.runtime.observability.safety_auditor import check_output_safety, SafetyFlag  # noqa: F401
from alice_engine.runtime.observability.failure_attributor import attribute_failure, FailureCategory  # noqa: F401

__all__ = [
    # Core Runtime
    "ReliableProvider",
    "get_reliable_provider",
    "UsageTracker",
    "CheckpointManager",
    "PromptInjectionGuard",
    "ContextWindowMonitor",
    "SessionCompactor",
    "CircuitBreaker",
    # Intelligence Runtime
    "KnowledgeStore",
    "KnowledgeItem",
    "InMemoryKnowledgeStore",
    "MemoryStore",
    "MemoryRecord",
    "InMemoryMemoryStore",
    "FileMemoryStore",
    # Observability Runtime
    "check_output_safety",
    "SafetyFlag",
    "attribute_failure",
    "FailureCategory",
]
