# 平台到 SDK 迁移指南

**版本**: 1.0  
**日期**: 2026-07-09  
**目标**: 帮助开发者从 `aitest.*` 平台导入迁移到 `alice_engine` SDK 导入

---

## 快速参考

### 常见导入迁移

| 平台导入 (旧) | SDK 导入 (新) | 说明 |
|--------------|--------------|------|
| `from aitest.engine import Engine` | `from alice_engine import Engine` | Engine 主类 |
| `from aitest.engine.executor import AgentLoop` | `from alice_engine import ExecutionKernel` | 执行器 |
| `from aitest.llm.providers.claude import ClaudeProvider` | `from alice_engine.providers import get_provider` | LLM Provider |
| `from aitest.engine.extensions import AuditExtension` | `from alice_engine import AuditExtension` | 扩展（部分） |
| `from aitest.graphs.sop_graph import build_graph` | `from alice_engine.workflow import WorkflowBuilder` | 工作流 |

---

## 分类迁移指南

### 1. Engine 核心

#### ✅ 已迁移到 SDK

```python
# 旧
from aitest.engine import Engine, RunResult
from aitest.engine.project import Project, ProjectConfig

# 新
from alice_engine import Engine, RunResult, Project, ProjectConfig
```

**使用示例**:
```python
from alice_engine import Engine, Project

project = Project("./my-test-project")
engine = Engine(
    project=project,
    llm_provider="claude",
    mock_llm=False,
)
result = engine.run(module="user", pages=["user-list"])
print(result.status)
```

---

### 2. LLM Providers

#### ✅ 已迁移到 SDK

```python
# 旧（直接导入 Provider 类）
from aitest.llm.providers.claude import ClaudeProvider
from aitest.llm.providers.openai import OpenAIProvider

# 新（使用工厂函数）
from alice_engine.providers import get_provider

llm = get_provider("claude", api_key="...")
llm = get_provider("openai", model="gpt-4o")
```

**注意**: 平台层 `aitest.adapters.llm.interface.get_provider()` 提供额外功能：
- 自动注入 API key（从 `.env` 读取）
- Trace 装饰器包装（性能监控）

```python
# 平台增强版（推荐在 aitest 项目中使用）
from aitest.adapters.llm.interface import get_provider

llm = get_provider("claude")  # 自动读取 ANTHROPIC_API_KEY
```

---

### 3. Extensions

#### ✅ 部分迁移到 SDK

| Extension | SDK | 平台 | 说明 |
|-----------|-----|------|------|
| `AuditExtension` | ✅ | ❌ | 已迁移 |
| `ComplexityExtension` | ✅ | ❌ | 已迁移 |
| `KnowledgeExtension` | ❌ | ✅ | 平台特定（待迁移） |
| `MemoryExtension` | ❌ | ✅ | 平台特定（待迁移） |

```python
# 已迁移的扩展
from alice_engine import AuditExtension, ComplexityExtension

# 平台特定扩展（暂时保留）
from aitest.engine.extensions import KnowledgeExtension, MemoryExtension

engine = Engine(project=project)
engine.add_extension(AuditExtension())
engine.add_extension(ComplexityExtension())
engine.add_extension(KnowledgeExtension())  # 仍从平台导入
```

**路线图**: Knowledge 和 Memory Extension 将在未来版本迁移到 SDK。

---

### 4. Runtime Capabilities

#### ✅ 已迁移到 SDK

```python
# 旧
from aitest.runtime.knowledge import KnowledgeStore, InMemoryKnowledgeStore
from aitest.runtime.memory import MemoryStore, InMemoryMemoryStore

# 新
from alice_engine.runtime import (
    KnowledgeStore, InMemoryKnowledgeStore,
    MemoryStore, InMemoryMemoryStore,
)
```

