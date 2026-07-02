# Extensions

## 编写自定义扩展

实现 `EngineExtension` 协议即可:

```python
from alice_engine import Engine, RunResult

class MyExtension:
    def on_init(self, engine):
        """Engine 初始化后调用。"""
        self.engine = engine
        print(f"Project: {engine.config.project_path}")

    def on_phase_end(self, module, phase, result):
        """每个 Phase 完成后调用。"""
        print(f"Phase {phase}: {result}")

    def on_cycle_end(self, module, result: RunResult):
        """整个 SOP 完成后调用。"""
        print(f"Done: {result.status} in {result.elapsed_seconds}s")

engine = Engine(project_path="./my-project")
engine.add_extension(MyExtension())
```

## 内置扩展

### AuditExtension

审计扩展，记录执行日志。

### ComplexityExtension

复杂度评估扩展。

### KnowledgeExtension

知识提取扩展。

### MemoryExtension

测试记忆扩展。

## 扩展最佳实践

1. **保持轻量** — 扩展不应阻塞主流程
2. **异常安全** — 捕获异常，不要让扩展崩溃引擎
3. **可选依赖** — 扩展的依赖应该是可选的
