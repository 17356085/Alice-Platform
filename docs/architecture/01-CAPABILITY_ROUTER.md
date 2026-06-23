# Capability Router — 统一能力路由层

> 参考: Aperant `config/agent-configs.ts` (声明式 Agent 配置) + `tools/registry.ts` (工具注册表)
> 适配: AITest 测试领域 (Browser/RAG/Codegen/Execute/Report/Validate)
> 状态: v1.0-draft | 优先级: P0

## 1. 问题

### 1.1 当前状态

AITest 有两个"工具系统"，但都不可用：

```python
# 问题 1: MCP 工具定义了，但从未传给 LLM
# aitest/agents/skill_executor.py → run_skill() 调用 provider.complete()
# 查看 llm/provider.py:189-193，tools 参数构建了但 run_skill() 传 tools=None
response = llm.complete(system_prompt, user_prompt)  # tools 从未传递

# 问题 2: "技能" 只是 Markdown 提示模板
# governance/skills/automation/page-object-generator.md
# LLM 只能生成文本，不能调用函数
```

结果：Agent 的"行动"就是生成一段文本然后保存到文件。Agent 不能：
- 调用浏览器导航到页面
- 搜索 RAG 知识库
- 运行 pytest
- 获取页面截图

### 1.2 为什么不能直接用 Aperant 的 Tool Calling

Aperant 的工具（Read/Write/Edit/Bash/Glob/Grep）是为代码操作设计的：

```
Aperant: LLM → function_call("Write", {path, content}) → 写入代码文件
```

AITest 需要的是测试能力抽象：

```
AITest: Agent → capability("browser.navigate", {url}) → BrowserUse/Playwright
              → capability("rag.search", {query})      → ChromaDB
              → capability("codegen.script", {spec})    → 生成测试脚本
              → capability("execute.pytest", {module})  → 运行测试
```

## 2. 设计

### 2.1 核心概念

```
Capability (能力)  — Agent 可见的抽象接口 (e.g., "browser", "rag_search")
    │
    ▼
CapabilityProvider (能力提供者) — 具体实现 (e.g., BrowserUseProvider, PlaywrightProvider)
    │
    ▼
Tool Definition (工具定义) — 传给 LLM 的 JSON Schema function calling 格式
```

**关键区别**：一个 Capability 可以有多个 Provider。Capability 是"做什么"，Provider 是"怎么做"。

### 2.2 架构图

```
Agent Loop (agent_runner.py)
    │
    │  run_skill() 改为通过 Capability Router 执行
    │
    ▼
┌─────────────────────────────────────────────────┐
│              CapabilityRouter                     │
│                                                   │
│  register(name, provider)                         │
│  resolve(name, context) → CapabilityProvider      │
│  to_tool_defs(agent_type) → list[ToolDef]         │
│  execute(call: ToolCall) → ToolResult             │
│                                                   │
│  _registry: dict[str, list[CapabilityProvider]]   │
│  _capability_by_agent: dict[str, list[str]]       │
└─────────────────────────────────────────────────┘
    │                    │                    │
    ▼                    ▼                    ▼
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ Browser  │    │ RAG Search   │    │ Codegen       │
│ Providers│    │ Providers    │    │ Providers     │
├──────────┤    ├──────────────┤    ├──────────────┤
│BrowserUse│    │ ChromaDB     │    │ ScriptGen     │
│Playwright│    │ ContextFile  │    │ FixtureGen    │
│Selenium  │    │              │    │               │
└──────────┘    └──────────────┘    └──────────────┘
    │                    │                    │
    ▼                    ▼                    ▼
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ Execute  │    │ Report        │    │ Validate      │
│ Providers│    │ Providers     │    │ Providers     │
├──────────┤    ├──────────────┤    ├──────────────┤
│Pytest    │    │ ExcelExport   │    │ Assertion     │
│Shell     │    │ AllureJSON    │    │ Evidence      │
│Python    │    │ Markdown      │    │ Consistency   │
└──────────┘    └──────────────┘    └──────────────┘
```

### 2.3 Capability 目录

