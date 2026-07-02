# Alice Engine

AI 测试自动化 SDK — 从 `pip install alice-engine` 开始。

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

## 异步用法

```python
import asyncio
from alice_engine import Engine, Project

async def main():
    project = Project("./my-project")
    engine = Engine(project=project, llm_provider="mock")
    result = await engine.run_async("equipment", pages=["alarm-config"])
    print(result.status)

asyncio.run(main())
```

## 五层架构

```
Runtime    — Engine 主动依赖 (Retry, Checkpoint, Security, Knowledge, Memory)
Workflow   — Engine 组织流程 (SOPGraph, Planner, AgentLoop)
Adapter    — Engine 通过接口调用 (LLMProvider, ToolProvider)
Extension  — 被动监听 (Audit, Complexity)
Platform   — 业务特有 (Web, Auth, Report)
```

## 核心概念

### Project — 项目配置

```python
from alice_engine import Project

project = Project("./my-project")
print(project.name)      # "my-project"
print(project.modules)   # ["equipment", "tank", "personnel"]
print(project.config.url) # "https://example.com"
```

### Engine — 执行引擎

```python
from alice_engine import Engine

engine = Engine(project=project, llm_provider="mock")
result = engine.run("equipment", pages=["alarm-config"])
```

### RunResult — 执行结果

```python
result = engine.run("equipment")

result.status           # "completed" | "completed_with_issues" | "failed"
result.success          # True | False
result.run_id           # "engine-abc123"
result.elapsed_seconds  # 45.2
result.completed_phases # ["observe", "plan", ...]
result.failed_phases    # []
result.pages            # ["alarm-config"]
result.agent_outputs    # {...}
```

## Runtime Capabilities

### KnowledgeStore — 知识检索

```python
from alice_engine.runtime import InMemoryKnowledgeStore

knowledge = InMemoryKnowledgeStore()
engine = Engine(project=project, knowledge=knowledge)
```

### MemoryStore — 执行记忆

```python
from alice_engine.runtime import InMemoryMemoryStore

memory = InMemoryMemoryStore()
engine = Engine(project=project, memory=memory)

# 查看历史
history = memory.get_history("equipment")
last = memory.get_last("equipment")
```

### ReliableProvider — 可靠调用

```python
from alice_engine.runtime.retry import ReliableProvider
from alice_engine.providers import get_provider

provider = get_provider("claude")
reliable = ReliableProvider(primary=provider, max_retries=3)
```

## LLM Providers

```python
from alice_engine.providers import get_provider, list_providers

# 可用 Provider
print(list_providers())  # ['mock', 'claude', 'openai', 'deepseek', 'ollama']

# 获取 Provider
mock = get_provider("mock")
claude = get_provider("claude", api_key="sk-...")
openai = get_provider("openai", model="gpt-4o-mini")
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