**使用示例**:
```python
from alice_engine import Engine, Project
from alice_engine.runtime import InMemoryKnowledgeStore, InMemoryMemoryStore

engine = Engine(
    project=Project("./my-project"),
    knowledge=InMemoryKnowledgeStore(),
    memory=InMemoryMemoryStore(),
)
```

---

### 5. Discovery

#### ⚠️ 分层设计（保留两者）

| 包 | 职责 | 导入 |
|----|------|------|
| `alice-discovery` | 静态源码分析 | `from alice_discovery import SourceDiscoveryPipeline` |
| `aitest/discovery/` | 运行时发现 + 插件管理 | `from aitest.discovery.registry import DiscoveryRegistry` |

```python
# SDK 静态分析
from alice_discovery import SourceDiscoveryPipeline, VueRouterExtractor

pipeline = SourceDiscoveryPipeline()
knowledge = pipeline.run(Path("./vue-app"))

# 平台运行时发现
from aitest.discovery.registry import DiscoveryRegistry
from aitest.discovery.browser_use import BrowserUseDiscovery

discovery = DiscoveryRegistry.create("browser-use", project_id="my-app")
```

**说明**: 这不是重复代码，而是分层设计。SDK 提供通用能力，平台提供集成。

---

### 6. Events

#### ✅ 已迁移到 SDK

```python
# 旧
from aitest.engine.event_bus import EventBus, get_event_bus

# 新
from alice_engine import EventBus

bus = EventBus()
bus.subscribe("phase_start", handler)
bus.emit("phase_start", {"phase": "discovery"})
```

**注意**: 平台层 `aitest.engine.event_bus.get_event_bus()` 返回适配器单例：
```python
# 平台适配器（桥接到平台 EventBus）
from aitest.engine.event_bus import get_event_bus

bus = get_event_bus()  # 单例，桥接到平台 EventBus
```

---

### 7. Workflow

#### ✅ 已迁移到 SDK

```python
# 旧
from aitest.graphs.sop_graph import build_graph, SOPGraphExecutor
from aitest.graphs.state import GraphState

# 新
from alice_engine.workflow import WorkflowBuilder, ExecutionGraph
from alice_engine.kernel import SOPGraphExecutionKernel
```

**使用示例**:
```python
from alice_engine import Engine, Project
from alice_engine.workflow import WorkflowBuilder

builder = WorkflowBuilder()
graph = builder.build(module="user", pages=["user-list"])

engine = Engine(project=Project("./my-project"))
result = engine.run(module="user", pages=["user-list"])
```

---

## 平台特定保留

以下模块**不会**迁移到 SDK，因为它们是平台业务特有：

### 1. Runtime Config 和 Paths

```python
# 这些是平台基础设施，不属于 SDK
from aitest.runtime.config import config
from aitest.runtime.paths import get_workstudy, get_test_project_root
```

**理由**: 这些是 `aitest` 平台的项目管理逻辑，SDK 不需要知道 "WorkStudy" 或 ".tlo/" 目录。

---

### 2. Platform Context

```python
# 平台项目管理
from aitest.platform.context import get_project, ProjectContext
```

**理由**: SDK 使用 `Project` 对象传递配置，平台使用 `ProjectContext` 管理多项目。

---

### 3. Discovery Registry

```python
# 平台插件管理
from aitest.discovery.registry import DiscoveryRegistry
from aitest.discovery.browser_use import BrowserUseDiscovery
```

**理由**: SDK 提供静态分析（`alice-discovery`），平台提供运行时发现和插件管理。

---

## 迁移步骤

### Step 1: 审计当前导入

```bash
# 检查项目中的 aitest 导入
grep -rn "from aitest\." . --include="*.py" | grep -v __pycache__
```

### Step 2: 识别可迁移导入

参考本文档的 "常见导入迁移" 表格，识别哪些可以迁移到 SDK。

### Step 3: 逐个文件重构