```python
CAPABILITY_CATALOG = {
    # ── Browser ──
    "browser.navigate":       "导航到目标页面",
    "browser.screenshot":     "截取页面截图",
    "browser.click":          "点击元素",
    "browser.fill":           "填写表单字段",
    "browser.read_page":      "获取页面 DOM/文本内容",
    "browser.wait_for":       "等待元素出现",

    # ── Page Analysis ──
    "page.analyze":           "分析页面结构 (表格列/搜索字段/按钮)",
    "page.extract_menu":      "提取侧边栏/导航菜单树",
    "page.identify_components":"识别 UI 组件类型 (el-table/el-dialog/...)",
    "page.locate_elements":   "为关键元素生成定位器",

    # ── RAG / Knowledge ──
    "rag.search":             "搜索知识库 (已知问题/UI 模式/定位器历史)",
    "rag.lookup_similar":     "查找相似页面/模块的测试模式",
    "rag.get_business_rules": "获取业务规则约束",

    # ── Codegen ──
    "codegen.page_object":    "生成 Page Object 类",
    "codegen.test_script":    "生成 pytest 测试脚本",
    "codegen.fixture":        "生成 pytest fixture/conftest",

    # ── Execute ──
    "execute.pytest":         "运行 pytest 测试",
    "execute.script":         "运行任意 Python 脚本",
    "execute.shell":          "执行 shell 命令 (受安全校验)",

    # ── Validate ──
    "validate.assertion":     "运行断言检查",
    "validate.evidence":      "对比截图/输出与预期",
    "validate.consistency":   "代码红线/一致性检查",

    # ── Report ──
    "report.excel":           "生成 Excel 测试报告",
    "report.allure":          "生成 Allure HTML 报告",
    "report.summary":         "生成文本摘要报告",
}
```

### 2.4 Agent → Capability 映射 (声明式)

参考 Aperant `AGENT_CONFIGS` 的声明式模式：

```python
# platform/capabilities/agent_capabilities.py

AGENT_CAPABILITIES: dict[str, list[str]] = {
    "project-agent": [
        "rag.search",
        "rag.lookup_similar",
        "page.extract_menu",
    ],
    "requirement-agent": [
        "rag.get_business_rules",
        "page.analyze",
        "page.identify_components",
    ],
    "test-design-agent": [
        "page.analyze",
        "page.locate_elements",
        "rag.search",            # 查找已知定位器失败模式
        "rag.lookup_similar",    # 查找相似页面测试模式
    ],
    "automation-agent": [
        "codegen.page_object",
        "codegen.test_script",
        "codegen.fixture",
        "page.analyze",          # 读取 PAGE_CONTEXT
        "rag.search",            # 查找已知 UI 模式
        "execute.script",        # 验证生成的代码语法
        "validate.consistency",
    ],
    "execution-agent": [
        "execute.pytest",
        "validate.evidence",
        "report.allure",
        "browser.screenshot",    # 失败截图
    ],
    "bug-analysis-agent": [
        "execute.pytest",        # 复现
        "rag.search",            # 查找已知问题
        "browser.navigate",
        "browser.screenshot",
        "validate.assertion",
    ],
    "report-agent": [
        "report.excel",
        "report.allure",
        "report.summary",
        "rag.search",            # 补充背景信息
    ],
    "knowledge-agent": [
        "rag.search",
        "rag.lookup_similar",
        "rag.get_business_rules",
    ],
}
```

### 2.5 核心类设计

