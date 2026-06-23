# Testing Memory — 测试领域记忆系统

> 参考: Aperant `Memory.md` (84KB 蓝图 — 设计理念 + 类型化 Memory + 行为信号)
>       + `memory/injection/` (active injection) + `memory/retrieval/` (multi-modal retrieval)
> 适配: AITest 测试领域 — Schema 完全重设计，理念借鉴
> 状态: v1.0-draft | 优先级: P2

## 1. 设计理念

### 1.1 为什么不照搬 Aperant Memory

Aperant Memory 记录的是代码领域的事：
```
- Gotcha: "这个库的 v3 版本改了 API"
- Decision: "选用 Zustand 而非 Redux"
- Pattern: "IPC handler 的注册模式"
- Workflow Recipe: "添加新 Agent 类型的步骤"
```

AITest 需要的是测试领域的事：
```
- UI Pattern → Test Pattern 映射
- Locator 历史（哪个定位器容易失败）
- Business Rule（业务约束）
- Known Bug（已知缺陷 + workaround）
- Historical Failure（历史失败模式）
- Page Dependency（页面间依赖关系）
- Risk Pattern（风险识别模式）
```

### 1.2 Aperant 中值得借鉴的理念

| 理念 | Aperant 做法 | AITest 采纳 |
|------|-------------|------------|
| 类型化 Memory | 25+ memory type 各司其职 | 定义 8 类 TestingMemory |
| 行为信号 | 17 个被动观察信号 (共访问、错误重试等) | 6 个测试专用信号 |
| 注入分层 | 系统提示(500ms)→初始消息(2s)→工具结果(<100ms)→prepareStep(<50ms) | 保留分层设计 |
| 检索融合 | BM25 + 向量 + 图邻域提升 → RRF 融合 | 当前 ChromaDB + BM25 即可 |
| 来源追踪 | 每条记录带出处 + 衰减 | 采纳 |

## 2. Testing Memory Schema

### 2.1 Memory 类型定义

```python
# platform/knowledge/testing_memory.py

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    """测试领域 Memory 类型。"""
    UI_PATTERN = "ui_pattern"              # UI 模式 → 测试策略
    LOCATOR_HISTORY = "locator_history"     # 元素定位器演变史
    BUSINESS_RULE = "business_rule"         # 业务规则约束
    KNOWN_BUG = "known_bug"                # 已知缺陷
    HISTORICAL_FAILURE = "historical_failure"  # 历史失败模式
    PAGE_DEPENDENCY = "page_dependency"     # 页面间依赖
    RISK_PATTERN = "risk_pattern"          # 风险识别模式
    WORKFLOW_RECIPE = "workflow_recipe"    # 测试工作流配方


class Confidence(str, Enum):
    """信息可信度。"""
    VERIFIED = "verified"      # 多次验证过的
    OBSERVED_ONCE = "once"     # 观察到一次
    INFERRED = "inferred"      # LLM 推断的
    MANUAL = "manual"          # 人工标注的


@dataclass
class TestingMemory:
    """测试记忆条目基类。

    参考 Aperant Memory.md 的 Memory type schema 设计理念。
    """
    id: str                              # 唯一标识
    type: MemoryType                     # 记忆类型
    content: str                         # 核心内容
    module: Optional[str] = None         # 所属模块
    page: Optional[str] = None           # 所属页面
    confidence: Confidence = Confidence.OBSERVED_ONCE
    source: str = ""                     # 来源 (skill_id / agent_name)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    decay_factor: float = 1.0           # 衰减因子 (每次未确认 -0.1)
    verify_count: int = 0               # 验证次数
    tags: list[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════
#  各类 Memory 的专用字段
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class UIPatternMemory(TestingMemory):
    """UI 模式 → 测试策略映射。

    Example:
        UIPatternMemory(
            type=MemoryType.UI_PATTERN,
            component="el-table",
            pattern="table_with_pagination_and_search",
            test_strategy=[
                "test_pagination_navigation",
                "test_search_filter",
                "test_column_sort",
                "test_batch_operations",
            ],
            locator_hints={
                "search_input": "input[placeholder*='搜索']",
                "table_rows": ".el-table__body-wrapper tbody tr",
                "pagination": ".el-pagination",
            }
        )
    """
    component: str = ""                  # 组件类型 (el-table / el-dialog / ...)
    pattern: str = ""                    # 使用模式
    test_strategy: list[str] = field(default_factory=list)  # 对应的测试策略
    locator_hints: dict[str, str] = field(default_factory=dict)  # 定位器提示
    related_pages: list[str] = field(default_factory=list)  # 使用此模式的其他页面


@dataclass
class LocatorHistoryMemory(TestingMemory):
    """元素定位器演变史。

    Example:
        LocatorHistoryMemory(
            element="确认按钮",
            stable_locator="button.el-button--primary:has-text('确 定')",
            failed_locators=[
                "//span[text()='确 定']",       # 空格导致失败
                ".confirm-btn",                   # class 名变更
            ],
            success_rate=0.85,
        )
    """
    element: str = ""                    # 元素描述
    stable_locator: str = ""             # 当前稳定的定位器
    failed_locators: list[str] = field(default_factory=list)  # 历史失败定位器
    success_rate: float = 0.0           # 成功定位率
    workaround: str = ""                # 备选方案


@dataclass
class BusinessRuleMemory(TestingMemory):
    """业务规则约束。

    Example:
        BusinessRuleMemory(
            rule="工厂代码在审批后不可修改",
            scope="multiple_modules",
            affected_fields=["factory_code"],
            constraint_type="immutable_after_approval",
        )
    """
    rule: str = ""                       # 业务规则描述
    scope: str = "page"                  # 作用范围: page / module / global
    affected_fields: list[str] = field(default_factory=list)
    constraint_type: str = ""            # 约束类型


@dataclass
class KnownBugMemory(TestingMemory):
    """已知缺陷 + workaround。

    Example:
        KnownBugMemory(
            bug_description="IE11 下 el-select 不触发 change 事件",
            workaround="click 选项后手动 dispatch Event('change')",
            status="open",
            affected_browsers=["IE11"],
            related_test="test_edit_record",
        )
    """
    bug_description: str = ""
    workaround: str = ""
    status: str = "open"                 # open / fixed / wont_fix
    affected_browsers: list[str] = field(default_factory=list)
    related_test: str = ""


@dataclass
class HistoricalFailureMemory(TestingMemory):
    """历史失败模式。

    Example:
        HistoricalFailureMemory(
            failure_pattern="确认对话框按钮文本动态变化",
            root_cause="审批流状态不同 → 按钮文本不同 ('通过'/'驳回'/'确认')",
            fix_strategy="使用 data-testid 或按钮位置而非文本定位",
            failure_count=3,
        )
    """
    failure_pattern: str = ""
    root_cause: str = ""
    fix_strategy: str = ""
    failure_count: int = 0


@dataclass
class PageDependencyMemory(TestingMemory):
    """页面间依赖关系。

    Example:
        PageDependencyMemory(
            depends_on=["device-type"],   # 设备台账依赖设备类型
            dependency_type="data",        # 数据依赖 (需要先创建数据)
            reason="设备创建时必须选择设备类型",
        )
    """
    depends_on: list[str] = field(default_factory=list)
    dependency_type: str = "data"        # data / workflow / navigation
    reason: str = ""
```

