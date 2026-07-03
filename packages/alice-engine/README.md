# Alice Engine

AI 测试自动化 Runtime SDK — 从 `pip install alice-engine` 开始。

## 安装

```bash
# 核心 (最小依赖)
pip install alice-engine

# 带 LLM Provider
pip install alice-engine[llm-anthropic]
pip install alice-engine[llm-openai]

# 全部
pip install alice-engine[all]
```

## 快速开始

```python
from alice_engine import Engine, Project
from alice_engine.runtime import InMemoryKnowledgeStore, InMemoryMemoryStore

# 1. 创建 Project
project = Project("./my-project")

# 2. 创建 Engine
engine = Engine(
    project=project,
    llm_provider="mock",  # 或 "claude", "openai"
    knowledge=InMemoryKnowledgeStore(),
    memory=InMemoryMemoryStore(),
)

# 3. 执行测试
result = engine.run("equipment", pages=["alarm-config"])

print(result.status)           # "completed"
print(result.success)           # True
print(result.elapsed_seconds)   # 45.2
print(result.completed_phases)  # ["observe", "plan", ...]
```

## 核心模块

### AgentLoop — 执行引擎

```python
from alice_engine.core.executor import AgentLoop

agent = AgentLoop("automation-agent", module="equipment", page="alarm-config")
state = agent.run()

print(state.success)            # True
print(state.completed_skills)   # ["page-analyze", "test-generate", ...]
```

### SOPGraph — 工作流编排

```python
from alice_engine.workflow.sop_graph import build_sop_graph, build_compiled_graph

graph = build_sop_graph()
compiled = graph.compile(checkpointer=checkpointer)
result = compiled.invoke(initial_state, {"configurable": {"thread_id": "my-run"}})
```

SOP 图模块拆分:

```text
sop_graph.py       图构建 (build_sop_graph, build_compiled_graph)
sop_nodes.py       节点函数 (entry, preflight, exit, page_advance)
sop_hitl.py        HITL 审批 + 质量门禁
sop_routing.py     路由逻辑 + 常量
sop_preflight.py   Preflight 缓存
```

### LLM Providers

```python
from alice_engine.providers import get_provider, list_providers

print(list_providers())  # ['mock', 'claude', 'openai', 'deepseek', 'ollama']

mock = get_provider("mock")
claude = get_provider("claude", api_key="sk-...")
openai = get_provider("openai", model="gpt-4o-mini")
```

### ReliableProvider — 可靠调用

```python
from alice_engine.runtime.retry import ReliableProvider
from alice_engine.providers import get_provider

provider = get_provider("claude")
reliable = ReliableProvider(primary=provider, max_retries=3)
```

## 五层架构

```text
Runtime    — Engine 主动依赖 (Retry, Checkpoint, Security, Knowledge, Memory)
Workflow   — Engine 组织流程 (SOPGraph, Planner, AgentLoop)
Adapter    — Engine 通过接口调用 (LLMProvider, ToolProvider)
Extension  — 被动监听 (Audit, Complexity)
Platform   — 业务特有 (Web, Auth, Report)
```

## 目录结构

```text
alice_engine/
├── core/
│   ├── executor.py          AgentLoop 执行引擎
│   ├── planner.py           任务规划
│   ├── task.py              任务状态定义
│   └── skill_loader.py      Skill 加载器
├── workflow/
│   ├── sop_graph.py         SOP 图构建
│   ├── sop_nodes.py         节点函数
│   ├── sop_hitl.py          HITL 审批
│   ├── sop_routing.py       路由逻辑
│   ├── sop_preflight.py     Preflight 缓存
│   ├── state.py             状态定义
│   └── nodes.py             节点工厂
├── providers/
│   ├── claude.py            Claude Provider
│   ├── openai.py            OpenAI Provider
│   ├── deepseek.py          DeepSeek Provider
│   └── mock.py              Mock Provider (测试用)
├── runtime/
│   ├── retry.py             重试 + 降级
│   ├── context_window.py    上下文窗口监控
│   ├── checkpoint.py        LangGraph 检查点
│   └── security.py          安全层
└── events.py                事件总线
```

## Extensions

```python
from alice_engine import Engine, EngineExtension, RunResult

class NotifyExtension:
    def on_init(self, engine):
        print(f"Engine started: {engine.project.name}")

    def on_phase_end(self, module, phase, result):
        print(f"Phase {phase} completed")

    def on_cycle_end(self, module, result: RunResult):
        print(f"Done: {result.status}")

engine = Engine(project=project, extensions=[NotifyExtension()])
```

## EventBus

```python
from alice_engine import Engine, EventBus

bus = EventBus()
bus.subscribe("run_start", lambda d: print(f"开始: {d}"))
bus.subscribe("complete", lambda d: print(f"完成: {d['status']}"))

engine = Engine(project=project, event_bus=bus)
```

## 自定义 Provider

```python
from alice_engine import Engine, LLMProvider, LLMResponse, register_provider

class MyProvider(LLMProvider):
    def supports_tools(self):
        return True

    def complete(self, system_prompt, user_prompt, **kwargs):
        return LLMResponse(content="My response")

register_provider("my-provider", MyProvider)
engine = Engine(project=project, llm_provider="my-provider")
```

## 项目配置

项目需要 `project.yaml` (位于项目根目录或 `.tlo/` 目录):

```yaml
name: my-project
url: https://example.com
tech_stack:
  framework: vue3
  ui: element-plus
test_framework: pytest
accounts:
  - username: admin
    password: xxx
modules:
  - equipment
  - tank
  - personnel
```

## 异常处理

```python
from alice_engine import Engine, Project, ProjectNotFoundError, ExecutionError

try:
    project = Project("./nonexistent")
except ProjectNotFoundError:
    print("项目不存在")

try:
    engine = Engine(project=project)
    result = engine.run("equipment")
except ExecutionError as e:
    print(f"执行失败: {e}")
```

## License

MIT
