# AI 自动化测试平台 — 去平台化路线图

> 版本：v1.0 | 日期：2026-06-12 | 来源：架构审计评估
> 背景文档：`AI_TEST_PLATFORM_ARCHITECTURE_OPTIMIZATION.md`（完整架构审计）
> 前置阅读：`CLAUDE.md` → `governance/README.md`

---

## 一、问题陈述

当前项目深度绑定 Claude Code 平台：

| 耦合点 | 具体表现 | 影响 |
|--------|---------|------|
| Agent 调用 | 依赖 Claude Code 的 `Skill` 工具 + 斜杠命令 | 无法在其他 AI 客户端中使用 |
| Workflow 编排 | 依赖 Claude Code 的 `Workflow` 工具（`workflow.js`） | 编排逻辑不可跨平台复现 |
| Agent 执行 | 依赖 Claude Code 的 Agent SDK（subagent） | 子 Agent 调度绑死 Claude |
| 入口发现 | 依赖 `CLAUDE.md` 自动加载机制 | 其他平台无等效机制 |
| Memory | 依赖 Claude Code 原生 Memory | 跨会话记忆不可移植 |
| LLM | 仅支持 Claude 模型系列 | 无法使用 GPT/本地模型 |

**但好消息是**：项目约 60% 的资产已经是平台无关的——

```
✅ Skill 内容 (Prompt)    → 纯 Markdown，28 个 Skill 全部可移植
✅ Context 数据            → 纯 YAML/Markdown，版本化存储
✅ MCP Server             → 标准协议（CNCF 托管），2 个 Server 已就绪
✅ aitest CLI             → 纯 Python，10 个子命令
✅ RAG 引擎               → ChromaDB，5 集合 235 文档
✅ Event Bus              → 文件持久化，4 种事件类型
✅ Workflow Engine        → 自研 YAML DAG 执行器
✅ Agent Scheduler        → Python 状态机，前置条件检测
✅ 代码质量工具            → check_code_quality.py，独立可执行
```

---

## 二、六条去平台化路径

### 路径总览

| 路径 | 投入 | 收益 | 风险 | 适合时机 | LLM无关 | 多用户 | Web UI |
|------|:---:|:---:|:---:|------|:---:|:---:|:---:|
| 1. MCP 优先 | ★☆☆☆☆ | ★★★☆☆ | 低 | **现在** | 部分 | ❌ | ❌ |
| 2. CLI + Provider 抽象 | ★★☆☆☆ | ★★★★☆ | 低 | **1 个月内** | ✅ | ❌ | ❌ |
| 3. LangGraph 移植 | ★★★★☆ | ★★★★★ | 中 | ✅ 已完成 (2026-06-13) | ✅ | ❌ | ❌ |
| 4. Dify 低代码编排 | ★★★☆☆ | ★★★★☆ | 中低 | 需要非开发用户时 | ✅ | ✅ | ✅ |
| 5. 自研 FastAPI 平台 | ★★★★☆ | ★★★★★ | 中高 | 3-6 个月内 | ✅ | ✅ | 可选 |
| 6. 容器化 + 消息队列 | ★★★★★ | ★★★★★ | 高 | 多项目/大团队时 | ✅ | ✅ | 独立 |

---

### 路径 1：MCP 优先 — 协议层解耦

**核心思路**：不改变现有架构，通过 MCP 协议让更多 AI 客户端消费你的测试能力。

MCP（Model Context Protocol）是 Anthropic 推出的**开放标准**，2026 年已捐给 CNCF，非 Claude 专属。

**支持 MCP 的客户端生态**（截至 2026-06）：

