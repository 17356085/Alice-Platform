# 从 aitest 迁移

## 主要变化

| aitest | alice-engine |
|--------|-------------|
| `from aitest.engine import Engine` | `from alice_engine import Engine` |
| `Engine(workstudy=...)` | `Engine(project=...)` |
| `engine.run()` 返回 dict | `engine.run()` 返回 RunResult |
| 需要 `fastapi`, `sqlalchemy` 等 | 最小依赖 |
| 仅同步 | 同步 + 异步 |

## 迁移步骤

### 1. 替换导入

```python
# Before
from aitest.engine import Engine

# After
from alice_engine import Engine
```

### 2. 更新构造函数

```python
# Before
engine = Engine(workstudy="/path/to/project")

# After
from alice_engine import Project
project = Project("/path/to/project")
engine = Engine(project=project)
```

### 3. 处理返回值

```python
# Before
result = engine.run("equipment")
status = result["status"]  # dict

# After
result = engine.run("equipment")
status = result.status  # RunResult dataclass
success = result.success  # 便捷属性
```

### 4. 异步支持 (可选)

```python
# 新增
result = await engine.run_async("equipment")
```

## 向后兼容

aitest 中的以下模块已改为 re-export，旧 import 路径仍然可用:

```python
# 这些仍然工作
from aitest.engine.task import Observation
from aitest.engine.state_machine import TaskState
from aitest.graphs.state import SOPState
from aitest.runtime.retry import ReliableProvider
```
