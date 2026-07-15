# Step 3: graphs ↔ infra 循环依赖拆分报告

**执行时间**: 2026-07-14
**状态**: ✅ 已完成（无需拆分）

## 拆分目标

检查并消除 `aitest.graphs` 与 `aitest.infra` 之间的双向循环依赖（如果存在）。

## 循环依赖分析

### 依赖关系检测

使用静态分析扫描 `graphs` 和 `infra` 模块的所有 Python 文件中的导入语句：

```bash
graphs → ['infra']
infra → (无依赖)
```

### 结论

✅ **graphs → infra 是单向依赖，架构合理**

- `graphs` 模块（测试流程编排层）依赖 `infra` 模块（基础设施层）
- `infra` 模块不依赖 `graphs` 模块
- **不存在循环依赖**

## 架构验证

### 分层关系

```
┌─────────────┐
│   graphs    │  ← 测试流程编排层（SOP 图、并行执行）
│  (编排层)   │
└─────┬───────┘
      │ 单向依赖
      ↓
┌─────────────┐
│    infra    │  ← 基础设施层（db, logging, metrics, security）
│ (基础设施层) │
└─────────────┘
   (完全独立)
```

这是正确的分层架构：
- **编排层** (`graphs`) 使用基础设施服务
- **基础设施层** (`infra`) 完全独立，可被多个上层模块共享

### 典型依赖示例

`graphs` 对 `infra` 的合理依赖包括：

1. **数据库**: `from aitest.infra.db import get_session`
2. **日志**: `from aitest.infra.logging import get_logger`
3. **指标**: `from aitest.infra.metrics import record_metric`
4. **安全**: `from aitest.infra.security import sanitize_command`
5. **SQL**: `from aitest.infra.sql import execute_query`

这些都是基础设施服务，上层模块依赖它们是正常且必要的。

## 执行的更改

**无需更改** - 依赖关系已经符合架构最佳实践。

## 拆分效果

### 拆分前的依赖关系

```
graphs → infra (单向)
infra → (无依赖)
```

### 拆分后的依赖关系

```
graphs → infra (单向，保持不变)
infra → (无依赖)
```

### 关键结论

✅ **架构分层明确**: `graphs` 作为编排层依赖基础设施层，`infra` 完全独立  
✅ **无循环依赖**: 不存在反向依赖  
✅ **无需重构**: 当前设计已经符合最佳实践

## 对 SCC 的影响

- **拆分前**: `graphs → infra` 单向依赖（不在同一个 SCC 中）
- **拆分后**: 保持单向依赖（无变化）
- **预期效果**: 无影响 - 这两个模块本就不在循环依赖中

## 设计原则验证

✅ **依赖倒置**: 上层 `graphs` 依赖下层 `infra`，而非反向  
✅ **单一职责**: `infra` 专注基础设施，`graphs` 专注流程编排  
✅ **开闭原则**: `graphs` 通过 `infra` 提供的稳定接口使用基础服务  
✅ **接口隔离**: `infra` 提供清晰的功能模块（db, logging, metrics, security）

## 总结

Step 3 完成了 `graphs ↔ infra` 循环依赖的检查：

### ✅ 验证结果

- **无循环依赖**: `graphs → infra` 单向依赖，架构合理
- **无需重构**: 当前依赖关系已经符合最佳实践
- **分层明确**: 编排层依赖基础设施层，符合软件工程原则

### 📊 对 SCC 的影响

- **检查前**: 预期可能存在循环依赖
- **检查后**: 确认不存在循环依赖
- **实际效果**: 无需拆分，这两个模块本就独立

### 🔑 架构洞察

1. **正确的分层** - `graphs` 作为编排层自然依赖 `infra` 提供的基础服务
2. **清晰的边界** - `infra` 不知道 `graphs` 的存在，保持了基础设施层的独立性
3. **可复用性** - `infra` 可以被 `platform`、`mcp`、`graphs` 等多个模块共享

### 📋 下一步

**Step 4**: 拆分 `platform ↔ discovery` 循环依赖（如果存在）

继续按照 6 步计划逐步检查剩余循环依赖：
- ~~Step 1: platform ↔ mcp~~ ✅
- ~~Step 2: platform ↔ infra~~ ✅
- ~~Step 3: graphs ↔ infra~~ ✅（无需拆分）
- Step 4: platform ↔ discovery
- Step 5: platform ↔ knowledge/testing/audit_engine
- Step 6: llm ↔ adapters
