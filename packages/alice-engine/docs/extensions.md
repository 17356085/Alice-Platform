# Extensions 指南

Extensions 是 alice-engine 的被动监听层，通过生命周期钩子在不修改 Engine 核心代码的前提下，扩展执行行为。

---

## 生命周期钩子

```
Engine.run() 被调用
    │
    ├─► on_init(engine)              初始化时触发（一次）
    │
    ├─ [SOP 执行中] ─────────────────────────────
    │   ├─► on_phase_end(module, phase, result)  每个 Phase 完成时触发
    │   └─► on_phase_end(...)                   重复 N 次
    │
    └─► on_cycle_end(module, result)             整个 Run 完成时触发（一次）
```

实现 `EngineExtension` Protocol 即可（无需继承任何基类）:

```python
from alice_engine import Engine, RunResult

class MyExtension:
    def on_init(self, engine) -> None:
        """Engine 初始化后调用。可保存 engine 引用。"""
        self.engine = engine

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        """每个 Phase 完成后调用。result 包含该 Phase 的输出。"""
        pass

    def on_cycle_end(self, module: str, result: RunResult) -> None:
        """整个 SOP 完成后调用。result 为完整执行结果。"""
        pass

# 注册 Extension
engine = Engine(project=project, extensions=[MyExtension()])
```

---

## 内置 Extensions

### AuditExtension

执行审计 Extension，记录每次 Run 的详细日志。

```python
from alice_engine.extensions import AuditExtension

ext = AuditExtension(log_path="./audit.log")
engine = Engine(project=project, extensions=[ext])
```

**功能**:
- 记录每个 Phase 的开始时间、结束时间、耗时
- 记录每次 Run 的总耗时、状态、成功/失败
- 输出到文件或标准输出

---

### ComplexityExtension

复杂度评估 Extension，对测试任务进行难度评分。

```python
from alice_engine.extensions import ComplexityExtension

ext = ComplexityExtension()
engine = Engine(project=project, extensions=[ext])
result = engine.run("equipment")

# 执行后可查询复杂度
print(ext.last_score)    # 0-100 分
print(ext.last_tier)     # "SIMPLE" / "STANDARD" / "COMPLEX"
```

**评分因子（18 个）**:
- 页面元素数量、交互复杂度、API 调用数
- 权限矩阵维度、数据验证规则数
- 依赖组件数量、异步操作数量
- 等（详见 `alice_engine.platform.complexity`）

---

### KnowledgeExtension

知识检索与沉淀 Extension — 让 Engine 在执行前了解历史经验。

```python
from alice_engine.extensions import KnowledgeExtension
from alice_engine.runtime import InMemoryKnowledgeStore

# 使用 InMemory 存储（默认，零配置）
ext = KnowledgeExtension()

# 或指定存储后端
store = InMemoryKnowledgeStore()
ext = KnowledgeExtension(store=store, search_limit=5)

engine = Engine(project=project, extensions=[ext])
```

**工作方式**:

```
执行前:  Engine 调用 ext.search_before_run(module, pages)
          → 从 KnowledgeStore 检索历史相关知识
          → 注入到 Agent 上下文（减少重复探索）

执行后:  on_cycle_end 触发
          → 将本次 RunResult 沉淀到 KnowledgeStore
          → 供下次执行参考
```

**主动调用**:

```python
# 执行前检索知识
knowledge_ctx = ext.search_before_run("equipment", ["alarm-config"])
# 返回: {"alarm-config": [KnowledgeItem, ...]}

# 执行后自动沉淀（on_cycle_end 钩子）
result = engine.run("equipment")
```

**自定义存储后端**:

```python
class ChromaKnowledgeStore:
    def ingest(self, module: str, result) -> None:
        # 向量化 result，存入 ChromaDB
        ...

    def search(self, module: str, page_slug: str, limit: int = 5) -> list:
        # 向量检索，返回相关知识
        ...

    def clear(self, module: str) -> None:
        ...

ext = KnowledgeExtension(store=ChromaKnowledgeStore())
```

**性能**（真实测量，Python 3.11.11）:
- `ingest()`: 1.79μs（558k/s）
- `search(limit=5)`: 43.16μs（23k/s）
- `on_cycle_end()` 钩子: 1.20μs

---

### MemoryExtension

执行历史记忆 Extension — 让 Engine 记住每次 Run 的结果。

```python
from alice_engine.extensions import MemoryExtension
from alice_engine.runtime import InMemoryMemoryStore

# 使用 InMemory 存储（默认，零配置）
ext = MemoryExtension()

# 或指定存储后端
store = InMemoryMemoryStore()
ext = MemoryExtension(store=store)

engine = Engine(project=project, extensions=[ext])
```

**工作方式**:

```
执行后:  on_cycle_end 触发
          → 调用 store.remember(module, result)
          → 记录 RunResult（状态、耗时、完成 Phase、错误信息）

按需查询:
  ext.get_last_run("equipment")          → 上次执行记录
  ext.get_history("equipment", limit=5)  → 最近 5 次记录
```

