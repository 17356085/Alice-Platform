"""Testing Memory — 测试领域记忆系统。

Week 3 Day 3-4: 类型化 Memory schema + ChromaDB CRUD + Signal Observer。

参考:
  - Aperant Memory.md (类型化设计理念)
  - Aperant memory/observer/signals.ts (被动行为信号)
  - AITest 现有 platform/knowledge.py (ChromaDB 基础设施)

8 种 Testing Memory 类型:
  ui_pattern          — UI组件模式 → 测试策略
  locator_history     — 元素定位器成功率 + 失败历史
  business_rule       — 业务规则约束
  known_bug           — 已知缺陷 + workaround
  historical_failure  — 历史失败模式 + 修复策略
  page_dependency     — 页面间依赖关系
  risk_pattern        — 风险识别模式
  workflow_recipe     — 测试工作流配方
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
#  Enums
# ══════════════════════════════════════════════════════════════════════════

class MemoryType(str, Enum):
    UI_PATTERN = "ui_pattern"
    LOCATOR_HISTORY = "locator_history"
    BUSINESS_RULE = "business_rule"
    KNOWN_BUG = "known_bug"
    HISTORICAL_FAILURE = "historical_failure"
    PAGE_DEPENDENCY = "page_dependency"
    RISK_PATTERN = "risk_pattern"
    WORKFLOW_RECIPE = "workflow_recipe"


class Confidence(str, Enum):
    VERIFIED = "verified"        # 多次验证
    OBSERVED_ONCE = "once"       # 单次观察
    INFERRED = "inferred"        # LLM 推断
    MANUAL = "manual"            # 人工标注


class BehaviorSignal(str, Enum):
    """被动行为信号 — 无需 Agent 显式报告。参考 Aperant signals.ts。"""
    LOCATOR_RETRY = "locator_retry"            # 多次尝试不同定位器
    SCRIPT_SYNTAX_FIX = "script_syntax_fix"    # 修复自己生成的代码
    ASSERTION_ADJUST = "assertion_adjust"      # 反复修改断言
    EXCESSIVE_GREP = "excessive_grep"          # 同一 pattern grep >5次
    SKILL_SKIP = "skill_skip"                  # 跳过某个 Skill
    TOOL_ERROR_RETRY = "tool_error_retry"      # 同一 tool >3次失败
    EXCESSIVE_RE_READ = "excessive_re_read"    # 重复读同一文件 >3次
    REDUNDANT_STEP = "redundant_step"          # 执行已完成的工作


# ══════════════════════════════════════════════════════════════════════════
#  Memory Schemas
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class TestingMemory:
    """测试记忆基类。参考 Aperant Memory.md schema 设计。"""
    id: str = ""
    type: MemoryType = MemoryType.UI_PATTERN
    content: str = ""                           # 核心内容 (embedding target)
    module: Optional[str] = None
    page: Optional[str] = None
    confidence: Confidence = Confidence.OBSERVED_ONCE
    source: str = ""                            # skill_id / agent_name
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    decay_factor: float = 1.0
    verify_count: int = 0
    tags: list[str] = field(default_factory=list)

    def to_metadata(self) -> dict:
        return {
            "type": self.type.value,
            "module": self.module or "",
            "page": self.page or "",
            "confidence": self.confidence.value,
            "source": self.source,
            "decay_factor": self.decay_factor,
            "verify_count": self.verify_count,
            "tags": ",".join(self.tags),
        }

    @classmethod
    def from_metadata(cls, content: str, metadata: dict) -> "TestingMemory":
        return cls(
            content=content,
            type=MemoryType(metadata.get("type", "ui_pattern")),
            module=metadata.get("module") or None,
            page=metadata.get("page") or None,
            confidence=Confidence(metadata.get("confidence", "once")),
            source=metadata.get("source", ""),
            decay_factor=float(metadata.get("decay_factor", 1.0)),
            verify_count=int(metadata.get("verify_count", 0)),
            tags=metadata.get("tags", "").split(",") if metadata.get("tags") else [],
        )


@dataclass
class UIPatternMemory(TestingMemory):
    """UI 模式 → 测试策略映射。"""
    component: str = ""              # el-table / el-dialog / el-form / ...
    pattern: str = ""                # table_with_pagination / dialog_with_form / ...
    test_strategy: list[str] = field(default_factory=list)
    locator_hints: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.type = MemoryType.UI_PATTERN


@dataclass
class LocatorHistoryMemory(TestingMemory):
    """元素定位器演变史。"""
    element: str = ""                # 元素描述
    stable_locator: str = ""         # 当前稳定定位器
    failed_locators: list[str] = field(default_factory=list)
    success_rate: float = 0.0

    def __post_init__(self):
        self.type = MemoryType.LOCATOR_HISTORY


@dataclass
class KnownBugMemory(TestingMemory):
    """已知缺陷。"""
    bug_description: str = ""
    workaround: str = ""
    status: str = "open"             # open / fixed / wont_fix
    affected_browsers: list[str] = field(default_factory=list)
    related_test: str = ""

    def __post_init__(self):
        self.type = MemoryType.KNOWN_BUG


@dataclass
class HistoricalFailureMemory(TestingMemory):
    """历史失败模式。"""
    failure_pattern: str = ""
    root_cause: str = ""
    fix_strategy: str = ""
    failure_count: int = 0

    def __post_init__(self):
        self.type = MemoryType.HISTORICAL_FAILURE


# ══════════════════════════════════════════════════════════════════════════
#  Memory Lifecycle
# ══════════════════════════════════════════════════════════════════════════

class MemoryLifecycle:
    """记忆生命周期管理。参考 Aperant trust-gate.ts。"""

    DECAY_RATE = 0.1
    BOOST_RATE = 0.2
    VERIFY_THRESHOLD = 3
    DELETE_THRESHOLD = 0.3

    @staticmethod
    def decay(memory: TestingMemory) -> TestingMemory:
        memory.decay_factor = max(0.1, memory.decay_factor - MemoryLifecycle.DECAY_RATE)
        if memory.decay_factor <= MemoryLifecycle.DELETE_THRESHOLD:
            memory.confidence = Confidence.INFERRED
        return memory

    @staticmethod
    def boost(memory: TestingMemory) -> TestingMemory:
        memory.verify_count += 1
        memory.decay_factor = min(1.0, memory.decay_factor + MemoryLifecycle.BOOST_RATE)
        if memory.verify_count >= MemoryLifecycle.VERIFY_THRESHOLD:
            memory.confidence = Confidence.VERIFIED
        return memory

    @staticmethod
    def should_delete(memory: TestingMemory) -> bool:
        if memory.decay_factor < MemoryLifecycle.DELETE_THRESHOLD:
            return True
        if memory.type == MemoryType.KNOWN_BUG:
            if hasattr(memory, 'status') and getattr(memory, 'status') == "fixed":
                try:
                    age = (datetime.now() - datetime.fromisoformat(memory.updated_at)).days
                    if age > 30:
                        return True
                except Exception:
                    pass
        return False


# ══════════════════════════════════════════════════════════════════════════
#  Signal Observer
# ══════════════════════════════════════════════════════════════════════════

class SignalObserver:
    """信号观察器 — 被动收集行为信号。参考 Aperant memory/observer/signals.ts。"""

    def __init__(self):
        self._buffer: list[dict] = []
        self._tool_call_counts: dict[str, int] = {}
        self._file_read_counts: dict[str, int] = {}
        self._step_count: int = 0

    def on_tool_call(self, tool_name: str, args: dict = None) -> None:
        self._tool_call_counts[tool_name] = self._tool_call_counts.get(tool_name, 0) + 1

    def on_file_read(self, file_path: str) -> None:
        self._file_read_counts[file_path] = self._file_read_counts.get(file_path, 0) + 1
        if self._file_read_counts[file_path] > 3:
            self._emit(BehaviorSignal.EXCESSIVE_RE_READ, {"file": file_path, "count": self._file_read_counts[file_path]})

    def on_skill_complete(self, skill_id: str, output: str) -> None:
        self._step_count += 1
        if len(output) < 100:
            self._emit(BehaviorSignal.SKILL_SKIP, {"skill": skill_id})

    def on_retry(self, skill_id: str, attempt: int) -> None:
        self._emit(BehaviorSignal.TOOL_ERROR_RETRY, {"skill": skill_id, "attempt": attempt})

    def on_locator_change(self, element: str, old: str, new: str) -> None:
        self._emit(BehaviorSignal.LOCATOR_RETRY, {"element": element, "old_locator": old, "new_locator": new})

    def flush(self) -> list[dict]:
        signals = self._buffer.copy()
        self._buffer.clear()
        return signals

    def _emit(self, signal: BehaviorSignal, detail: dict) -> None:
        self._buffer.append({
            "signal": signal.value,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        })
