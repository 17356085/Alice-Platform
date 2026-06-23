# 去平台化实施计划 v1.0

> **来源**：`PLATFORM_INDEPENDENCE_ROADMAP.md`（去平台化路线图）→ 提取立即执行 + 1 个月内的任务
> **目标**：交付给独立 AI 会话执行，无需原始对话上下文
> **前提**：请先阅读 `governance/docs/plans/PLATFORM_INDEPENDENCE_ROADMAP.md` 了解六条路径的全貌
> **本项目入口**：`CLAUDE.md`（AI 第一阅读文件）

---

## 快速导航

| Phase | 内容 | 优先级 | 预计工时 | 依赖 |
|-------|------|:---:|:---:|------|
| [Phase 1：MCP Agent 编排 Tools](#phase-1mcp-agent-编排-tools) | 路径 1 收尾 | P0 | 1-2h | 无 |
| [Phase 2：LLM Provider 抽象层](#phase-2llm-provider-抽象层) | 路径 2 核心 | P0 | 3-4h | 无 |
| [Phase 3：PromptAdapter + Skill Runner](#phase-3promptadapter--skill-runner) | 路径 2 引擎 | P1 | 2-3h | Phase 2 |
| [Phase 4：FastAPI 骨架](#phase-4fastapi-骨架) | 路径 5 P1 | P2 | 2-3h | Phase 2 完成更佳 |
| [Phase 5：整合测试](#phase-5整合测试) | 端到端验证 | P2 | 1h | Phase 1-4 |

---

## 背景（给接手 AI 的上下文）

### 项目是什么

鞍集涂源管理系统（Vue 3 + Element Plus）的 AI 辅助自动化测试项目。Python 3.x + pytest + Selenium。

### 当前架构

```
Skill (28个 Markdown Prompt) → Agent (8个 Skill 编排器) → Workflow (full-sop 全流程)
```

- **已有平台无关资产**：`aitest/` 目录（rag_engine, event_bus, workflow_engine, agent_scheduler, mcp_server, knowledge_server, cli, bug_history）
- **已有 MCP Server**：2 个（aitest-tools: 5 Tools, aitest-knowledge: Resources 参数化加载）
- **已有 ChromaDB RAG**：5 集合 235 文档
- **当前耦合点**：Agent 调用依赖 Claude Code 的 Skill/Workflow 工具，LLM 只支持 Claude

### 本次实施目标

1. 将 Agent 编排能力暴露为 MCP Tool（其他客户端可调用）
2. 建立 LLM Provider 抽象层（Claude / OpenAI / 本地模型可切换）
3. 搭建 FastAPI 骨架（为后续平台化铺路）

### 关键文件路径

```
WorkStudy/
├── aitest/                          ← ★ 本次改动主目录
│   ├── mcp_server.py               ← Phase 1 改动
│   ├── cli.py                       ← Phase 2/3 改动
│   ├── agent_runner.py             ← Phase 3 新建
│   ├── llm/                         ← Phase 2/3 新建目录
│   │   ├── __init__.py
│   │   ├── provider.py
│   │   ├── skill_registry.py
│   │   ├── skill_loader.py
│   │   ├── prompt_adapter.py
│   │   └── context_injector.py
│   └── server/                      ← Phase 4 新建目录
│       ├── __init__.py
│       ├── api/agents.py
│       ├── api/webhooks.py
│       ├── core/context_cache.py
│       └── main.py
├── governance/
│   ├── docs/
│   │   ├── PLATFORM_INDEPENDENCE_ROADMAP.md   ← 背景阅读
│   │   └── IMPLEMENTATION_PLAN_PLATFORM_INDEPENDENCE.md ← ★ 你正在读
│   ├── skills/                     ← Skill 内容（不改动，只读取）
│   └── context/                    ← Context 数据（不改动，只读取）
└── requirements.txt                ← Phase 2 新增依赖
```

### 当前 Python 环境

```
已安装: chromadb 1.5.9, mcp 1.27.2, uvicorn 0.49.0
需安装: anthropic, openai, litellm, fastapi, pydantic, python-multipart
```

---

## Phase 1：MCP Agent 编排 Tools

### 目标

在现有 `aitest/mcp_server.py` 中新增 3 个 Agent 编排 Tool，让任何 MCP 客户端都能触发 Agent 执行。

### 背景

现有 MCP Server 提供了 5 个 Tool（check_code_quality, get_module_status, rag_search_known_issues, run_test, generate_report），但缺少 Agent 编排入口。其他 MCP 客户端可以调用你的工具，但无法执行「页面分析→代码生成」的完整 Agent 流程。

### 改动清单

#### 1-A：在 mcp_server.py 中新增 3 个 Tool 定义

文件：`aitest/mcp_server.py`

在 `list_tools()` 函数的 `return [...]` 列表末尾，与其他 Tool 平级，新增 3 个 Tool：

```python
# Tool 6: run_test_design_agent
Tool(
    name="run_test_design_agent",
    description="执行测试设计 Agent：页面分析 → 风险建模 → 测试用例设计。产出 PAGE_CONTEXT.md + RISK_MODEL.md + TEST_DESIGN.md + TEST_CASES.md",
    inputSchema={
        "type": "object",
        "properties": {
            "module": {
                "type": "string",
                "description": "模块名，如 equipment, tank, personnel, system-user"
            },
            "page": {
                "type": "string",
                "description": "页面名（slug 格式），如 alarm-config, unit-management"
            },
            "options": {
                "type": "string",
                "description": "可选参数（JSON 格式），如 '{\"skip_page_analysis\": true}'",
                "default": "{}"
            }
        },
        "required": ["module", "page"]
    }
),
# Tool 7: run_automation_agent
Tool(
    name="run_automation_agent",
    description="执行自动化 Agent：技术分析 → 定位器设计 → PageObject 生成 → 测试脚本生成 → 合规检查。产出 TECH_ANALYSIS.md + AUTO_STRATEGY.md + PageObject.py + test_*.py + conftest.py",
    inputSchema={
        "type": "object",
        "properties": {
            "module": {"type": "string", "description": "模块名"},
            "page": {"type": "string", "description": "页面名（slug 格式）"},
            "options": {"type": "string", "description": "可选参数（JSON 格式）", "default": "{}"}
        },
        "required": ["module", "page"]
    }
),
# Tool 8: run_full_sop
Tool(
    name="run_full_sop",
    description="端到端 SOP 编排：按 Phase 0→9 自动串联 8 个 Agent。支持断点续跑、失败自动分流。这是最完整的入口，一键完成整个模块的测试体系建设",
    inputSchema={
        "type": "object",
        "properties": {
            "module": {"type": "string", "description": "模块名"},
            "mode": {
                "type": "string",
                "description": "执行模式: full(全流程) | resume(断点续跑) | status(仅查看进度) | from-automation(从自动化阶段开始)",
                "enum": ["full", "resume", "status", "from-automation"],
                "default": "full"
            },
            "pages": {
                "type": "string",
                "description": "指定页面列表（逗号分隔），如 'alarm-config,unit-management'。不指定则自动发现"
            }
        },
        "required": ["module"]
    }
),
```

#### 1-B：在 call_tool() 中新增 case 分支

文件：`aitest/mcp_server.py`

在 `call_tool()` 函数的 `if name == "..."` 分支末尾新增 3 个 case：

```python
elif name == "run_test_design_agent":
    module = arguments.get("module", "")
    page = arguments.get("page", "")
    options_str = arguments.get("options", "{}")
    try:
        options = json.loads(options_str)
    except json.JSONDecodeError:
        options = {}
    
    # 检查前置条件：MODULE_CONTEXT 是否存在
    module_context = CONTEXT_MODULES / module / "MODULE_CONTEXT.md"
    if not module_context.exists():
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "blocked",
                "reason": f"MODULE_CONTEXT.md 不存在。请先执行 requirement-agent 完成模块建模",
                "suggested_action": f"使用 run_full_sop module={module} mode=full 从项目初始化开始"
            }, ensure_ascii=False)
        )]
    
    # 构造 Skill 调用参数
    skill_args = f"module={module} page={page}"
    if options.get("skip_page_analysis"):
        skill_args += " skip_page_analysis=true"
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "triggered",
            "agent": "test-design-agent",
            "module": module,
            "page": page,
            "message": f"请在 AI 客户端中执行: /test-design-agent {skill_args}",
            "note": "Agent 执行需要 AI 客户端的 LLM 能力，MCP Tool 负责触发和传参。执行完成后请检查 governance/context/projects/web-automation/modules/{module}/pages/{page}/ 目录下的产出文件。"
        }, ensure_ascii=False)
    )]

elif name == "run_automation_agent":
    module = arguments.get("module", "")
    page = arguments.get("page", "")
    
    # 检查前置条件：PAGE_CONTEXT + TEST_CASES 是否存在
    page_dir = CONTEXT_MODULES / module / "pages" / page
    missing = []
    for doc in ["PAGE_CONTEXT.md", "TEST_CASES.md"]:
        if not (page_dir / doc).exists():
            missing.append(doc)
    
    if missing:
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "blocked",
                "reason": f"缺少前置产物: {', '.join(missing)}",
                "suggested_action": f"使用 run_test_design_agent module={module} page={page} 先完成测试设计"
            }, ensure_ascii=False)
        )]
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "triggered",
            "agent": "automation-agent",
            "module": module,
            "page": page,
            "message": f"请在 AI 客户端中执行: /automation-agent module={module} pageName={page}",
            "note": "执行完成后请检查 ZJSN_Test-master526/page/{module}_page/ 和 script/{module}/ 目录下的代码文件"
        }, ensure_ascii=False)
    )]

elif name == "run_full_sop":
    module = arguments.get("module", "")
    mode = arguments.get("mode", "full")
    pages_str = arguments.get("pages", "")
    pages = [p.strip() for p in pages_str.split(",") if p.strip()] if pages_str else []
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "triggered",
            "agent": "full-sop",
            "module": module,
            "mode": mode,
            "pages": pages,
            "message": f"请在 AI 客户端中执行: /full-sop module={module} mode={mode}" + (f" pages={','.join(pages)}" if pages else ""),
            "note": "全流程编排会自动串联 8 个 Agent，预计耗时 10-20 分钟。支持断点续跑 (mode=resume)。"
        }, ensure_ascii=False)
    )]
```

#### 1-C：更新 .claude/mcp.json 描述

文件：`.claude/mcp.json`

将 `aitest-tools` 的 `description` 更新为：
```json
"description": "AI 测试平台工具集：代码质量检查、已知问题搜索、模块状态查询、自动化覆盖率、Agent 编排（test-design / automation / full-sop）"
```

### 验收标准

1. `python -m aitest.mcp_server` 启动无报错
2. 任意 MCP 客户端列出 Tools 时能看到 `run_test_design_agent`、`run_automation_agent`、`run_full_sop`
3. 调用 `run_test_design_agent` 且 MODULE_CONTEXT.md 不存在时，返回 `"status": "blocked"` 及建议操作
4. 调用 `run_full_sop mode=status` 返回进度查询提示

---

## Phase 2：LLM Provider 抽象层

### 目标

建立统一的 LLM 调用接口，支持 Claude / OpenAI / Ollama 三种 Provider 的切换。后续新增 Provider 只需实现一个接口。

### 新增依赖

```bash
pip install anthropic openai litellm
```

> 注意：安装后需在 `.env` 中配置对应 API Key。已有 `.env.example` 文件，按需添加 `OPENAI_API_KEY` 和 `ANTHROPYC_API_KEY`。

### 改动清单

#### 2-A：新建 aitest/llm/__init__.py

文件：`aitest/llm/__init__.py`（新建）

```python
"""LLM Provider 抽象层 — 统一 Claude / OpenAI / Ollama 调用接口。"""
from aitest.llm.provider import (
    LLMProvider,
    LLMResponse,
    ClaudeProvider,
    OpenAIProvider,
    OllamaProvider,
    get_provider,
)
```

#### 2-B：新建 aitest/llm/provider.py（核心文件）

文件：`aitest/llm/provider.py`（新建，~180 行）

核心设计要点：
1. `LLMResponse` dataclass — 统一返回格式（content, tool_calls, token_usage, model）
2. `LLMProvider` ABC — 定义 `complete()` 抽象方法 + `supports_tools()` 
3. `ClaudeProvider` — 使用 `anthropic` SDK，映射到 Anthropic Messages API
4. `OpenAIProvider` — 使用 `openai` SDK，映射到 Chat Completions API
5. `OllamaProvider` — 使用 `openai` SDK 兼容模式（Ollama 的 `/v1` 端点兼容 OpenAI API）
6. `get_provider(name)` 工厂函数 — 根据字符串名返回 Provider 实例

关键实现细节：

```python
# 伪代码骨架（交给接手 AI 实现）
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()  # 自动读取 .env 中的 API Key

@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    token_usage: dict = field(default_factory=dict)
    model: str = ""

class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str,
                 tools: Optional[list] = None, temperature: float = 0.7,
                 max_tokens: int = 8192) -> LLMResponse:
        """执行一次 LLM 调用。"""
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """是否支持 native tool calling。"""
        pass

class ClaudeProvider(LLMProvider):
    def __init__(self, model="claude-sonnet-4-6"):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
    # ... 实现 complete() 使用 self.client.messages.create()
    # ... Claude 的 tool calling 格式与 OpenAI 不同，需要转换

class OpenAIProvider(LLMProvider):
    def __init__(self, model="gpt-4o"):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
    # ... 实现 complete() 使用 self.client.chat.completions.create()

class OllamaProvider(LLMProvider):
    def __init__(self, model="qwen3", base_url="http://localhost:11434"):
        from openai import OpenAI
        self.client = OpenAI(base_url=f"{base_url}/v1", api_key="ollama")
        self.model = model
    # ... 实现 complete()，supports_tools() 返回 False（本地模型通常不支持）

def get_provider(name: str = "claude", **kwargs) -> LLMProvider:
    """工厂函数：根据名称创建 Provider 实例。
    
    用法:
        provider = get_provider("claude")
        provider = get_provider("openai", model="gpt-4o-mini")
        provider = get_provider("ollama", model="qwen3", base_url="http://localhost:11434")
    """
    providers = {
        "claude": ClaudeProvider,
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
    }
    if name not in providers:
        raise ValueError(f"Unknown provider: {name}. Available: {list(providers.keys())}")
    return providers[name](**kwargs)
```

#### 2-C：在 .env.example 中新增配置项

文件：`ZJSN_Test-master526/.env.example`（如果 `.env` 实际位置不同，请在项目中搜索 `.env` 文件定位）

新增：
```bash
# LLM Provider 配置
ANTHROPIC_API_KEY=sk-ant-xxx    # Claude API Key
OPENAI_API_KEY=sk-xxx           # OpenAI API Key（可选）
OLLAMA_BASE_URL=http://localhost:11434  # Ollama 地址（可选）
DEFAULT_LLM_PROVIDER=claude     # 默认使用的 LLM Provider
```

### 验收标准

1. `from aitest.llm import get_provider` 可正常导入
2. `get_provider("claude")` 返回 `ClaudeProvider` 实例
3. `get_provider("openai")` 返回 `OpenAIProvider` 实例
4. `get_provider("unsupported")` 抛出 `ValueError`
5. Provider 实例的 `complete()` 方法调用成功（需有效 API Key）

---

## Phase 3：PromptAdapter + Skill Runner

### 目标

建立 Skill 加载、Prompt 适配、上下文注入的完整引擎，让 Skill 能在任何 LLM Provider 上运行。

### 改动清单

#### 3-A：新建 aitest/llm/skill_loader.py

文件：`aitest/llm/skill_loader.py`（新建，~80 行）

核心功能：
1. `load_skill(skill_id: str) -> str` — 根据 Skill ID 读取 Markdown 文件
2. `list_skills(category: str = None) -> list[str]` — 列出所有可用 Skill
3. `get_skill_metadata(skill_id: str) -> dict` — 从 `skill-registry.yaml` 获取 Skill 元数据

Skill ID 格式：`{category}/{skill-name}`，如 `test-design/page-analysis`。
文件路径映射：`governance/skills/{category}/{skill-name}.md`

```python
# 伪代码骨架
def load_skill(skill_id: str) -> str:
    """加载 Skill Prompt 内容。"""
    # skill_id 格式: "test-design/page-analysis"
    skill_path = GOVERNANCE / "skills" / f"{skill_id}.md"
    if not skill_path.exists():
        # 尝试从 skill-registry.yaml 查找实际路径
        registry = load_registry()
        for s in registry.get("skills", []):
            if s["id"] == skill_id or s["id"] == skill_id.split("/")[-1]:
                skill_path = GOVERNANCE / s["file"]
                break
    
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill not found: {skill_id}. Searched: {skill_path}")
    
    return skill_path.read_text(encoding="utf-8")
```

#### 3-B：新建 aitest/llm/prompt_adapter.py

文件：`aitest/llm/prompt_adapter.py`（新建，~120 行）

核心功能：
1. 根据目标 Provider 类型适配 Skill Prompt
2. 本地模型：去除 XML tags、增加示例、截断过长的 system prompt
3. Claude：保持原样（Skill 就是为 Claude 优化的）
4. GPT-4o：保持基本不变，仅限制 system prompt 长度

```python
# 伪代码骨架
class PromptAdapter:
    def adapt(self, skill_prompt: str, provider_type: str, 
              context: str = "") -> str:
        """将 Skill Prompt 适配到目标 Provider。"""
        config = self.ADAPTATIONS.get(provider_type, {})
        adapted = skill_prompt
        
        # 本地模型适配
        if config.get("strip_xml_tags"):
            adapted = self._xml_to_markdown(adapted)
        if config.get("add_examples"):
            adapted = self._inject_examples(adapted)
        
        # 注入上下文
        if context:
            adapted += f"\n\n## 当前上下文\n{context}"
        
        # 截断
        max_len = config.get("max_system_length", 32000)
        if len(adapted) > max_len:
            adapted = adapted[:max_len-200] + "\n\n[截断] 超出模型限制..."
        
        return adapted
```

#### 3-C：新建 aitest/llm/context_injector.py

文件：`aitest/llm/context_injector.py`（新建，~100 行）

核心功能：
1. 根据 Skill ID 自动判断需要注入哪些 Context
2. 从 ChromaDB RAG 按需检索相关片段（而非全量加载）
3. 构造注入到 Skill Prompt 的上下文块

```python
# 伪代码骨架
SKILL_CONTEXT_MAP = {
    # Skill ID → 需要的 Context（按优先级排列）
    "test-design/page-analysis": [
        {"type": "project_context", "heading": "BasePage API"},
        {"type": "project_context", "heading": "Element Plus 坑位"},
    ],
    "automation/tech-analysis": [
        {"type": "project_context", "heading": "定位器规范"},
        {"type": "project_context", "heading": "Element Plus 坑位"},
        {"type": "page_context", "module": "{module}", "page": "{page}"},
    ],
    "automation/page-object-generator": [
        {"type": "project_context", "heading": "代码红线"},
        {"type": "page_objects", "query": "类似页面"},  # RAG 检索
    ],
    "diagnosis/bug-analysis": [
        {"type": "known_issues", "query": "{error_msg}"},  # RAG 检索
    ],
}

class ContextInjector:
    def inject(self, skill_id: str, skill_prompt: str, 
               variables: dict = None) -> str:
        """为 Skill Prompt 注入相关上下文。"""
        context_map = SKILL_CONTEXT_MAP.get(skill_id, [])
        if not context_map:
            return skill_prompt
        
        context_blocks = []
        for ctx in context_map:
            content = self._resolve_context(ctx, variables)
            if content:
                context_blocks.append(content)
        
        if context_blocks:
            context_text = "\n\n---\n\n".join(context_blocks)
            return f"{skill_prompt}\n\n## 参考上下文\n{context_text}"
        return skill_prompt
```

#### 3-D：新建 aitest/agent_runner.py（核心编排文件）

文件：`aitest/agent_runner.py`（新建，~200 行）

这是整个去平台化的核心——Skill 编排引擎。

核心功能：
1. `run_skill(skill_id, user_input, provider, context_vars) -> LLMResponse` — 执行单个 Skill
2. `run_agent(agent_name, **kwargs) -> dict` — 执行一个 Agent（多个 Skill 编排）
3. 编排逻辑复用 Agent .md 中的定义

```python
# 伪代码骨架
def run_skill(
    skill_id: str,
    user_input: str,
    provider: str = "claude",
    context_vars: dict = None,
) -> LLMResponse:
    """
    执行单个 Skill：加载 → 注入上下文 → 适配 Prompt → 调用 LLM。
    
    用法:
        result = run_skill(
            "test-design/page-analysis",
            "分析 equipment 模块的 alarm-config 页面",
            provider="openai",
            context_vars={"module": "equipment", "page": "alarm-config"}
        )
    """
    from aitest.llm.skill_loader import load_skill
    from aitest.llm.prompt_adapter import PromptAdapter
    from aitest.llm.context_injector import ContextInjector
    from aitest.llm.provider import get_provider
    
    # 1. 加载 Skill Prompt
    system_prompt = load_skill(skill_id)
    
    # 2. 注入上下文
    injector = ContextInjector()
    system_prompt = injector.inject(skill_id, system_prompt, context_vars)
    
    # 3. 适配到目标 Provider
    adapter = PromptAdapter()
    system_prompt = adapter.adapt(system_prompt, provider)
    
    # 4. 创建 Provider 实例并调用
    llm = get_provider(provider)
    response = llm.complete(
        system_prompt=system_prompt,
        user_prompt=user_input,
    )
    
    return response


def run_agent(
    agent_name: str,
    provider: str = "claude",
    **kwargs,
) -> dict:
    """
    执行一个 Agent（多个 Skill 编排）。
    
    用法:
        result = run_agent(
            "test-design-agent",
            module="equipment",
            page="alarm-config",
            provider="openai"
        )
    """
    # Agent → Skill 映射（读取自 governance/agents/README.md）
    AGENT_SKILL_MAP = {
        "test-design-agent": [
            "test-design/page-analysis",
            "test-design/risk-modeling",
            "test-design/testcase-design",
        ],
        "automation-agent": [
            "automation/tech-analysis",
            "automation/auto-strategy",
            "automation/page-object-generator",
            "automation/test-script-generator",
            "automation/code-consistency-checker",
        ],
        "bug-analysis-agent": [
            "diagnosis/bug-analysis",
        ],
        "report-agent": [
            "reporting/report-generator",
        ],
    }
    
    skills = AGENT_SKILL_MAP.get(agent_name, [])
    if not skills:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    results = {}
    context_vars = kwargs.copy()
    
    for skill_id in skills:
        # 构造 Skill 的用户输入
        user_input = f"模块: {kwargs.get('module', 'N/A')}"
        if kwargs.get("page"):
            user_input += f", 页面: {kwargs['page']}"
        
        # 执行 Skill
        response = run_skill(
            skill_id=skill_id,
            user_input=user_input,
            provider=provider,
            context_vars=context_vars,
        )
        
        # 记录结果，传递给下一个 Skill
        results[skill_id] = response
        context_vars[f"prev_{skill_id.split('/')[-1]}"] = response.content[:2000]
    
    return {
        "agent": agent_name,
        "provider": provider,
        "skills_executed": len(skills),
        "results": {k: {"model": v.model, "tokens": v.token_usage} 
                     for k, v in results.items()},
    }
```

#### 3-E：扩展 aitest/cli.py 增加 Skill/Agent 执行子命令

文件：`aitest/cli.py`

在现有的 `main()` 函数中，在 `sub.add_parser("bug", ...)` 之前新增两个子命令：

```python
# ── skill ──
p_skill = sub.add_parser("skill", help="Skill 执行")
p_skill.add_argument("skill_id", help="Skill ID (如 test-design/page-analysis)")
p_skill.add_argument("--input", "-i", required=True, help="用户输入")
p_skill.add_argument("--provider", "-p", default="claude", 
                     choices=["claude", "openai", "ollama"],
                     help="LLM Provider")
p_skill.add_argument("--module", help="模块名（上下文注入用）")
p_skill.add_argument("--page", help="页面名（上下文注入用）")

# ── agent ──  (扩展已有，增加 run 子命令)
# 在已有的 p_agent 中增加 run action
# 或者新建 p_agent_run 子命令
```

对应的 CLI 命令实现：

```python
def cmd_skill(args):
    """执行单个 Skill。"""
    from aitest.agent_runner import run_skill
    
    print(f"Skill: {args.skill_id}")
    print(f"Provider: {args.provider}")
    print(f"Input: {args.input[:80]}...")
    print()
    
    response = run_skill(
        skill_id=args.skill_id,
        user_input=args.input,
        provider=args.provider,
        context_vars={
            "module": args.module or "",
            "page": args.page or "",
        },
    )
    
    print(f"Model: {response.model}")
    print(f"Tokens: {response.token_usage}")
    print(f"\n--- Response ---\n{response.content[:2000]}")
```

### 验收标准

1. `from aitest.agent_runner import run_skill` 可正常导入
2. `run_skill("test-design/page-analysis", "分析 equipment/alarm-config", provider="claude")` 执行成功
3. 输出包含 Context 注入痕迹（如「当前上下文」块）
4. `aitest skill test-design/page-analysis --input "分析 tank 模块" --provider claude --module tank` CLI 可用

---

## Phase 4：FastAPI 骨架

### 目标

搭建 FastAPI 服务骨架，暴露 Agent 触发 API + Jenkins Webhook 端点。

### 新增依赖

```bash
pip install fastapi pydantic python-multipart
# uvicorn 已安装 (0.49.0)
```

### 改动清单

#### 4-A：新建 aitest/server/ 目录结构

```
aitest/server/
├── __init__.py
├── main.py                  ← FastAPI 应用入口
├── api/
│   ├── __init__.py
│   ├── agents.py            ← /api/agent/run, /api/agent/status
│   └── webhooks.py          ← /api/webhook/jenkins
└── core/
    ├── __init__.py
    └── context_cache.py     ← Context 分层缓存
```

#### 4-B：aitest/server/main.py

文件：`aitest/server/main.py`（新建，~40 行）

```python
"""AI Test Platform — FastAPI 服务入口。"""
from fastapi import FastAPI
from aitest.server.api import agents, webhooks

app = FastAPI(
    title="AI Test Platform",
    description="AI 自动化测试平台 API — Agent 触发、Workflow 管理、报告查询",
    version="0.1.0",
)

app.include_router(agents.router)
app.include_router(webhooks.router)

@app.get("/")
async def root():
    return {
        "name": "AI Test Platform",
        "version": "0.1.0",
        "docs": "/docs",
    }

@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 4-C：aitest/server/api/agents.py

文件：`aitest/server/api/agents.py`（新建，~80 行）

核心 API：
1. `POST /api/agent/run` — 触发 Agent 执行（接受 JSON body，返回 run_id）
2. `GET /api/agent/status/{run_id}` — 查询执行进度
3. `GET /api/module/{module}/status` — 查询模块 SOP 进度（调用 agent_scheduler）

```python
"""Agent 触发 API。"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/agent", tags=["Agents"])

class AgentRunRequest(BaseModel):
    agent: str  # test-design-agent | automation-agent | bug-analysis-agent | report-agent
    module: str
    page: Optional[str] = None
    provider: str = "claude"
    mode: str = "full"

@router.post("/run")
async def trigger_agent(req: AgentRunRequest):
    """触发 Agent 执行。"""
    # Phase 4 MVP：直接同步执行（后续版本改为后台任务）
    from aitest.agent_runner import run_agent
    
    try:
        result = run_agent(
            agent_name=req.agent,
            provider=req.provider,
            module=req.module,
            page=req.page,
        )
        return {
            "status": "completed",
            "agent": req.agent,
            "module": req.module,
            "skills_executed": result["skills_executed"],
            "results": result["results"],
        }
    except Exception as e:
        return {
            "status": "failed",
            "agent": req.agent,
            "error": str(e),
        }

@router.get("/status/{module}")
async def module_sop_status(module: str):
    """查询模块 SOP 进度。"""
    from aitest.agent_scheduler import check_preconditions
    return check_preconditions(module)
```

#### 4-D：aitest/server/api/webhooks.py

文件：`aitest/server/api/webhooks.py`（新建，~40 行）

```python
"""Webhook 端点 — Jenkins/GitLab CI 集成。"""
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/webhook", tags=["Webhooks"])

@router.post("/jenkins")
async def jenkins_webhook(request: Request):
    """Jenkins CI 完成时触发。
    
    Pipeline 成功 → 提示生成测试报告
    Pipeline 失败 → 提示执行 Bug 分析
    """
    payload = await request.json()
    build_status = payload.get("build_status", "UNKNOWN")
    module = payload.get("module", "")

    if build_status == "FAILURE":
        return {
            "action": "trigger_bug_analysis",
            "module": module,
            "suggested_command": f"/bug-analysis-agent module={module} mode=batch",
            "note": "请在 AI 客户端中执行上述命令，或调用 POST /api/agent/run"
        }
    elif build_status == "SUCCESS":
        return {
            "action": "trigger_report",
            "module": module,
            "suggested_command": f"/report-agent module={module} mode=summary",
        }
    else:
        return {"action": "no_action", "build_status": build_status}
```

#### 4-E：aitest/server/core/context_cache.py

文件：`aitest/server/core/context_cache.py`（新建，~100 行）

核心功能（与之前讨论的一致）：
1. L1 内存缓存（Python dict, TTL 5min）
2. L2 ChromaDB RAG 检索（按需加载 chunk）
3. L3 磁盘读取（L1/L2 miss 时）

### 启动方式

```bash
# 启动 FastAPI 服务
python -m aitest.server.main

# 或
uvicorn aitest.server.main:app --reload --port 8000

# 访问 API 文档
open http://localhost:8000/docs
```

### 验收标准

1. `python -m aitest.server.main` 启动无报错
2. `curl http://localhost:8000/health` 返回 `{"status": "ok"}`
3. `curl http://localhost:8000/docs` 可访问 Swagger UI
4. `POST /api/agent/run` 可触发 Agent 执行（需有效 API Key）
5. `GET /api/agent/status/{module}` 返回模块 SOP 进度 JSON

---

## Phase 5：整合测试

### 目标

端到端验证：通过 CLI / MCP / API 三种入口，分别完成一个 Agent 的执行。

### 测试用例

#### 测试 1：CLI 执行单个 Skill

```bash
# 使用 Claude
aitest skill test-design/risk-modeling \
  --input "分析 equipment/alarm-config 页面的测试风险" \
  --provider claude \
  --module equipment \
  --page alarm-config

# 使用 OpenAI（如果配置了 API Key）
aitest skill test-design/risk-modeling \
  --input "分析 equipment/alarm-config 页面的测试风险" \
  --provider openai \
  --module equipment \
  --page alarm-config
```

**期望**：输出风险模型分析结果，包含 Context 注入痕迹。

#### 测试 2：CLI 执行 Agent

```bash
# 执行 test-design-agent（3 个 Skill 编排）
aitest agent run --agent test-design-agent \
  --module equipment --page alarm-config \
  --provider claude
```

**期望**：依次执行 page-analysis → risk-modeling → testcase-design，输出 3 个 Skill 的 Token 用量。

#### 测试 3：MCP Tool 触发

在任意 MCP 客户端中：
1. 列出 Tools，确认 `run_test_design_agent` 存在
2. 调用 `run_full_sop(module="equipment", mode="status")`
3. 调用 `run_test_design_agent(module="equipment", page="alarm-config")`

**期望**：返回正确的状态 JSON 或触发指令。

#### 测试 4：FastAPI 端点

```bash
# 启动服务
python -m aitest.server.main &

# 查询模块状态
curl http://localhost:8000/api/agent/status/equipment | python -m json.tool

# 触发 Agent 执行
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"agent": "test-design-agent", "module": "equipment", "page": "alarm-config", "provider": "claude"}' \
  | python -m json.tool

# 访问 Swagger UI
# 浏览器打开 http://localhost:8000/docs
```

**期望**：所有端点返回正确的 JSON。

### 回归检查

验证改动未破坏现有功能：

```bash
# 现有 MCP Server 仍可启动
python -m aitest.mcp_server &
# Ctrl+C 退出

# 现有 CLI 子命令仍可用
aitest check --help
aitest rag status
aitest bus listen
aitest agent next --module=tank
aitest workflow status
```

---

## 文件改动汇总

| 文件 | Phase | 操作 | 预计行数 |
|------|:---:|:---:|:---:|
| `aitest/mcp_server.py` | 1 | 编辑：新增 3 个 Tool 定义 + case 分支 | +80 行 |
| `.claude/mcp.json` | 1 | 编辑：更新 description | 1 行 |
| `aitest/llm/__init__.py` | 2 | **新建** | 8 行 |
| `aitest/llm/provider.py` | 2 | **新建** | ~180 行 |
| `ZJSN_Test-master526/.env.example` | 2 | 编辑：新增 LLM 配置 | +5 行 |
| `aitest/llm/skill_loader.py` | 3 | **新建** | ~80 行 |
| `aitest/llm/prompt_adapter.py` | 3 | **新建** | ~120 行 |
| `aitest/llm/context_injector.py` | 3 | **新建** | ~100 行 |
| `aitest/agent_runner.py` | 3 | **新建** | ~200 行 |
| `aitest/cli.py` | 3 | 编辑：新增 `skill` 子命令 | +50 行 |
| `aitest/server/__init__.py` | 4 | **新建** | 1 行 |
| `aitest/server/main.py` | 4 | **新建** | ~40 行 |
| `aitest/server/api/__init__.py` | 4 | **新建** | 1 行 |
| `aitest/server/api/agents.py` | 4 | **新建** | ~80 行 |
| `aitest/server/api/webhooks.py` | 4 | **新建** | ~40 行 |
| `aitest/server/core/__init__.py` | 4 | **新建** | 1 行 |
| `aitest/server/core/context_cache.py` | 4 | **新建** | ~100 行 |
| `requirements.txt` | 2 | 编辑：新增依赖 | +5 行 |

**总计**：4 个文件编辑 + 13 个文件新建，~1100 行 Python。

---

## 执行顺序

```
Phase 1 (MCP Tools)     ← 最独立，1-2h，改 1 个文件
    ↓
Phase 2 (Provider 抽象)  ← 无依赖，3-4h，新建 2 个文件
    ↓
Phase 3 (Skill Runner)   ← 依赖 Phase 2，2-3h，新建 4 个文件 + 编辑 cli.py
    ↓
Phase 4 (FastAPI 骨架)   ← 依赖 Phase 2-3 更佳，2-3h，新建 6 个文件
    ↓
Phase 5 (整合测试)       ← 依赖 Phase 1-4，1h，验证
```

如果时间有限，**至少完成 Phase 1+2**——这已经实现了 MCP 协议标准化和 LLM Provider 无关性两个核心目标。Phase 3-4 可在后续会话中继续。

---

## 注意事项

1. **API Key 安全**：`.env` 中的 API Key 不要提交到 Git。`.env.example` 仅放空值模板。
2. **litellm 可选**：如果不想引入 litellm 依赖，Phase 2 可直接使用各 Provider 的原生 SDK（`anthropic` + `openai`），手动处理差异。代码量增加 ~50 行但减少一个依赖。
3. **Ollama 前提**：使用 Ollama Provider 需要本地运行 Ollama 服务且已拉取模型（如 `ollama pull qwen3`）。在 Windows 上 Ollama 默认地址为 `http://localhost:11434`。
4. **向后兼容**：所有新建文件不修改现有 Skill Markdown 和 Context 文件。Agent Runner 是纯新增能力，不影响 Claude Code 中已有的 Skill/Agent 调用方式。
5. **Provider 选择建议**：
   - `claude` (Claude Sonnet 4.6)：复杂 Skill（tech-analysis, bug-analysis, page-object-generator）
   - `openai` (GPT-4o)：代码生成类 Skill 表现可能更优
   - `ollama` (Qwen3 8B+)：简单 Skill（code-consistency-checker 本就不需要 LLM；allure-report-analyzer 可用本地模型）
6. **FastAPI 服务不要在生产环境用 `--reload`**：Phase 4 是 MVP 骨架，`uvicorn` 的 reload 模式仅用于开发。

---

> **给接手 AI 的提示**：严格按 Phase 1→2→3→4→5 顺序执行。每个 Phase 完成后运行对应的验收测试。Phase 2 的 Provider 实现是最关键的——如果只做一件事，做 Phase 2。