| 客户端 | 支持模型 | 形态 | MCP 成熟度 |
|--------|---------|------|:---:|
| Claude Desktop | Claude | 桌面应用 | 🟢 完整 |
| Claude Code | Claude | CLI | 🟢 完整 |
| **Continue.dev** | Claude / GPT-4 / 本地模型 | VS Code / JetBrains | 🟢 完整 |
| **Cline** | Claude / GPT / Gemini | VS Code | 🟢 完整 |
| **Cursor** | Claude / GPT-4 | IDE | 🟡 部分 |
| **Sourcegraph Cody** | Claude / GPT-4 | VS Code | 🟢 完整 |
| **Zed** | Claude / GPT-4 | 编辑器 | 🟡 部分 |

**现有基础**：

```json
// .claude/mcp.json — 已配置 2 个 MCP Server
{
  "mcpServers": {
    "aitest-tools": {
      "command": "python", "-m", "aitest.mcp_server"
    },
    "aitest-knowledge": {
      "command": "python", "-m", "aitest.knowledge_server"
    }
  }
}
```

**改造清单**：

| 步骤 | 内容 | 文件 |
|------|------|------|
| 1 | 将 Agent 编排暴露为 MCP Tool（`run_test_design_agent` 等） | `aitest/mcp_server.py` |
| 2 | 为 MCP Resources 增加更多 Context 资源 URI | `aitest/knowledge_server.py` |
| 3 | 编写跨客户端适配指南 | 新建 `governance/docs/integration/MCP_CLIENT_GUIDE.md` |

**效果**：用户可以在 Continue.dev / Cline / Cursor 中直接使用 AI 测试能力。

---

### 路径 2：CLI + LLM Provider 抽象 — 命令行层解耦 ⭐ 推荐优先

**核心思路**：将 `aitest` CLI 升级为完整的 Agent 执行入口，通过 LLM Provider 抽象层支持多种模型。

**架构变化**：

```
改造前:
  用户 → Claude Code → Skill 工具调用 → Agent 执行
                              ↓
                     只能使用 Claude 模型

改造后:
  用户 → aitest CLI → LLM Provider 抽象层 → Agent 执行
         │                ├── Claude API (anthropic)
         │                ├── OpenAI API (openai)
         │                ├── Azure OpenAI
         │                ├── 本地模型 (Ollama: qwen3, llama3, ...)
         │                └── 其他 (DeepSeek, Groq, ...)
         │
         └── 纯 Python，无外部平台依赖
```

**核心组件设计**：

```python
# aitest/llm/provider.py — LLM Provider 抽象层

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict]
    token_usage: dict
    model: str

class LLMProvider(ABC):
    """统一的 LLM 调用接口。所有 Provider 实现此接口。"""

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """执行一次 LLM 调用。"""
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """是否支持 tool calling。"""
        pass

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3"):
        from openai import OpenAI  # Ollama 兼容 OpenAI API
        self.client = OpenAI(base_url=base_url + "/v1", api_key="ollama")
        self.model = model


# aitest/llm/skill_runner.py — Skill 执行引擎

def load_skill(skill_id: str) -> str:
    """从 governance/skills/ 加载 Skill Prompt 内容。"""
    skill_path = WORKSTUDY / "governance" / "skills" / f"{skill_id}.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill not found: {skill_id}")
    return skill_path.read_text(encoding="utf-8")

def run_skill(
    skill_id: str,
    user_input: str,
    provider: LLMProvider,
    context: dict = None,
) -> LLMResponse:
    """执行一个 Skill：加载 Prompt → 注入上下文 → 调用 LLM → 返回结果。"""
    system_prompt = load_skill(skill_id)

    # 注入上下文（PROJECT_CONTEXT / MODULE_CONTEXT 等）
    if context:
        context_block = "\n\n".join(
            f"## {key}\n{value}" for key, value in context.items()
        )
        system_prompt += f"\n\n## 当前上下文\n{context_block}"

    return provider.complete(
        system_prompt=system_prompt,
        user_prompt=user_input,
    )
```

**使用方式对比**：