### 2.2 ChromaDB Collection 设计

```python
# 5 个 ChromaDB Collection → 扩展为 8 个

CHROMA_COLLECTIONS = {
    "ui_patterns": {
        "description": "UI 组件模式 → 测试策略映射",
        "memory_type": MemoryType.UI_PATTERN,
        "embedding_model": "text-embedding-3-small",
    },
    "locator_history": {
        "description": "元素定位器成功率 + 失败历史",
        "memory_type": MemoryType.LOCATOR_HISTORY,
        "embedding_model": "text-embedding-3-small",
    },
    "business_rules": {
        "description": "跨页面/跨模块业务规则",
        "memory_type": MemoryType.BUSINESS_RULE,
        "embedding_model": "text-embedding-3-small",
    },
    "known_bugs": {
        "description": "已知缺陷 + workaround",
        "memory_type": MemoryType.KNOWN_BUG,
        "embedding_model": "text-embedding-3-small",
    },
    "historical_failures": {
        "description": "历史失败模式 + 修复策略",
        "memory_type": MemoryType.HISTORICAL_FAILURE,
        "embedding_model": "text-embedding-3-small",
    },
    "page_dependencies": {
        "description": "页面间依赖关系图",
        "memory_type": MemoryType.PAGE_DEPENDENCY,
        "embedding_model": "text-embedding-3-small",
    },
    "risk_patterns": {
        "description": "风险识别模式",
        "memory_type": MemoryType.RISK_PATTERN,
        "embedding_model": "text-embedding-3-small",
    },
    "workflow_recipes": {
        "description": "测试工作流配方 (多页面协作)",
        "memory_type": MemoryType.WORKFLOW_RECIPE,
        "embedding_model": "text-embedding-3-small",
    },
}
```

## 3. 四个注入层次

参考 Aperant Memory 的 4 层注入设计：

