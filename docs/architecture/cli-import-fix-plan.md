# CLI 内部导入修复方案

**问题**: 3 处 CLI 代码从 `aitest.engine` 导入，绕过 SDK 公共 API

---

## 问题分析

### 问题 1 & 2: Extensions 导入

**位置**:
- `aitest/cli/adapters/engine_adapter.py:48-51`
- `aitest/cli/commands/run.py:80-83`

**当前代码**:
```python
from aitest.engine.extensions import (
    AuditExtension, ComplexityExtension,
    KnowledgeExtension, MemoryExtension,
)
```

**问题**: 
- SDK 仅导出 `AuditExtension` 和 `ComplexityExtension`
- `KnowledgeExtension` 和 `MemoryExtension` 仍在平台层 `aitest/engine/extensions/`

**原因**: 这两个扩展是平台特定的，还未迁移到 SDK

---

### 问题 3: EventBus 导入

**位置**: `aitest/cli/commands/run.py:35`

**当前代码**:
```python
from aitest.engine.event_bus import get_event_bus
```

**问题**: 绕过 SDK 公共 API

**SDK 导出**: `alice_engine` 导出 `EventBus` 类，但未导出 `get_event_bus()` 工厂函数

---

## 修复方案

### 方案 A: 混合导入（推荐 - 快速修复）

保持当前功能，部分使用 SDK，部分保留平台导入：

```python
# SDK 导出的扩展
from alice_engine import AuditExtension, ComplexityExtension

# 平台特定扩展（暂时保留）
from aitest.engine.extensions import KnowledgeExtension, MemoryExtension

# EventBus - 创建实例而非使用全局单例
from alice_engine import EventBus
bus = EventBus()
```

**优点**:
- 快速修复（1 小时）
- 不破坏现有功能
- SDK 部分已迁移

**缺点**:
- 仍有平台依赖（Knowledge/Memory 扩展）
- 未完全使用 SDK

---

### 方案 B: 完全迁移到 SDK（理想 - 需要更多工作）

1. **迁移 KnowledgeExtension 和 MemoryExtension 到 SDK**
   - 移动到 `packages/alice-engine/alice_engine/extensions/`
   - 添加到 SDK 公共 API 导出
   - 工作量：1-2 天

2. **添加 get_event_bus() 到 SDK**
   - 或使用 `EventBus()` 实例化
   - 工作量：半天

3. **CLI 完全使用 SDK API**
   ```python
   from alice_engine import (
       AuditExtension, ComplexityExtension,
       KnowledgeExtension, MemoryExtension,
       EventBus
   )
   ```

**优点**:
- CLI 完全独立
- 扩展可被外部 SDK 用户使用

**缺点**:
- 需要更多时间
- 涉及 SDK 变更

---

### 方案 C: 移除平台特定扩展（最激进）

从 CLI 中移除 Knowledge 和 Memory 扩展支持：

```python
# 仅支持 SDK 导出的扩展
from alice_engine import AuditExtension, ComplexityExtension

ext_map = {
    "audit": AuditExtension,
    "complexity": ComplexityExtension,
    # knowledge 和 memory 暂不支持
}
```

**优点**:
- CLI 完全使用 SDK
- 代码最干净

**缺点**:
- 破坏现有功能
- 用户无法通过 CLI 启用 Knowledge/Memory 扩展

---

## 推荐执行路径

### 立即执行（今天）：方案 A - 混合导入

**修改 1: `aitest/cli/adapters/engine_adapter.py`**
```python
# 第 48-51 行改为：
from alice_engine import AuditExtension, ComplexityExtension
from aitest.engine.extensions import KnowledgeExtension, MemoryExtension
```

**修改 2: `aitest/cli/commands/run.py`**
```python
# 第 35 行改为：
from alice_engine import EventBus

# 第 59 行改为：
bus = EventBus()  # 创建实例而非全局单例

# 第 80-83 行改为：
from alice_engine import AuditExtension, ComplexityExtension
from aitest.engine.extensions import KnowledgeExtension, MemoryExtension
```

**测试**:
```bash
aitest run --module equipment --extensions audit,complexity
aitest run --module equipment --extensions knowledge,memory
```

**工作量**: 1 小时

---

### 后续执行（第 2-3 周）：方案 B - 完全迁移

**任务**:
1. 迁移 `aitest/engine/extensions/knowledge.py` → SDK
2. 迁移 `aitest/engine/extensions/memory.py` → SDK
3. 添加到 SDK 公共 API
4. 更新 CLI 导入为纯 SDK

**工作量**: 1-2 天

---

## 审计报告更新

修复后，审计结果将变为：

| 检查项 | 修复前 | 修复后（方案 A） | 修复后（方案 B） |
|--------|--------|------------------|------------------|
| CLI → SDK 公共 API | ⚠️ 3 处内部导入 | ⚠️ 2 处平台导入（Knowledge/Memory） | ✅ 全部 SDK |
| SDK 独立性 | ✅ 通过 | ✅ 通过 | ✅ 通过 |

---

## 执行决策

**我建议**: 先执行**方案 A**（今天完成），然后在第 2-3 周执行**方案 B**。

这样可以：
- ✅ 快速减少内部导入（从 3 处降至 2 处）
- ✅ 不破坏现有功能
- ✅ 为完全迁移铺路

你同意这个方案吗？我可以立即开始修改代码。
