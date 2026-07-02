"""
Engine Extensions — 可插拔子引擎。

每个 Extension 实现 EngineExtension 协议，在 Engine 生命周期钩子中运行。

可用 Extensions:
  - AuditExtension:       状态漂移 + SOP 合规审计
  - ComplexityExtension:  按复杂度选择 SOP 流水线
  - KnowledgeExtension:   跨 Run 知识复用
  - MemoryExtension:      ChromaDB 向量记忆
"""

from aitest.engine.extensions.audit import AuditExtension
from aitest.engine.extensions.complexity import ComplexityExtension
from aitest.engine.extensions.knowledge import KnowledgeExtension
from aitest.engine.extensions.memory import MemoryExtension

__all__ = [
    "AuditExtension",
    "ComplexityExtension",
    "KnowledgeExtension",
    "MemoryExtension",
]