```python
# 第 1 层: 系统提示注入 (一次性，<500ms)
# 在 Agent 启动时注入全局相关的记忆

def inject_system_memory(agent_name: str, module: str) -> str:
    """构建注入系统提示的记忆上下文。"""
    mem = TestingMemoryStore()

    # 查询与当前模块相关的记忆
    relevant = mem.search_multi(
        queries=[
            {"collection": "business_rules", "query": f"module={module}"},
            {"collection": "ui_patterns", "query": module},
            {"collection": "page_dependencies", "query": module},
        ],
        top_k=3,
    )

    return _format_memory_context(relevant, max_tokens=2000)


# 第 2 层: 初始消息注入 (每个 Skill 开始前，<2s)
# 注入与当前 Skill 相关的记忆

def inject_skill_memory(skill_id: str, page: str) -> str:
    """构建注入初始消息的记忆上下文。"""
    mem = TestingMemoryStore()

    relevant = mem.search_multi([
        {"collection": "locator_history", "query": page},
        {"collection": "historical_failures", "query": f"{page}"},
        {"collection": "known_bugs", "query": f"page={page}"},
        {"collection": "risk_patterns", "query": skill_id},
    ])

    return _format_memory_context(relevant, max_tokens=1000)


# 第 3 层: 工具结果增强 (<100ms)
# 在 LLM tool call 结果中插入相关记忆

def augment_tool_result(tool_name: str, result: dict) -> dict:
    """增强工具返回结果。"""
    if tool_name == "browser__navigate":
        # 注入该页面的定位器历史
        page_url = result.get("url", "")
        locator_hints = TestingMemoryStore().search(
            "locator_history", page_url, top_k=3
        )
        result["_memory_hints"] = locator_hints

    elif tool_name == "execute__pytest":
        # 注入已知问题
        failures = result.get("failure_output", "")
        known_bugs = TestingMemoryStore().search(
            "known_bugs", failures, top_k=5
        )
        result["_known_bugs"] = known_bugs

    return result


# 第 4 层: prepareStep 回调 (<50ms)
# 每步执行前注入最新的行为信号

def prepare_step_injection(agent_state: dict) -> str:
    """构建步骤间的记忆注入。"""
    injections = []

    # Dead-end detection (参考 Aperant dead-end-detector.ts)
    if _is_stuck(agent_state):
        injections.append(
            "[MEMORY] You appear to be stuck. "
            "Consider trying a different approach or asking for help."
        )

    # Confidence boost from verified memory
    verified = TestingMemoryStore().get_verified(agent_state["page"])
    if verified:
        injections.append(f"[VERIFIED] {verified['content']}")

    return "\n".join(injections)
```

## 4. 行为信号 (被动观察)

参考 Aperant 的 17 个行为信号，AITest 定义 6 个测试专用信号：

```python
class BehaviorSignal(Enum):
    """被动观察到的行为信号。无需 Agent 显式报告。"""

    # 执行信号
    LOCATOR_RETRY = "locator_retry"          # Agent 多次尝试不同定位器
    SCRIPT_SYNTAX_FIX = "script_syntax_fix"  # Agent 修复自己生成的代码语法
    ASSERTION_ADJUST = "assertion_adjust"    # Agent 反复修改断言条件

    # 效率信号
    EXCESSIVE_GREP = "excessive_grep"        # 同一 pattern grep 超过 5 次
    SKILL_SKIP = "skill_skip"               # Agent 跳过某个 Skill
    TOOL_ERROR_RETRY = "tool_error_retry"    # 同一 tool call 失败超过 3 次

    # 效率信号
    EXCESSIVE_RE_READ = "excessive_re_read"  # 重复读取同一文件 >3 次
    REDUNDANT_STEP = "redundant_step"        # 执行了已完成的工作


class SignalObserver:
    """信号观察器 — 被动收集行为信号。

    参考 Aperant memory/observer/signals.ts 的设计理念。
    """

    def __init__(self):
        self._signal_buffer: list[dict] = []
        self._tool_call_counts: dict[str, int] = {}
        self._file_read_counts: dict[str, int] = {}

    def on_tool_call(self, tool_name: str, args: dict) -> None:
        self._tool_call_counts[tool_name] = self._tool_call_counts.get(tool_name, 0) + 1

    def on_file_read(self, file_path: str) -> None:
        self._file_read_counts[file_path] = self._file_read_counts.get(file_path, 0) + 1
        if self._file_read_counts[file_path] > 3:
            self._emit(BehaviorSignal.EXCESSIVE_RE_READ, {"file": file_path})

    def on_skill_complete(self, skill_id: str, output: str) -> None:
        # 检查产出是否为空
        if len(output) < 100:
            self._emit(BehaviorSignal.SKILL_SKIP, {"skill": skill_id})

    def flush(self) -> list[dict]:
        """获取并清空信号缓冲 (每个阶段结束时调用)。"""
        signals = self._signal_buffer.copy()
        self._signal_buffer.clear()
        return signals

    def _emit(self, signal: BehaviorSignal, detail: dict) -> None:
        self._signal_buffer.append({
            "signal": signal.value,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        })
```

