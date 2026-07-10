"""Extensions -- 可选的行为增强，被动监听 Engine 生命周期。

Extensions 不影响 Engine 完成一次正常执行。
"""

from alice_engine.extensions.audit import AuditExtension
from alice_engine.extensions.complexity import ComplexityExtension
from alice_engine.extensions.knowledge import KnowledgeExtension
from alice_engine.extensions.memory import MemoryExtension
from alice_engine.extensions.diff import extract_diff
from alice_engine.extensions.monitor import OnlineMonitor, RunMetrics
from alice_engine.extensions.cost import CostAuditor
from alice_engine.extensions.review import (
    RuleConfig,
    FileBundler,
    PositionVerifier,
    ReviewRule,
    ReviewBundle,
    ReviewIssue,
    ReviewResult,
)

__all__ = [
    "AuditExtension",
    "ComplexityExtension",
    "KnowledgeExtension",
    "MemoryExtension",
    "extract_diff",
    "OnlineMonitor",
    "RunMetrics",
    "CostAuditor",
    "RuleConfig",
    "FileBundler",
    "PositionVerifier",
    "ReviewRule",
    "ReviewBundle",
    "ReviewIssue",
    "ReviewResult",
]
