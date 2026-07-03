# Architecture Freeze v1.1

> 日期: 2026-07-03
> 基于: Architecture Cleanup Sprint 完成
> 前置: Architecture Freeze v1.0 (2026-06-23)

---

## Frozen（不可修改）

以下模块的公共接口（`__all__` 导出）已冻结。修改需要 RFC + 评审。

### Run 系统

| 模块 | 冻结接口 | 文件 |
|------|---------|------|
| **Run** | dataclass 字段、to_dict() | `platform/run.py` |
| **RunEvent** | dataclass 字段、to_dict()、EventType 常量 | `platform/run_event.py` |
| **ExecutionRequest** | dataclass 字段、生命周期方法 | `platform/execution_request.py` |
| **EventDataKey** | 所有 key 常量 | `platform/run_event.py` |

### 编排层

| 模块 | 冻结接口 | 文件 |
|------|---------|------|
| **ExecutionService** | execute(), resume(), cancel() | `platform/execution_service.py` |
| **ExecutionResult** | dataclass 字段 | `platform/execution_service.py` |

### 事件系统

| 模块 | 冻结接口 | 文件 |
|------|---------|------|
| **EventBus** | subscribe(), publish(), publish_async(), priority 常量 | `platform/event_bus.py` |
| **RunEventConsumer** | Protocol: start(), stop(), is_active | `platform/consumer.py` |

### 存储层

| 模块 | 冻结接口 | 文件 |
|------|---------|------|
| **RunStore** | save_run(), load_run(), save_event(), list_events() | `platform/run_store.py` |
| **AuditLogger** | query(), count(), stats() | `platform/audit_log.py` |

### 引擎

| 模块 | 冻结接口 | 文件 |
|------|---------|------|
| **ExecutionEngine** | Protocol: run(), run_interactive(), cancel() | `platform/engine_factory.py` |
| **AgentEvent** | dataclass 字段、AgentEventProtocol | `alice_engine/core/task.py` |

---

## Still Evolving（可修改）

以下模块仍在演进，接口可能变化。

| 模块 | 说明 | 文件 |
|------|------|------|
| **Artifacts** | 产物管理 | `platform/artifacts.py` |
| **Knowledge** | 知识库 | `platform/knowledge.py` |
| **Policy** | 治理策略 | `governance/` |
| **Plugin** | 插件系统 | `platform/plugin.py` |
| **UI** | 前端组件 | `aitest/web/` |
| **Replay** | 执行回放 | `platform/replay.py` |
| **Complexity** | 复杂度分类 | `platform/complexity/` |
| **ObservationBus** | Agent 观测事件 | `platform/observation_bus.py` |
| **TestingMemory** | 测试记忆 | `platform/testing_memory.py` |

---

## Import 方向规则

```
server/api  →  platform  →  infra  →  runtime
                ↓
            alice-engine
```

**禁止**：
- `infra` → `platform` ❌
- `platform` → `server` ❌
- `alice-engine` → `aitest` ❌

**验证**：
```bash
# 无反向依赖
grep -r "from aitest.platform" aitest/infra/ --include="*.py"
grep -r "from aitest.server" aitest/platform/ --include="*.py"
grep -r "from aitest\." packages/alice-engine/ --include="*.py"
```

---

## DI 规则

1. **新增模块必须用 DI** — 构造函数接受依赖参数
2. **Singleton 作为 fallback** — `get_xxx()` 仅用于向后兼容
3. **API 层通过 app.state 获取共享实例** — 不直接调用 `get_xxx()`

---

## Event Contract 规则

1. **新增 event type 必须在 EventType 中定义**
2. **新增 event data key 必须在 EventDataKey 中定义**
3. **Consumer 必须用 EventDataKey 常量访问 event.data**
4. **新增 Consumer 必须实现 RunEventConsumer Protocol**

---

## 修改流程

1. 检查是否涉及 Frozen 模块
2. 如果是 → 写 RFC，说明为什么必须改
3. 如果不是 → 直接改，但遵守 Import/DI/Event 规则
4. 所有改动必须通过 `pytest tests/`