## 5. 来源追踪与衰减

参考 Aperant Memory 的 provenance 追踪和 trust gate 设计：

```python
class MemoryLifecycle:
    """记忆生命周期管理。"""

    DECAY_RATE = 0.1       # 每次未确认衰减 10%
    BOOST_RATE = 0.2       # 每次验证提升 20%
    VERIFY_THRESHOLD = 3   # 验证 3 次后升级为 VERIFIED
    DELETE_THRESHOLD = 0.3 # 衰减到 30% 以下时删除

    @staticmethod
    def decay(memory: TestingMemory) -> TestingMemory:
        """衰减：长时间未确认的记忆降低置信度。"""
        memory.decay_factor = max(0.1, memory.decay_factor - MemoryLifecycle.DECAY_RATE)
        if memory.decay_factor <= MemoryLifecycle.DELETE_THRESHOLD:
            memory.confidence = Confidence.INFERRED
        return memory

    @staticmethod
    def boost(memory: TestingMemory) -> TestingMemory:
        """提升：验证成功后增加置信度。"""
        memory.verify_count += 1
        memory.decay_factor = min(1.0, memory.decay_factor + MemoryLifecycle.BOOST_RATE)
        if memory.verify_count >= MemoryLifecycle.VERIFY_THRESHOLD:
            memory.confidence = Confidence.VERIFIED
        return memory

    @staticmethod
    def should_delete(memory: TestingMemory) -> bool:
        """判断是否应删除此记忆。"""
        if memory.decay_factor < MemoryLifecycle.DELETE_THRESHOLD:
            return True
        # 过期的 known bug (已修复超过 30 天)
        if memory.type == MemoryType.KNOWN_BUG and memory.status == "fixed":
            age_days = (datetime.now() - datetime.fromisoformat(memory.updated_at)).days
            if age_days > 30:
                return True
        return False
```

## 6. Integration with ChromaDB

```python
# platform/knowledge/testing_memory_store.py

class TestingMemoryStore:
    """测试记忆存储 — ChromaDB 封装。

    替换当前的简单 ChromaDB 访问，提供类型化的 CRUD。
    """

    def __init__(self, persist_dir: str = None):
        import chromadb
        self._client = chromadb.PersistentClient(path=persist_dir or ".chroma_testing")
        self._ensure_collections()

    def _ensure_collections(self):
        for name, meta in CHROMA_COLLECTIONS.items():
            self._client.get_or_create_collection(
                name=name,
                metadata={"description": meta["description"]},
            )

    def add(self, memory: TestingMemory) -> str:
        """添加一条记忆。"""
        collection = self._client.get_collection(memory.type.value)
        collection.add(
            ids=[memory.id],
            documents=[memory.content],
            metadatas=[{
                "module": memory.module or "",
                "page": memory.page or "",
                "confidence": memory.confidence.value,
                "source": memory.source,
                "decay_factor": memory.decay_factor,
                "verify_count": memory.verify_count,
                "tags": ",".join(memory.tags),
            }],
        )
        return memory.id

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        min_confidence: Confidence = None,
    ) -> list[dict]:
        """搜索记忆。按相关性 + 置信度排序。"""
        collection = self._client.get_collection(collection_name)
        results = collection.query(query_texts=[query], n_results=top_k)

        memories = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            score = results["distances"][0][i] if results.get("distances") else 0

            # 过滤低置信度记忆
            if min_confidence and Confidence(meta["confidence"]).value < min_confidence.value:
                continue

            memories.append({
                "content": doc,
                "metadata": meta,
                "score": self._normalize_score(score),
            })

        # 按 相关性*decay_factor 排序
        memories.sort(key=lambda m: m["score"] * float(m["metadata"].get("decay_factor", 1.0)), reverse=True)
        return memories

    def search_multi(
        self,
        queries: list[dict],
        top_k: int = 3,
    ) -> dict[str, list[dict]]:
        """跨多个 Collection 搜索。"""
        results = {}
        for q in queries:
            results[q["collection"]] = self.search(
                q["collection"], q["query"], top_k=top_k
            )
        return results
```

## 7. 参考来源

| 特性 | 参考 |
|------|------|
| Memory 类型化设计 | Aperant Memory.md — 25+ memory type schema |
| 行为信号被动观察 | Aperant `memory/observer/signals.ts` — 17 行为信号 |
| 4 层注入设计 | Aperant Memory.md §Injection Points |
| 来源追踪 + 衰减 | Aperant `memory/observer/trust-gate.ts` + AITest 现有 `knowledge_model/provenance.py` |
| BM25 + 向量融合检索 | Aperant `memory/retrieval/rrf-fusion.ts` |
| ChromaDB 基础设施 | AITest 现有 `platform/knowledge.py` + ChromaDB 5 collections |