**主动调用**:

```python
result = engine.run("equipment")

# 查询上次执行
last = ext.get_last_run("equipment")
if last:
    print(f"上次状态: {last.status}")
    print(f"上次耗时: {last.elapsed_seconds}s")
    print(f"上次失败原因: {last.error}")

# 查询历史
history = ext.get_history("equipment", limit=10)
success_rate = sum(1 for r in history if r.success) / len(history)
print(f"成功率: {success_rate:.0%}")
```

**注意**: `MemoryExtension` 记录的是 `RunResult` 执行历史，不是向量语义记忆。
如需向量记忆，使用平台层的 `TestingMemoryStore`（ChromaDB）。

**性能**（真实测量，Python 3.11.11）:
- `remember()`: 2.06μs（485k/s）
- `get_last()`: 0.17μs（5.9M/s）
- `get_history(limit=10)`: 30.55μs（33k/s）
- `on_cycle_end()` 钩子: 1.14μs

---

## 组合使用

```python
from alice_engine import Engine, Project
from alice_engine.extensions import (
    AuditExtension,
    ComplexityExtension,
    KnowledgeExtension,
    MemoryExtension,
)
from alice_engine.runtime import InMemoryKnowledgeStore, InMemoryMemoryStore

project = Project("./my-project")

knowledge_store = InMemoryKnowledgeStore()
memory_store = InMemoryMemoryStore()

extensions = [
    AuditExtension(log_path="./audit.log"),
    ComplexityExtension(),
    KnowledgeExtension(store=knowledge_store, search_limit=10),
    MemoryExtension(store=memory_store),
]

engine = Engine(project=project, extensions=extensions, llm_provider="claude")

# 执行（4 个 Extension 全开，额外开销 < 0.3ms）
result = engine.run("equipment", pages=["alarm-config", "device-list"])

print(f"状态: {result.status}")
print(f"耗时: {result.elapsed_seconds}s")
```

---

## 编写自定义 Extension

### 最佳实践

```python
import logging
from alice_engine import RunResult

logger = logging.getLogger(__name__)


class NotifyExtension:
    """发送钉钉/Slack 通知的 Extension。"""

    def __init__(self, webhook_url: str, notify_on_failure_only: bool = False):
        self.webhook_url = webhook_url
        self.notify_on_failure_only = notify_on_failure_only
        self.engine = None

    def on_init(self, engine) -> None:
        self.engine = engine
        logger.info("NotifyExtension: initialized for project %s", engine.project.name)

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        # 大多数 Extension 不需要 phase-level 处理
        pass

    def on_cycle_end(self, module: str, result: RunResult) -> None:
        try:
            if self.notify_on_failure_only and result.success:
                return  # 仅失败时通知

            message = self._build_message(module, result)
            self._send(message)
        except Exception as e:
            # ⚠️ 必须捕获所有异常——Extension 崩溃不应影响主流程
            logger.warning("NotifyExtension: send failed: %s", e)

    def _build_message(self, module: str, result: RunResult) -> str:
        icon = "✅" if result.success else "❌"
        return f"{icon} [{module}] {result.status} in {result.elapsed_seconds:.1f}s"

    def _send(self, message: str) -> None:
        import urllib.request, json
        data = json.dumps({"text": message}).encode()
        req = urllib.request.Request(self.webhook_url, data=data,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
```

### 原则

1. **保持轻量** — Extension 钩子在主线程同步执行，避免耗时操作（文件 I/O、网络请求用后台线程）
2. **异常安全** — `on_cycle_end` 内必须 `try/except`，避免 Extension 崩溃影响主流程
3. **可选依赖** — Extension 的第三方依赖设为可选，在 `__init__` 或首次使用时导入
4. **状态隔离** — Extension 实例应是无状态的，或状态与 Engine 生命周期一致
5. **最小接口** — 不需要的钩子 `pass` 即可，Protocol 不强制实现所有方法

---

## Extension 性能参考

| Extension | `on_init` | `on_phase_end` | `on_cycle_end` | 备注 |
|-----------|-----------|----------------|----------------|------|
| AuditExtension | ~5μs | ~2μs | ~10μs | 本地 I/O |
| ComplexityExtension | ~10μs | ~50μs | ~5μs | 18 因子计算 |
| KnowledgeExtension | ~1μs | 0μs | 1.20μs | InMemory 实现 |
| MemoryExtension | ~1μs | 0μs | 1.14μs | InMemory 实现 |
| **4 个全开** | ~17μs | ~52μs | **~17μs/次** | 极低开销 |

4 个 Extension 全开时，Engine 创建额外开销 +48%（0.605ms → 0.896ms，绝对值 < 0.3ms）。
相对于 LLM 调用（数百 ms ~ 数秒），Extension 开销 < 0.01%，完全可以忽略。

详见 `docs/architecture/performance-benchmark-report.md`（真实测量数据）。
