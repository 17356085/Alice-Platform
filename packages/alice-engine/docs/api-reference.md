# API Reference

## 核心类

### Engine

```python
class Engine(
    project: Project,
    project_path: str | Path,
    llm_provider: str = "anthropic",
    event_bus: EventBus = None,
    knowledge: KnowledgeStore = None,
    memory: MemoryStore = None,
    extensions: list[EngineExtension] = None,
)
```

**属性:**
- `project -> Project` — 当前项目
- `extensions -> list[EngineExtension]` — 已注册扩展

**方法:**
- `run(module, pages, mode, run_id) -> RunResult` — 同步执行
- `run_async(module, pages, mode, run_id) -> RunResult` — 异步执行
- `validate() -> ValidationResult` — 验证配置
- `list_modules() -> list[str]` — 列出模块
- `add_extension(ext) -> None` — 注册扩展

---

### Project

```python
class Project(path: str | Path)
```

**属性:**
- `path -> Path` — 项目路径
- `name -> str` — 项目名称
- `config -> ProjectConfig` — 项目配置
- `modules -> list[str]` — 可用模块
- `governance_path -> Path` — 治理目录
- `has_governance -> bool` — 是否有治理目录

**方法:**
- `module_path(module) -> Path` — 模块目录
- `has_module(module) -> bool` — 检查模块
- `validate() -> ValidationResult` — 验证配置
- `exists(path) -> bool` — 检查项目是否存在 (类方法)

---

### RunResult

```python
@dataclass
class RunResult:
    status: str = "failed"           # "completed" | "completed_with_issues" | "failed"
    run_id: str = ""
    module: str = ""
    pages: list[str] = []
    mode: str = "full"
    elapsed_seconds: float = 0.0
    completed_phases: list[str] = []
    failed_phases: list[str] = []
    agent_outputs: dict = {}
    error: str | None = None

    @property
    def success(self) -> bool
```

---

### ValidationResult

```python
@dataclass
class ValidationResult:
    valid: bool = True
    errors: list[str] = []
    warnings: list[str] = []
    project: Project | None = None

    def add_error(msg: str)
    def add_warning(msg: str)
```

---

## Runtime Capabilities

### KnowledgeStore

```python
class KnowledgeStore(ABC):
    def search(module, page, limit=5) -> list[KnowledgeItem]
    def ingest(module, result) -> None
```

**内置实现:**
- `InMemoryKnowledgeStore` — 内存存储

---

### MemoryStore

```python
class MemoryStore(ABC):
    def remember(module, result) -> None
    def get_last(module) -> MemoryRecord | None
    def get_history(module, limit=10) -> list[MemoryRecord]
```

**内置实现:**
- `InMemoryMemoryStore` — 内存存储
- `FileMemoryStore` — 文件存储

---

### ReliableProvider

```python
class ReliableProvider(LLMProvider):
    def __init__(
        primary: LLMProvider,
        fallback_chain: list[LLMProvider] = None,
        max_retries: int = 3,
        timeout: float = 120.0,
    )
```

---

### CheckpointManager

```python
class CheckpointManager:
    def __init__(governance_path: str | Path)
    def get_checkpointer() -> SqliteSaver
    def cleanup(max_age_days, max_runs) -> dict
    def list_runs() -> list[str]
```

---

### ContextWindowMonitor

```python
class ContextWindowMonitor:
    def __init__(model: str)
    def check() -> WindowStatus
    def add_usage(input_tokens, output_tokens)
    def should_continue() -> bool
    def status_summary() -> str
```

---

### CircuitBreaker

```python
class CircuitBreaker:
    def __init__(name, failure_threshold=5, cooldown_seconds=60)
    def call(fn, *args, **kwargs)
    def state -> CircuitState
```

---

## Audit

### check_output_safety

```python
def check_output_safety(content: str, skill_id: str = "") -> list[SafetyFlag]
```

### attribute_failure

```python
def attribute_failure(observation, response_content: str = "") -> FailureCategory
```

### OnlineMonitor

```python
class OnlineMonitor:
    def __init__(data_dir: str | Path = None)
    def record_run(module: str, metrics: RunMetrics)
    def analyze(module: str, days: int = 7) -> dict
```

### CostAuditor

```python
class CostAuditor:
    def __init__(data_dir: str | Path = None)
    def record_cost(agent_name, tokens_in, tokens_out, model)
    def total_cost() -> float
```

---

## Providers

### get_provider

```python
def get_provider(name: str = "mock", **kwargs) -> LLMProvider
```

**可用 Provider:**
- `mock` — MockProvider (测试用)
- `claude` — Anthropic Claude
- `openai` — OpenAI GPT
- `deepseek` — DeepSeek
- `ollama` — Ollama 本地模型

### register_provider

```python
def register_provider(name: str, provider_cls: type[LLMProvider])
```

---

## 异常

- `AliceError` — 基础异常
- `ConfigError` — 配置错误
- `ProjectNotFoundError` — 项目不存在
- `ModuleNotFoundError` — 模块不存在
- `ExecutionError` — 执行失败
- `LLMProviderError` — Provider 错误
- `ExtensionError` — 扩展错误
