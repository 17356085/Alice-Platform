"""
Engine Extensions — 向后兼容层，re-export SDK Extensions。

推荐直接使用 SDK 导入：
    from alice_engine import AuditExtension, ComplexityExtension
    from alice_engine.extensions import KnowledgeExtension, MemoryExtension

可用 Extensions:
  - AuditExtension:       状态漂移 + SOP 合规审计
  - ComplexityExtension:  按复杂度选择 SOP 流水线
  - KnowledgeExtension:   跨 Run 知识复用
  - MemoryExtension:      执行历史记忆
"""

# 从 SDK 导入（向后兼容）
from alice_engine import AuditExtension, ComplexityExtension
from alice_engine.extensions import KnowledgeExtension, MemoryExtension

__all__ = [
    "AuditExtension",
    "ComplexityExtension",
    "KnowledgeExtension",
    "MemoryExtension",
]