```bash
# 改造前（仅 Claude Code）
/full-sop module=equipment

# 改造后（CLI，支持切换 Provider）
aitest agent run full-sop --module=equipment --provider=claude
aitest agent run test-design --module=equipment --page=alarm-config --provider=openai
aitest agent run automation --module=equipment --page=alarm-config --provider=ollama:qwen3
```

**新增文件清单**：

```
aitest/
├── llm/
│   ├── __init__.py
│   ├── provider.py          # LLMProvider 抽象 + Claude/OpenAI/Ollama 实现
│   ├── skill_runner.py      # Skill 加载 + 执行引擎
│   └── tool_adapter.py       # Tool definition → Provider-specific 格式转换
├── agent_runner.py           # Agent 执行器：Skill 编排 + 上下文注入
└── cli.py                    # 扩展：增加 --provider 参数 + agent run 子命令
```

**依赖**：建议使用 `litellm` 库统一多 Provider 适配，避免手动维护每个 Provider 的 SDK 差异。

**投入估计**：2-3 天。

---

### 路径 3：LangGraph 移植 — 框架层解耦

**核心思路**：用 LangGraph 的 StateGraph 重写 Agent 编排，获得多 LLM 支持 + 可观测性 + 动态路由能力。

> ⚠️ 适合时机：当自研 Workflow Engine 无法满足复杂条件路由需求时再考虑。当前阶段**不建议优先投入**。

**映射关系**：

| 你的架构 | LangGraph 概念 | 说明 |
|---------|---------------|------|
| Context 文档 | `State` (TypedDict) | 图执行过程中的共享状态 |
| Skill | `Node` | 图中的执行节点 |
| Agent | `SubGraph` | 可嵌套的子图 |
| Workflow | `StateGraph` | 顶层编排图 |
| full-sop.workflow.js | `CompiledGraph` | 编译后的可执行图 |
| SOP_STATUS.json | `Checkpointer` | 断点续跑持久化 |
| Event Bus | Stream events | LangGraph 原生流式事件 |

**示例**（test-design-agent 用 LangGraph 重写）：

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage, HumanMessage
from typing import TypedDict

class TestDesignState(TypedDict):
    module: str
    page: str
    page_context: str
    risk_model: str
    test_design: str
    test_cases: str
    errors: list[str]

def node_page_analysis(state: TestDesignState, llm) -> TestDesignState:
    skill_prompt = load_skill("test-design/page-analysis")
    response = llm.invoke([
        SystemMessage(content=skill_prompt),
        HumanMessage(content=f"模块:{state['module']} 页面:{state['page']}")
    ])
    state["page_context"] = response.content
    return state

# ... risk_modeling, testcase_design, write_artifacts 节点类似

builder = StateGraph(TestDesignState)
builder.add_node("page_analysis", node_page_analysis)
builder.add_node("risk_modeling", node_risk_modeling)
builder.add_node("testcase_design", node_testcase_design)
builder.add_node("write_artifacts", node_write_files)

builder.set_entry_point("page_analysis")
builder.add_edge("page_analysis", "risk_modeling")
builder.add_edge("risk_modeling", "testcase_design")
builder.add_edge("testcase_design", "write_artifacts")
builder.add_edge("write_artifacts", END)