```python
# 示例：重构一个测试脚本

# 修改前
from aitest.engine import Engine
from aitest.llm.providers.claude import ClaudeProvider

engine = Engine(workstudy="./my-project")
llm = ClaudeProvider(api_key="...")

# 修改后
from alice_engine import Engine, Project
from alice_engine.providers import get_provider

engine = Engine(project=Project("./my-project"))
llm = get_provider("claude", api_key="...")
```

### Step 4: 测试

```bash
# 运行测试确认无破坏性变更
pytest tests/
```

---

## 常见问题

### Q1: 为什么 `aitest.runtime` 不在 SDK 中？

**A**: `aitest.runtime` 是平台的基础设施层，包含：
- `config.py` — 读取 `aitest` 平台的环境变量配置
- `paths.py` — 管理 WorkStudy 目录、.tlo/ 路径
- `context.py` — 平台项目上下文管理

SDK 有自己的配置和项目管理方式（`Project` 对象），不需要这些平台特定逻辑。

---

### Q2: `KnowledgeExtension` 和 `MemoryExtension` 何时迁移到 SDK？

**A**: 计划在下一个迭代（1-2 周）迁移。当前它们依赖平台特定的存储实现，需要先抽象接口。

---

### Q3: 可以混用平台导入和 SDK 导入吗？

**A**: 可以，但不推荐。建议：
- 新代码：优先使用 SDK 导入
- 旧代码：逐步迁移

当前 CLI 使用混合导入策略作为过渡：
```python
# SDK 扩展
from alice_engine import AuditExtension, ComplexityExtension
# 平台特定扩展（待迁移）
from aitest.engine.extensions import KnowledgeExtension, MemoryExtension
```

---

### Q4: SDK 可以独立使用吗？

**A**: 是的，SDK 设计为独立包：

```python
# 纯 SDK 项目
from alice_engine import Engine, Project
from alice_engine.providers import get_provider
from alice_engine.runtime import InMemoryKnowledgeStore

project = Project("/path/to/test-project")
engine = Engine(
    project=project,
    llm_provider=get_provider("claude", api_key="sk-..."),
    knowledge=InMemoryKnowledgeStore(),
)
result = engine.run("user", ["user-list"])
```

---

### Q5: 平台的 `get_provider()` 和 SDK 的 `get_provider()` 有什么区别？

**A**: 

| 特性 | SDK | 平台 |
|------|-----|------|
| 基础功能 | ✅ Provider 创建 | ✅ Provider 创建 |
| API Key 注入 | ❌ 需手动传递 | ✅ 自动从 `.env` 读取 |
| Trace 装饰器 | ❌ | ✅ 性能监控 |
| 特殊处理 | ❌ | ✅ MiMo/Ollama base_url 注入 |

```python
# SDK 版本（手动传 API key）
from alice_engine.providers import get_provider
llm = get_provider("claude", api_key="sk-...")

# 平台版本（自动注入）
from aitest.adapters.llm.interface import get_provider
llm = get_provider("claude")  # 自动读取 ANTHROPIC_API_KEY
```

---

## 迁移检查清单

- [ ] 审计项目中的 `from aitest.*` 导入
- [ ] 识别可迁移到 SDK 的导入
- [ ] 更新 Engine 和 Project 导入
- [ ] 更新 LLM Provider 导入（使用 `get_provider()`）
- [ ] 更新 Extensions 导入（区分 SDK 和平台）
- [ ] 更新 Runtime Capabilities 导入
- [ ] 运行测试验证
- [ ] 更新文档和示例

---

## 参考资源

- **ADR-002** — Engine 职责边界
- **架构健康报告** — `docs/architecture/architecture-health-report-2026-07-09.md`
- **SDK README** — `packages/alice-engine/README.md`
- **审计报告** — `docs/architecture/cleanup-audit-2026-07-09.md`

---

**版本历史**:
- 1.0 (2026-07-09) — 初始版本，基于架构审计结果
