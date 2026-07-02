# Standalone Engine Architecture

> 架构解耦分析 — 文档 3/7
> 目标: 给出最小可运行（Standalone Engine）的架构，三层分类: Core / Extensions / Platform
> 注: 05 升级为四层 (Core/Runtime/Workflow/Adapter)，07 提供迁移地图

## 1. 架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Standalone Engine                                   │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Entry Point: demo.py / CLI                                        │  │
│  │   engine = Engine(workstudy, governance)                           │  │
│  │   engine.add_extension(AuditExtension())                          │  │
│  │   result = engine.run(module, pages, mode)                         │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │                                              │
│  ┌───────────────────────▼───────────────────────────────────────────┐  │
│  │ Extensions (可插拔)                                                │  │
│  │                                                                    │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │  │
│  │  │Capability│ │Complexity│ │Knowledge │ │Testing   │ │Browser │  │  │
│  │  │Router    │ │Classifier│ │+ RAG     │ │Memory    │ │-Use    │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘  │  │
│  │  ┌──────────┐ ┌──────────┐                                        │  │
│  │  │Audit     │ │Context   │                                        │  │
│  │  │Engine    │ │Builder   │                                        │  │
│  │  └──────────┘ └──────────┘                                        │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │ (Extensions 在生命周期钩子中运行)              │
│  ┌───────────────────────▼───────────────────────────────────────────┐  │
│  │ Core: SOP Runner                                                   │  │
│  │   build_sop_graph() → compile(checkpointer) → invoke(state)       │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │                                              │
│  ┌───────────────────────▼───────────────────────────────────────────┐  │
│  │ Core: SOP Graph (LangGraph StateGraph)                             │  │
│  │                                                                    │  │
│  │  entry → preflight → route ─┬→ project_agent ─→ route             │  │
│  │                              ├→ requirement_agent ─→ route         │  │
│  │                              ├→ test_design_agent ─→ qgate         │  │
│  │                              ├→ automation ─→ hitl ─→ page_iter    │  │
│  │                              ├→ execution_agent ─→ route           │  │
│  │                              ├→ bug_analysis ─→ qa_loop            │  │
│  │                              ├→ report_agent ─→ route              │  │
│  │                              └→ knowledge_agent ─→ route           │  │
│  │                              └→ exit → END                         │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │                                              │
│  ┌───────────────────────▼───────────────────────────────────────────┐  │
│  │ Core: AgentLoop                                                    │  │
│  │   SkillLoader.load(agent_name) → SkillExecutor.execute()          │  │
│  │     → LLMProvider.chat(messages) → 产物写入                        │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │                                              │
│  ┌───────────────────────▼───────────────────────────────────────────┐  │
│  │ Core: LLM Layer                                                    │  │
│  │   ReliableProvider(3x Retry) → Claude/DeepSeek/OpenAI             │  │
│  │   ContextWindow(85%/90% 阈值) → continuation                      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Core: Infrastructure                                               │  │
│  │   secure_subprocess, command_validator, paths, config              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Core: Governance (静态文件)                                         │  │
│  │   agents/*.yaml, skills/*.md, shared-language.md                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Core: Mocks (Standalone 专用)                                      │  │
│  │   NoopEventBus, SimpleErrorLogger                                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2. 模块清单

### 2.1 Core (MUST) — 24 个 Python 文件

**Core Graphs (7 文件)**

| 文件 | 职责 | 行数 |
|------|------|------|
| `graphs/sop_graph.py` | SOP 编排图 + 路由 | ~1500 |
| `graphs/sop_runner.py` | CompiledGraph.invoke() | ~200 |
| `graphs/state.py` | SOPState TypedDict | ~300 |
| `graphs/nodes.py` | AgentLoop 节点工厂 | ~200 |
| `graphs/checkpoint.py` | SQLite Checkpoint | ~100 |
| `graphs/execution_graph.py` | execution/report/knowledge 子图 | ~400 |
| `graphs/bug_analysis_graph.py` | bug 分析子图 | ~300 |

**Agent Runtime (5 文件)**

| 文件 | 职责 | 行数 |
|------|------|------|
| `agents/agent_runner.py` | AgentLoop 执行引擎 | ~800 |
| `agents/skill_executor.py` | Skill 加载+执行 | ~300 |
| `agents/runner_state.py` | 任务状态模型 | ~100 |
| `agents/task_state_machine.py` | Agent 状态机 | ~200 |
| `agents/core.py` | Agent 定义 | ~100 |

**LLM Layer (8 文件)**

| 文件 | 职责 | 行数 |
|------|------|------|
| `llm/provider.py` | 统一 LLM 接口 | ~200 |
| `llm/reliable_provider.py` | Retry + Fallback | ~300 |
| `llm/context_window.py` | Token 管理 + 续传 | ~400 |
| `llm/prompt_adapter.py` | Provider 格式化 | ~200 |
| `llm/skill_loader.py` | .md Skill 文件读取 | ~200 |
| `llm/skill_yaml_parser.py` | Skill YAML 解析 | ~100 |
| `llm/governance_gate.py` | 生成前检查 | ~100 |
| `llm/governance_connector.py` | Agent ↔ Governance | ~100 |

**Infrastructure (4 文件)**

| 文件 | 职责 | 行数 |
|------|------|------|
| `infra/secure_subprocess.py` | 安全 subprocess | ~100 |
| `infra/security/command_validator.py` | 命令白名单 | ~100 |
| `infra/security/__init__.py` | 安全模块入口 | ~50 |
| `infra/error_logger.py` | 错误日志 (可简化) | ~100 |

**Platform Core (3 文件)**

| 文件 | 职责 | 行数 |
|------|------|------|
| `platform/paths.py` | 路径解析 | ~170 |
| `platform/_paths_core.py` | 路径核心 | ~50 |
| `platform/context.py` | 项目上下文 | ~300 |

**Config (1 文件)**

| 文件 | 职责 | 行数 |
|------|------|------|
| `config.py` | .env + YAML 配置 | ~200 |

**Mocks (2 文件, 新建)**

| 文件 | 职责 | 行数 |
|------|------|------|
| `engine/mocks.py` | NoopEventBus, SimpleErrorLogger | ~50 |
| `engine/__init__.py` | Engine 类 + Extension 接口 | ~150 |

**Governance (静态文件, ~70 文件)**

| 目录 | 内容 | 文件数 |
|------|------|--------|
| `governance/agents/` | Agent 定义 YAML | ~12 |
| `governance/skills/` | Skill 提示 .md | ~24 |
| `governance/skills-dev/` | 开发 Skill .md | ~32 |
| `governance/context/` | shared-language.md | ~5 |

### 2.2 Extensions (SHOULD) — 9 个可插拔子引擎

| 子引擎 | 模块 | 独立职责 | 增强能力 |
|--------|------|----------|----------|
| **Capability Router** | `platform/capability_router/` | Agent ↔ Provider 路由 | 自动选择最优 Provider |
| **Complexity Classifier** | `platform/complexity/` | SOP 流水线路由 | 按复杂度选择流水线 |
| **Knowledge + RAG** | `knowledge/` | 知识检索 + 沉淀 | 跨 Run 知识复用 |
| **Testing Memory** | `platform/testing_memory.py` | ChromaDB 向量记忆 | 跨 Run 记忆 |
| **Memory Observer** | `platform/memory_observer.py` | Memory 自动同步 | Memory 生命周期 |
| **Browser-Use** | `discovery/browser_use.py` | AI 浏览器探索 | 自动探索页面结构 |
| **BU Adapter** | `bu_adapter.py` | Browser-Use 适配 | Skill ↔ BrowserUseDriver |
| **Audit Engine** | `audit_engine/` | 质量审计 (6 维) | 状态漂移 + SOP 合规 |
| **Context Builder** | `llm/context_builder.py` | 上下文压缩 | 减少 Token 消耗 |

### 2.3 Platform (MUST NOT) — 不进入 Engine

Web API, Dashboard, Auth, Tenant, Billing, Metrics, Hooks, ObservationBus, RunStore, ExecutionService, Lifecycle, Plugin, Artifacts, Timeline, Discovery, CLI, Web Frontend, MCP, IDE, Integrations, Chat, CostAdvisor, Testing Tools

## 3. Engine 类设计 (含 Extension 支持)

```python
# engine/__init__.py

import os
import logging
from pathlib import Path
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


# ── Extension 接口 ─────────────────────────────────────────────────

class EngineExtension(Protocol):
    """Engine Extension 接口。

    Extensions 在 Engine 生命周期钩子中运行:
      - on_init:       Engine 初始化后
      - on_preflight:  Preflight 完成后
      - on_phase_end:  每个 Phase 完成后
      - on_cycle_end:  整个 SOP 流水线完成后
    """

    def on_init(self, engine: "Engine") -> None:
        """Engine 初始化后调用。"""
        ...

    def on_preflight(self, module: str, preflight_result: dict) -> None:
        """Preflight 完成后调用。"""
        ...

    def on_phase_end(self, module: str, phase: str, result: dict) -> None:
        """每个 Phase 完成后调用。"""
        ...

    def on_cycle_end(self, module: str, result: dict) -> None:
        """整个 SOP 流水线完成后调用。"""
        ...


# ── Engine 类 ──────────────────────────────────────────────────────

class Engine:
    """Standalone Engine — 最小可运行的 SOP 执行引擎。

    三层架构:
      - Core:       串行必须，SOP 编排 + Agent 执行 + LLM 调用
      - Extensions:  可插拔子引擎，增强但不串入核心链路
      - Platform:    不属于引擎，Web API / Dashboard / Auth 等

    用法:
        engine = Engine()
        result = engine.run("equipment", ["alarm-config", "camera"])

    带 Extension:
        engine = Engine()
        engine.add_extension(AuditExtension())
        engine.add_extension(ComplexityExtension())
        result = engine.run("equipment", ["alarm-config", "camera"])
    """

    def __init__(
        self,
        workstudy: str = None,
        governance: str = None,
        llm_provider: str = None,
        event_bus=None,
    ):
        self.workstudy = Path(workstudy or os.environ.get("ENGINE_WORKSTUDY", "."))
        self.governance = Path(governance or os.environ.get(
            "ENGINE_GOVERNANCE", self.workstudy / "governance"))
        self.llm_provider = llm_provider or os.environ.get("LLM_PROVIDER", "anthropic")
        self.event_bus = event_bus or NoopEventBus()
        self._extensions: list[EngineExtension] = []

        # 配置路径
        os.environ["ENGINE_WORKSTUDY"] = str(self.workstudy)
        os.environ["ENGINE_GOVERNANCE"] = str(self.governance)

        logger.info("Engine initialized: workstudy=%s, governance=%s, llm=%s",
                     self.workstudy, self.governance, self.llm_provider)

    def add_extension(self, ext: EngineExtension) -> None:
        """注册一个 Extension。"""
        self._extensions.append(ext)
        ext.on_init(self)
        logger.info("Extension registered: %s", type(ext).__name__)

    def run(
        self,
        project: str,
        module: str = None,
        pages: list[str] = None,
        mode: str = "full",
        run_id: str = None,
    ) -> dict:
        """执行一次完整的 SOP 流水线。

        Args:
            project: 项目 ID (对应 .tlo/project.yaml)
            module: 模块名 (可选，None=自动发现)
            pages: 页面列表 (可选，None=自动发现)
            mode: 执行模式 (full/resume/from-automation/status)
            run_id: 运行 ID (可选，None=自动生成)
        """
        import time
        import uuid

        if run_id is None:
            run_id = f"engine-{uuid.uuid4().hex[:8]}"

        logger.info("Engine.run: module=%s, pages=%s, mode=%s, run_id=%s",
                     module, pages, mode, run_id)

        start_time = time.time()

        # 构建初始状态
        from aitest.graphs.state import create_initial_state
        initial_state = create_initial_state(module, pages or [], mode=mode)
        initial_state["run_id"] = run_id

        # 构建并编译图
        from aitest.graphs.sop_graph import build_sop_graph
        from aitest.graphs.checkpoint import get_checkpointer

        graph = build_sop_graph()
        compiled = graph.compile(checkpointer=get_checkpointer())

        # 执行
        try:
            final_state = compiled.invoke(
                initial_state,
                {"configurable": {"thread_id": run_id}},
            )
        except Exception as e:
            logger.error("Engine.run failed: %s", e, exc_info=True)
            return {
                "status": "failed",
                "run_id": run_id,
                "error": str(e),
                "elapsed_seconds": round(time.time() - start_time, 2),
                "completed_phases": [],
                "failed_phases": [],
                "pages": pages or [],
                "agent_outputs": {},
            }

        elapsed = time.time() - start_time

        result = {
            "status": final_state.get("status", "unknown"),
            "run_id": run_id,
            "elapsed_seconds": round(elapsed, 2),
            "completed_phases": final_state.get("completed_phases", []),
            "failed_phases": final_state.get("failed_phases", []),
            "pages": final_state.get("pages", []),
            "agent_outputs": final_state.get("agent_outputs", {}),
            "module": module,
            "mode": mode,
        }

        # Extensions: on_cycle_end
        for ext in self._extensions:
            try:
                ext.on_cycle_end(module, result)
            except Exception as e:
                logger.warning("Extension %s.on_cycle_end failed: %s",
                               type(ext).__name__, e)

        logger.info("Engine.run completed: status=%s, elapsed=%.1fs, phases=%d",
                     result["status"], elapsed, len(result["completed_phases"]))

        return result


class NoopEventBus:
    """空事件总线 — Standalone 模式下丢弃所有事件。"""

    def emit(self, event_type: str, **kwargs) -> None:
        logger.debug("EventBus.emit (noop): %s %s", event_type, kwargs)
```

## 4. Extension 实现示例

### 4.1 Audit Extension

```python
# engine/extensions/audit.py

"""Audit Engine Extension — 状态漂移 + SOP 合规检查。"""


class AuditExtension:
    """将 Audit Engine 作为 Extension 注入 Engine。"""

    def on_init(self, engine):
        self.engine = engine

    def on_preflight(self, module, preflight_result):
        pass  # Preflight 阶段不需要审计

    def on_phase_end(self, module, phase, result):
        pass  # Phase 级别审计可选

    def on_cycle_end(self, module, result):
        """SOP 完成后运行 StateAuditor + SOPAuditor。"""
        try:
            from aitest.audit_engine.state_auditor import StateAuditor
            auditor = StateAuditor()
            audit_report = auditor.audit(module, auto_repair=False)
            result["audit"] = {
                "drift_count": audit_report["drift_count"],
                "error_count": audit_report["error_count"],
                "warning_count": audit_report["warning_count"],
            }
        except Exception as e:
            import logging
            logging.getLogger("engine.audit").warning("Audit failed: %s", e)
```

### 4.2 Complexity Extension

```python
# engine/extensions/complexity.py

"""Complexity Classifier Extension — 按复杂度选择 SOP 流水线。"""


class ComplexityExtension:
    """在 Preflight 后评估页面复杂度，推荐最优流水线。"""

    def on_init(self, engine):
        self.engine = engine

    def on_preflight(self, module, preflight_result):
        """Preflight 后评估复杂度。"""
        try:
            from aitest.platform.complexity import complexity_assess
            pages = preflight_result.get("pages", [])
            for page_slug in pages:
                assessment = complexity_assess({}, page_title=page_slug)
                preflight_result.setdefault("complexity", {})[page_slug] = assessment
        except Exception as e:
            import logging
            logging.getLogger("engine.complexity").warning("Complexity failed: %s", e)

    def on_phase_end(self, module, phase, result):
        pass

    def on_cycle_end(self, module, result):
        pass
```

### 4.3 Knowledge Extension

```python
# engine/extensions/knowledge.py

"""Knowledge + RAG Extension — 跨 Run 知识复用。"""


class KnowledgeExtension:
    """注入历史知识到 AgentLoop 上下文。"""

    def on_init(self, engine):
        self.engine = engine
        self._store = None

    def _get_store(self):
        if self._store is None:
            try:
                from aitest.knowledge.rag_engine import RAGEngine
                self._store = RAGEngine()
            except Exception:
                self._store = False  # 标记不可用
        return self._store if self._store is not False else None

    def on_preflight(self, module, preflight_result):
        """注入历史知识。"""
        store = self._get_store()
        if store:
            try:
                relevant = store.search(module, limit=5)
                preflight_result["knowledge_context"] = relevant
            except Exception:
                pass

    def on_phase_end(self, module, phase, result):
        pass

    def on_cycle_end(self, module, result):
        """完成后沉淀知识。"""
        store = self._get_store()
        if store:
            try:
                store.ingest(module, result)
            except Exception:
                pass
```

## 5. 目录结构

```
aitest/
├── engine/                              ← 新增: Standalone Engine 入口
│   ├── __init__.py                      ← Engine 类 + Extension 接口
│   ├── mocks.py                         ← Mock 模块
│   └── extensions/                      ← 新增: Extension 实现
│       ├── audit.py                     ← Audit Engine Extension
│       ├── complexity.py                ← Complexity Classifier Extension
│       ├── knowledge.py                 ← Knowledge + RAG Extension
│       └── memory.py                    ← Testing Memory Extension
│
├── graphs/                              ← Core: SOP 编排
│   ├── sop_graph.py
│   ├── sop_runner.py
│   ├── state.py
│   ├── nodes.py
│   ├── checkpoint.py
│   ├── execution_graph.py
│   └── bug_analysis_graph.py
│
├── agents/                              ← Core: Agent 执行
│   ├── agent_runner.py
│   ├── skill_executor.py
│   ├── runner_state.py
│   ├── task_state_machine.py
│   └── core.py
│
├── llm/                                 ← Core: LLM 调用
│   ├── provider.py
│   ├── reliable_provider.py
│   ├── context_window.py
│   ├── prompt_adapter.py
│   ├── skill_loader.py
│   ├── skill_yaml_parser.py
│   ├── governance_gate.py
│   └── governance_connector.py
│
├── infra/                               ← Core: 基础设施
│   ├── secure_subprocess.py
│   └── security/
│       ├── __init__.py
│       └── command_validator.py
│
├── platform/                            ← Core + Extensions
│   ├── paths.py                         ← Core
│   ├── _paths_core.py                   ← Core
│   ├── context.py                       ← Core
│   ├── capability_router/               ← Extension
│   ├── complexity/                      ← Extension
│   ├── testing_memory.py                ← Extension
│   └── memory_observer.py               ← Extension
│
├── knowledge/                           ← Extension
│   ├── knowledge_extractor.py
│   └── rag_engine.py
│
├── audit_engine/                        ← Extension
│   ├── event_bus.py
│   ├── state_auditor.py
│   ├── sop_auditor.py
│   └── ...
│
├── discovery/                           ← Extension (Browser-Use)
│   └── browser_use.py
│
├── bu_adapter.py                        ← Extension
│
├── config.py                            ← Core: 配置
│
├── governance/                          ← Core: 静态文件
│   ├── agents/
│   ├── skills/
│   └── context/
│
├── server/                              ← Platform: 不进入 Engine
├── chat/                                ← Platform
├── hooks/                               ← Platform
├── testing/                             ← Platform
├── web/                                 ← Platform
├── mcp/                                 ← Platform
├── ide/                                 ← Platform
└── integrations/                        ← Platform
```

## 6. 依赖最小化

### 6.1 requirements-engine.txt (Core 最小依赖)

```
# Standalone Engine 最小依赖
langgraph>=0.2.0
langchain-core>=0.3.0
anthropic>=0.40.0
openai>=1.50.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

### 6.2 requirements-extensions.txt (Extensions 额外依赖)

```
# Extensions 额外依赖 (可选)
chromadb>=0.4.0          # Testing Memory
playwright>=1.40.0       # Browser-Use
```

### 6.3 环境变量

```bash
# .env (Standalone Engine)
ENGINE_WORKSTUDY=/path/to/workstudy
ENGINE_GOVERNANCE=/path/to/governance
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
# 可选
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...
```

## 7. 与完整 Platform 的关系

```
完整 Platform:
  Engine Core + All Extensions + Web API + Dashboard + Auth + Tenant + ...

Standalone Engine (Core only):
  Engine Core + NoopEventBus + Mocks

Standalone Engine (with Extensions):
  Engine Core + AuditExtension + ComplexityExtension + KnowledgeExtension + ...

切换方式:
  1. 完整 Platform:     python -m aitest.server.main
  2. Standalone Core:   python demo.py --module equipment
  3. Standalone + Ext:  python demo.py --module equipment --extensions audit,complexity
```

**关键设计原则**:

1. Engine Core 不修改任何现有代码
2. Extensions 通过接口注入，不硬编码到 Core
3. Extensions 可独立测试和演示
4. 完整 Platform 仍然正常工作