graph = builder.compile(checkpointer=SqliteSaver(...))
result = graph.invoke(
    {"module": "equipment", "page": "alarm-config"},
    config={"configurable": {"thread_id": "equipment-alarm-20260612"}}
)
```

**收益**：
- LLM Provider 无关（通过 LangChain ChatModel 抽象，支持 Claude/GPT/Gemini/...）
- 自动获得 LangSmith 可观测性（调用链追踪、Token 统计、延迟监控）
- 内置断点续跑（SqliteSaver / PostgresSaver）
- 原生 Human-in-the-loop（`interrupt()` 等待人工确认）

**成本**：
- 学习 LangGraph 概念
- 8 个 Agent workflow 需重写（可渐进式迁移）
- 新增依赖：`langgraph` + `langchain-core` + `langchain-community`

**何时选择此路径**：
- 当自研 Workflow Engine 无法满足复杂条件路由时
- 当需要 LangSmith 级别的可观测性时
- 当团队已有 LangChain 经验时

---

### 路径 4：Dify 低代码编排 — 业务层解耦

**核心思路**：用 Dify 作为可视化编排层，将 Skill 内容导入为 Prompt 模板，让非开发人员也能使用 AI 测试能力。

**适合场景**：手工测试工程师、业务 BA 需要直接使用 AI 测试能力。

**架构**：

```
Dify 平台
├── 知识库
│   ├── PROJECT_CONTEXT.md  ← 文档知识库
│   ├── known-issues.yaml   ← 结构化知识库
│   └── TECH_ANALYSIS/*.md  ← RAG 检索源
│
├── 工作流（可视化编排）
│   ├── 页面分析流程
│   ├── 代码生成流程
│   └── Bug 分析流程
│
├── Agent 策略
│   ├── test-design-agent  (绑定知识库 + 工具)
│   ├── automation-agent   (绑定代码生成 + 合规检查)
│   └── bug-analysis-agent (绑定 RAG + 日志分析)
│
└── API / Webhook
    ├── POST /api/workflows/run  ← Jenkins 触发
    └── GET  /api/reports        ← Dashboard 数据
```

**优劣势**：

| 优势 | 劣势 |
|------|------|
| 自带 Web UI，零代码编排 | Dify 自身需 Docker 部署 |
| 内置 RAG 引擎 | Prompt 导入有适配成本 |
| 多 LLM Provider 开箱即用 | 复杂并行编排不如代码灵活 |
| API 网关自动生成 | 代码生成需要文件系统写入配置 |

**何时选择此路径**：
- 非开发用户（手工测试工程师/BA）开始使用 AI 测试能力时
- 需要快速搭建 Web UI 而不想自研时

---

### 路径 5：自研 FastAPI 平台 — 完全自主

**核心思路**：在 `aitest/` 之上构建独立的 Web 服务，实现 Agent 编排引擎 + Web UI + API Gateway。

**目标架构**：

```
aitest-platform/
├── server/
│   ├── api/
│   │   ├── agents.py          # POST /api/agent/run   Agent 触发
│   │   ├── workflows.py       # POST /api/workflow/run  Workflow 管理
│   │   ├── reports.py         # GET  /api/report/summary  报告查询
│   │   └── webhooks.py        # POST /api/webhook/jenkins  CI 集成
│   ├── core/
│   │   ├── agent_runner.py    # Agent 执行引擎（复用 Skill 内容）
│   │   ├── skill_loader.py    # Skill Markdown → System Prompt
│   │   ├── context_manager.py # Context 版本化加载
│   │   └── llm_provider.py    # LLM Provider 抽象
│   ├── db/
│   │   ├── models.py          # SQLAlchemy 模型
│   │   └── migrations/
│   └── ui/                    # 前端（初期可选）
│       └── dashboard/         # React/Vue 模块状态 Dashboard
│
├── aitest/                    # 现有模块（不变）
│   ├── rag_engine.py
│   ├── event_bus.py
│   ├── workflow_engine.py
│   ├── agent_scheduler.py
│   └── cli.py
│
└── governance/                # 现有治理层（不变）
    ├── skills/
    ├── context/
    ├── agents/
    └── docs/
```

**分阶段推进**：

| 阶段 | 内容 | 工时 | 依赖 | 产出 |
|------|------|:---:|------|------|
| **P1** | Agent Runner + LLM Provider 抽象 + FastAPI 骨架 | 1-2 周 | 路径 2 完成 | `POST /api/agent/run` 可用 |
| **P2** | Workflow API + Webhook + Jenkins 集成 | 1-2 周 | P1 | CI 失败自动触发 Bug Analysis |
| **P3** | Web Dashboard（模块状态/趋势/覆盖率） | 2-3 周 | P2 | 可视化面板上线 |

**关键技术选型**：

| 组件 | 选择 | 理由 |
|------|------|------|
| Web 框架 | FastAPI | Python 原生，异步支持，自动 OpenAPI |
| 数据库 | SQLite（单机）→ PostgreSQL（多用户） | 零运维起步 |
| LLM 适配 | `litellm` | 统一 100+ Provider 接口 |
| 异步任务 | Celery + Redis（阶段2引入） | 长时间 Agent 执行不能阻塞 HTTP |
| 前端 | React + Vite（阶段3引入） | 渐进式，CLI Dashboard 先行 |

**何时选择此路径**：
- 当需要 API 供外部系统（Jenkins/GitLab CI/飞书）集成时
- 当需要多用户协作时
- 当需要可视化 Dashboard 时

---

### 路径 6：容器化 + 消息队列 — 企业级解耦

**核心思路**：每个 Agent 封装为独立容器，通过消息队列通信，支持弹性伸缩和异构 LLM。

> ⚠️ 远期方案，当前不做详细设计。仅在多项目/大团队/高并发场景下考虑。

```
                       ┌──────────────┐
                       │  API Gateway │  (FastAPI / Kong)
                       └──────┬───────┘
                              │
                       ┌──────┴───────┐
                       │  Task Queue  │  (Celery / Redis Streams)
                       └──────┬───────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ test-design  │   │ automation   │   │ bug-analysis │
   │   Agent Pod  │   │   Agent Pod  │   │   Agent Pod  │
   │ (Claude API) │   │ (GPT-4 API)  │   │ (本地 Ollama) │
   └──────────────┘   └──────────────┘   └──────────────┘
```

- 每个 Agent 独立部署、独立扩缩容
- 不同 Agent 可使用不同 LLM（强项匹配）
- 消息队列解耦，Agent 故障不影响其他 Agent

---

## 三、推荐路线图

```
现在 ──────── 1 个月 ──────── 3 个月 ──────── 6 个月
  │              │                │                │
  ▼              ▼                ▼                ▼
路径 1: MCP    路径 2: CLI       路径 5: FastAPI   路径 5: Web UI
协议解耦       Provider 抽象     平台化骨架       Dashboard
(已完成 60%)   (2-3 天)          (2-3 周)         (2-3 周)
```

### 为什么是这个顺序

1. **路径 1 优先**：你已完成 MCP Server 搭建，只需补充跨客户端文档即可放大现有投资的收益
2. **路径 2 是杠杆点**：投入最低（2-3 天），但实现了 **LLM Provider 无关性**——这是「去平台化」的核心。有了 Provider 抽象层，Skill 内容和 Context 数据就能在任何模型上运行
3. **路径 3（LangGraph）已完成**：`aitest/graphs/sop_graph.py` 已实现完整 SOP 编排，支持断点续跑、HITL interrupt。与 AgentLoop 并行使用
4. **路径 5 已完成（自建 Chat Agent）**：基于 FastAPI + SSE 流式 + AgentLoop.run_interactive() 的自研 Chat Agent 已上线，包含 Web 聊天界面、意图解析、交互式 Agent 执行。消除了 Claude Code 44% 的基础设施 token 浪费
5. **路径 4（Dify）留给未来**：当非开发用户开始使用时考虑
6. **容器化/微服务化留给未来**：当多项目/大团队时考虑

### 当前状态（2026-06-14 更新）

| 路径 | 状态 | 说明 |
|------|:----:|------|
| 1. MCP 优先 | ✅ 完成 | `aitest/mcp/` + `aitest/knowledge_server.py` 就绪 |
| 2. CLI + Provider 抽象 | ✅ 完成 | `aitest sop/agent/skill run`，支持 Claude/OpenAI/Ollama/DeepSeek |
| 3. LangGraph 移植 | ✅ 完成 | `aitest/graphs/sop_graph.py` 完整编排 |
| 4. Dify 低代码编排 | 🔵 未来 | 非开发用户需要时 |
| 5. 自研 FastAPI 平台 | ✅ 完成 | Chat Agent + SSE 流式 + Web UI 已上线 |
| 6. 容器化 + 消息队列 | 🔵 未来 | 多项目/大团队时 |

---

## 四、与已有架构的关系

```
本路线图与已有文档的分工：

governance/docs/
├── architecture/AI_TEST_PLATFORM_ARCHITECTURE_OPTIMIZATION.md  ← 完整架构审计（什么是问题）
├── architecture/ARCHITECTURE_REVIEW_V2_2026-06-13.md          ← V2 架构复审（C+ 评级 → 改进方向）
├── plans/IMPROVEMENT_PLAN_v2.1.md                        ← 3 个改进任务（RAG/Event/接口）
├── plans/PLATFORM_INDEPENDENCE_ROADMAP.md                 ← ★ 你正在读：去平台化路线图
├── plans/SELF_HOSTED_CHAT_AGENT_PLAN.md                  ← 🆕 自建 Chat Agent 实施计划（5 Phase）
└── plans/WEB_DASHBOARD_PLAN.md                            ← Web 仪表盘计划

关系：
  架构审计（发现 7 个问题）
    ├── 短期改进（3 个任务）→ IMPROVEMENT_PLAN_v2.1.md
    ├── 长期演进（去平台化）→ PLATFORM_INDEPENDENCE_ROADMAP.md
    └── 自建 Agent（省 44% token）→ SELF_HOSTED_CHAT_AGENT_PLAN.md
```

**本路线图与已有资产的关系**：

```
现有资产                    去平台化后的角色
─────────────────────────────────────────────────
governance/skills/*.md     → Skill 内容（不变，被 agent_runner 读取）
governance/context/        → Context 数据（不变，被 context_manager 读取）
governance/agents/*.js     → Agent 编排定义（路径2保留兼容，路径5用Python重写）
aitest/rag_engine.py       → RAG 引擎（不变）
aitest/event_bus.py        → Event Bus（不变）
aitest/workflow_engine.py  → Workflow Engine（不变，FastAPI 包装）
aitest/agent_scheduler.py  → Agent Scheduler（不变，FastAPI 包装）
aitest/mcp_server.py       → MCP Server（不变，加 Tools）
aitest/cli.py              → CLI 入口（扩展 --provider 参数）
.claude/skills/            → 斜杠命令（保留作为 Claude Code 入口，新增 CLI 作为通用入口）
```

---

## 五、风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|:---:|:---:|------|
| Provider 抽象层不够抽象，Claude 特定 Prompt 在其他模型上效果差 | 高 | 中 | 先在 2-3 个 Skill 上做 A/B 测试，建立 Prompt 适配指南 |
| litellm 依赖不稳定 | 低 | 中 | litellm 是成熟项目（10k+ stars），降级方案：直接使用各 SDK |
| 本地模型（Ollama）token 限制导致长 Context 截断 | 中 | 中 | Skill 分级：复杂 Skill 限制使用 128k 模型，简单 Skill 可用本地模型 |
| FastAPI 化后 Token 成本上升（每次 API 调用重新加载 Context） | 中 | 低 | RAG 分层加载 + Context 缓存 |
| 去平台化后维护两套入口（Claude Code + CLI）增加负担 | 中 | 低 | Claude Code 入口保留兼容但不新增功能，新功能仅通过 CLI 发布 |

---

## 六、后续行动

### 立即执行（本周）

- [x] 阅读本路线图，确认推荐顺序（路径 1→2→5）
- [x] 补充 MCP 跨客户端文档（`MCP_CLIENT_GUIDE.md`） — 2026-06-14 更新 v1.1

### 1 个月内

- [x] 实现路径 2：LLM Provider 抽象 + Skill Runner
  - `aitest/llm/provider.py` — Claude / OpenAI / Ollama / **DeepSeek** (新增) + 工厂函数
  - `aitest/llm/skill_loader.py` — Skill 加载 + Variant 支持
  - `aitest/llm/skill_registry.py` — 分级矩阵 + 兼容性检查
  - `aitest/llm/context_injector.py` — RAG + 文件 + 缓存
  - `aitest/llm/prompt_adapter.py` — 跨模型 Prompt 适配
  - `aitest/agent_runner.py` — `run_skill()` / `run_agent()` / `AgentLoop` 全部支持 `--provider`
  - `aitest/cli.py` — `aitest skill run` / `aitest agent run` 支持 `--provider`
- [x] ~~在 2-3 个 Skill 上验证多 Provider 效果~~ → `aitest/provider_verify.py` 已创建，待 API Key 就绪后执行
- [x] 建立 Prompt 适配指南 → `governance/docs/guides/PROMPT_ADAPTATION_GUIDE.md`

### 3 个月内

- [x] FastAPI 骨架 + Agent Runner API (`aitest/server/` 已上线)
- [ ] Jenkins Webhook 集成（CI 失败 → 自动触发 Bug Analysis）
- [ ] 使用 `dev-agent` 生态完成前后端分离（chat.html → Vue 3 独立项目）

### 6 个月内

- [ ] Web Dashboard（模块状态/趋势/覆盖率）
- [ ] 评估是否需要引入 Dify（如果非开发用户开始使用）

---

## 附录：相关文件索引

| 文件 | 说明 |
|------|------|
| `CLAUDE.md` | 项目入口，AI 第一阅读文件 |
| `governance/README.md` | 治理层骨架说明 |
| `governance/docs/architecture/AI_TEST_PLATFORM_ARCHITECTURE_OPTIMIZATION.md` | 完整架构审计（现状+优化） |
| `governance/docs/plans/IMPROVEMENT_PLAN_v2.1.md` | 短期改进计划（RAG/Event/接口） |
| `governance/docs/plans/PLATFORM_INDEPENDENCE_ROADMAP.md` | ★ 本文件 |
| `governance/docs/integration/MCP_CLIENT_GUIDE.md` | MCP 跨客户端配置指南 (v1.1) |
| `governance/docs/guides/PROMPT_ADAPTATION_GUIDE.md` | ★ 新增：跨模型 Prompt 适配指南 |
| `aitest/cli.py` | CLI 入口（10 子命令，--provider 参数） |
| `aitest/llm/provider.py` | LLM Provider 抽象层（4 Provider） |
| `aitest/llm/skill_loader.py` | Skill 加载器 + Variant 支持 |
| `aitest/llm/skill_registry.py` | Skill 能力分级 + Provider 兼容性检查 |
| `aitest/llm/context_injector.py` | 上下文注入器（RAG + 文件 + 缓存） |
| `aitest/llm/prompt_adapter.py` | 跨模型 Prompt 适配器 |
| `aitest/provider_verify.py` | ★ 新增：多 Provider 验证脚本 |
| `aitest/mcp/` | MCP Server 模块化包（P3 架构） |
| `aitest/knowledge_server.py` | MCP Server — aitest-knowledge |
| `aitest/rag_engine.py` | RAG 引擎（ChromaDB） |
| `aitest/event_bus.py` | Event Bus（4 事件类型） |
| `aitest/agent_scheduler.py` | Agent 调度器（状态机） |
| `aitest/workflow_engine.py` | Workflow 引擎（YAML DAG） |
| `.claude/mcp.json` | MCP 配置 |

---

> **2026-06-14 更新**：路径 1→2→5 核心任务全部完成。路径 2 新增 DeepSeekProvider + 验证脚本 + Prompt 适配指南。下一优先级：前后端分离（Vue 3 独立项目）+ Jenkins Webhook 集成。