```python
# platform/capabilities/router.py

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol
from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════════════════════════
#  Tool Definition (传给 LLM 的 JSON Schema)
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ToolDef:
    """工具定义 — 对应 LLM function calling 的 JSON Schema。"""
    name: str                          # e.g. "browser__navigate"
    description: str                   # Human-readable description
    parameters: dict                   # JSON Schema for parameters
    # 元数据 (Agent 调度用)
    capability: str                    # 所属 Capability (e.g. "browser.navigate")
    side_effect: str = "read"          # "read" | "write" | "execute"
    estimated_duration: str = "1s"     # 预估耗时
    requires_confirmation: bool = False  # 是否需要人工确认


@dataclass
class ToolCall:
    """LLM 发起的单次工具调用。"""
    id: str                            # LLM 返回的 tool_call_id
    name: str                          # 工具名称
    arguments: dict                    # 解析后的参数
    agent_name: str                    # 发起调用的 Agent
    timestamp: float = field(default_factory=lambda: __import__('time').time())


@dataclass
class ToolResult:
    """工具执行结果。"""
    call_id: str
    success: bool
    content: str                       # 文本返回给 LLM
    data: Any = None                   # 结构化数据 (供 Observation Bus 消费)
    error: Optional[str] = None
    duration_ms: float = 0.0
    truncated: bool = False            # 输出是否被截断


# ══════════════════════════════════════════════════════════════════════════
#  CapabilityProvider — 能力提供者基类
# ══════════════════════════════════════════════════════════════════════════

class CapabilityProvider(ABC):
    """能力提供者基类。

    一个 Capability 可以有多个 Provider (e.g., BrowserUse + Playwright 都提供 browser.*)。
    Router 根据上下文 (env, availability, priority) 选择最佳 Provider。
    """

    # 子类必须设置
    capability: str                    # e.g. "browser.navigate"
    provider_name: str                 # e.g. "browseruse"
    priority: int = 100                # 越小越优先 (1=最高)

    @abstractmethod
    def tool_def(self) -> ToolDef:
        """返回传给 LLM 的工具定义 (JSON Schema)。"""
        ...

    @abstractmethod
    def available(self, context: dict) -> bool:
        """检查此 Provider 在当前上下文中是否可用。"""
        ...

    @abstractmethod
    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        """执行工具调用。"""
        ...

    def truncation_limit(self) -> int:
        """输出截断限制 (字符数)，默认 8000。"""
        return 8000


# ══════════════════════════════════════════════════════════════════════════
#  CapabilityRouter
# ══════════════════════════════════════════════════════════════════════════

class CapabilityRouter:
    """统一能力路由层。

    用法:
        router = CapabilityRouter()
        router.register(BrowserUseNavigateProvider())
        router.register(PlaywrightNavigateProvider())

        # 为 Agent 获取工具定义列表
        tools = router.tool_defs_for_agent("automation-agent")

        # 执行 LLM 发来的工具调用
        result = router.execute(tool_call, context={"module": "equipment"})
    """

    def __init__(self):
        self._registry: dict[str, list[CapabilityProvider]] = {}
        self._agent_capabilities: dict[str, list[str]] = {}

    def register(self, provider: CapabilityProvider) -> None:
        """注册一个能力提供者。同一 Capability 可有多个 Provider。"""
        cap = provider.capability
        if cap not in self._registry:
            self._registry[cap] = []
        self._registry[cap].append(provider)
        # 按 priority 排序
        self._registry[cap].sort(key=lambda p: p.priority)

    def resolve(self, capability: str, context: dict) -> CapabilityProvider:
        """根据上下文选择最佳 Provider。

        Raises:
            CapabilityUnavailableError: 无可用 Provider
        """
        providers = self._registry.get(capability, [])
        for provider in providers:
            if provider.available(context):
                return provider
        raise CapabilityUnavailableError(
            f"No available provider for '{capability}'"
        )

    def tool_defs_for_agent(self, agent_name: str) -> list[dict]:
        """获取 Agent 可用的所有工具定义 (JSON Schema 格式，可直接传 LLM)。

        参考 Aperant agent-configs.ts 的 getRequiredMcpServers() 模式。
        """
        capabilities = self._agent_capabilities.get(agent_name, [])
        if not capabilities:
            # 默认：给所有注册的 Capability
            capabilities = list(self._registry.keys())

        tools = []
        for cap in capabilities:
            providers = self._registry.get(cap, [])
            if providers:
                # 取最高优先级的可用 Provider 的工具定义
                tools.append(providers[0].tool_def())

        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        """执行工具调用。

        从 tool name 反查 Capability → 选择 Provider → 执行。
        """
        # 从 tool name 查找 capability
        # tool name 格式: "{capability_namespace}__{action}"
        # e.g. "browser__navigate" → capability "browser.navigate"
        capability = self._tool_name_to_capability(call.name)
        if not capability:
            return ToolResult(
                call_id=call.id, success=False,
                content=f"Unknown tool: {call.name}",
                error=f"No capability registered for tool '{call.name}'"
            )

        try:
            provider = self.resolve(capability, context)
        except CapabilityUnavailableError as e:
            return ToolResult(
                call_id=call.id, success=False,
                content=str(e), error=str(e)
            )

        try:
            result = provider.execute(call, context)
        except Exception as e:
            return ToolResult(
                call_id=call.id, success=False,
                content=f"Tool execution error: {e}",
                error=str(e)
            )

        # 输出截断 (参考 Aperant tools/truncation.ts)
        if len(result.content) > provider.truncation_limit():
            result.content = (
                result.content[:provider.truncation_limit()]
                + f"\n\n[... truncated {len(result.content) - provider.truncation_limit()} chars ...]"
            )
            result.truncated = True

        return result

    def _tool_name_to_capability(self, tool_name: str) -> Optional[str]:
        """工具名 → Capability 名 映射。"""
        for cap, providers in self._registry.items():
            for p in providers:
                if p.tool_def().name == tool_name:
                    return cap
        return None


class CapabilityUnavailableError(Exception):
    """指定 Capability 无可用 Provider。"""
    pass
```

## 3. Provider 实现示例

### 3.1 BrowserUse Navigate Provider

```python
# platform/capabilities/providers/browser_navigate.py

class BrowserUseNavigateProvider(CapabilityProvider):
    capability = "browser.navigate"
    provider_name = "browseruse"
    priority = 100  # 默认首选

    def tool_def(self) -> ToolDef:
        return ToolDef(
            name="browser__navigate",
            description="导航到目标页面 URL。返回页面标题和主要内容摘要。",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "目标页面 URL"},
                    "wait_until": {
                        "type": "string",
                        "enum": ["load", "networkidle", "selector"],
                        "default": "networkidle",
                        "description": "等待条件"
                    },
                },
                "required": ["url"],
            },
            capability=self.capability,
            side_effect="read",
            estimated_duration="5s",
        )

    def available(self, context: dict) -> bool:
        """检查 BrowserUse 是否可用。"""
        try:
            from aitest.discovery.browser_use import BrowserUseDiscovery
            return True
        except ImportError:
            return False

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        import time
        start = time.time()

        try:
            from aitest.bu_adapter import BrowserUseDriver
            driver = BrowserUseDriver()
            result = driver.navigate(
                url=call.arguments["url"],
                wait_until=call.arguments.get("wait_until", "networkidle"),
            )

            return ToolResult(
                call_id=call.id,
                success=True,
                content=f"已导航到: {result['title']}\nURL: {result['url']}\n"
                        f"主要内容: {result.get('summary', 'N/A')[:2000]}",
                data=result,
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ToolResult(
                call_id=call.id,
                success=False,
                content=f"导航失败: {e}",
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )
```

### 3.2 RAG Search Provider

```python
# platform/capabilities/providers/rag_search.py

class ChromaDBSearchProvider(CapabilityProvider):
    capability = "rag.search"
    provider_name = "chromadb"
    priority = 100

    def tool_def(self) -> ToolDef:
        return ToolDef(
            name="rag__search",
            description=(
                "搜索测试知识库。可查找已知问题、UI 模式、定位器历史、"
                "历史失败记录。返回最相关的结果及其相似度分数。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "collection": {
                        "type": "string",
                        "enum": ["known_issues", "ui_patterns", "locator_history",
                                 "business_rules", "historical_failures"],
                        "description": "目标知识集合",
                    },
                    "top_k": {"type": "integer", "default": 5, "maximum": 10},
                },
                "required": ["query"],
            },
            capability=self.capability,
            side_effect="read",
            estimated_duration="0.5s",
        )

    def available(self, context: dict) -> bool:
        from aitest.platform.knowledge import get_knowledge
        return get_knowledge().available()

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        from aitest.platform.knowledge import get_knowledge
        import time
        start = time.time()

        results = get_knowledge().search(
            query=call.arguments["query"],
            collection=call.arguments.get("collection"),
            top_k=call.arguments.get("top_k", 5),
        )

        # 格式化为 LLM 友好的文本
        lines = []
        for i, r in enumerate(results):
            lines.append(
                f"[{i+1}] (score: {r['score']:.2f}, source: {r['metadata'].get('source', 'unknown')})\n"
                f"    {r['content'][:500]}"
            )

        return ToolResult(
            call_id=call.id,
            success=True,
            content="\n\n".join(lines) if lines else "未找到相关结果。",
            data=results,
            duration_ms=(time.time() - start) * 1000,
        )
```

## 4. 与 Agent Loop 的集成

### 4.1 改造 run_skill()

```python
# aitest/agents/skill_executor.py — 改造后

def run_skill(
    skill_id: str,
    agent_name: str,
    provider_name: str = "claude",
    context: dict = None,
    router: CapabilityRouter = None,  # ← 新增
) -> LLMResponse:
    """执行一个 Skill。如有 CapabilityRouter，启用原生 tool calling。"""

    system_prompt = load_skill(skill_id)
    user_prompt = _build_user_prompt(skill_id, context)

    llm = get_provider(provider_name)

    # ★ 关键改造: 传入工具定义
    tools = None
    if router is not None:
        tools = router.tool_defs_for_agent(agent_name)

    response = llm.complete(
        system_prompt,
        user_prompt,
        tools=tools,  # ← 现在真的传入了
    )

    # ★ 处理 tool calls: 如果 LLM 返回了 tool calls，执行它们
    if response.tool_calls and router is not None:
        tool_results = []
        for tc in response.tool_calls:
            call = ToolCall(
                id=tc["id"],
                name=tc["name"],
                arguments=tc["input"],
                agent_name=agent_name,
            )
            result = router.execute(call, context or {})
            tool_results.append(result)

        # 将 tool results 注入为新的 user message，让 LLM 继续
        # (多轮 tool calling 循环)
        ...

    return response
```

### 4.2 初始化

```python
# platform/capabilities/__init__.py

from platform.capabilities.router import CapabilityRouter
from platform.capabilities.providers.browser_navigate import BrowserUseNavigateProvider
from platform.capabilities.providers.browser_screenshot import BrowserUseScreenshotProvider
from platform.capabilities.providers.rag_search import ChromaDBSearchProvider
from platform.capabilities.providers.execute_pytest import PytestProvider
from platform.capabilities.providers.codegen_page_object import PageObjectGenProvider
from platform.capabilities.providers.codegen_test_script import TestScriptGenProvider
from platform.capabilities.agent_capabilities import AGENT_CAPABILITIES

def create_router() -> CapabilityRouter:
    """工厂函数：创建预配置的 CapabilityRouter。"""
    router = CapabilityRouter()

    # 注册所有 Provider
    for provider_cls in [
        BrowserUseNavigateProvider,
        BrowserUseScreenshotProvider,
        ChromaDBSearchProvider,
        PytestProvider,
        PageObjectGenProvider,
        TestScriptGenProvider,
        # ... 更多 Provider
    ]:
        router.register(provider_cls())

    # 设置 Agent → Capability 映射
    router._agent_capabilities = AGENT_CAPABILITIES

    return router
```

## 5. 扩展指南

### 添加新的 Capability

```python
# 1. 在 CAPABILITY_CATALOG 中注册 (router.py)
# 2. 实现 CapabilityProvider
class NewProvider(CapabilityProvider):
    capability = "execute.new_thing"
    provider_name = "my_impl"
    ...

# 3. 在 create_router() 中注册
router.register(NewProvider())

# 4. 在 AGENT_CAPABILITIES 中分配给 Agent
AGENT_CAPABILITIES["automation-agent"].append("execute.new_thing")
```

### 同一 Capability 的多个 Provider 切换

```python
# 环境变量控制
# CAPABILITY_BROWSER=playwright  → 使用 Playwright
# CAPABILITY_BROWSER=browseruse  → 使用 BrowserUse (默认)

class PlaywrightNavigateProvider(CapabilityProvider):
    capability = "browser.navigate"
    provider_name = "playwright"
    priority = 200  # 低于 BrowserUse，作为备选

    def available(self, context: dict) -> bool:
        # 仅当环境变量指定时才使用
        return os.getenv("CAPABILITY_BROWSER") == "playwright"
```

## 6. 参考来源

| 特性 | 参考 |
|------|------|
| 声明式 Agent→Tool 映射 | Aperant `agent-configs.ts`: `AGENT_CONFIGS` registry |
| Tool 注册表模式 | AITest 现有 `mcp/tools/registry.py`: `ToolDef` dataclass |
| Provider 抽象 | Aperant `providers/factory.ts`: multi-provider + availability check |
| Tool 输出截断 | Aperant `tools/truncation.ts`: disk-spillover truncation |
| Capability > Tool 的理念 | ChatGPT 分析："AITest 应该抽象 Capability 而非 Tool" |
| Tool calling 多轮循环 | Aperant `session/runner.ts`: `streamText()` with `stopWhen: stepCountIs(N)` |
