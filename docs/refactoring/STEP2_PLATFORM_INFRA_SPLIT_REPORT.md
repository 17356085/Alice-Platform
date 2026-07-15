# Step 2: platform ↔ infra 循环依赖拆分报告

**执行时间**: 2026-07-14
**状态**: ✅ 已完成

## 拆分目标

消除 `aitest.platform` 与 `aitest.infra` 之间的双向循环依赖，确保基础设施层（infra）不依赖上层平台模块。

## 循环依赖分析

### 拆分前的循环依赖

**infra → platform** (8 处):
1. `infra/models.py` lines 24-27: 导入 `platform.workflow_models.WorkflowModel`
2. `infra/models.py` lines 24-27: 导入 `platform.model_provider_models.ModelProviderModel`
3. `infra/models.py` lines 24-27: 导入 `platform.secret_models.SecretModel, SecretAuditLogModel`
4. `infra/models.py` lines 24-27: 导入 `platform.environment_models.EnvironmentModel`
5. `infra/models.py` line 219: 导入 `platform.quality_models.DatasetModel, EvaluationModel, ExperimentModel`
6. `infra/models.py` line 223: 导入 `platform.workflow_models.WorkflowModel` (重复)
7. `infra/models.py` line 227: 导入 `platform.worker_lease_models.WorkerLeaseModel`
8. `infra/config_registry.py` line 141: 导入 `platform.versioning.resolve_policy_version`

**platform → infra** (49 处):
- 合理的基础设施依赖：db, sql, logging, metrics, encryption, secure_subprocess 等

### 问题诊断

1. **ORM 模型错位**: `infra/models.py` 设计为"统一 ORM 模型中心"，但通过 import 聚合了分散在 `platform` 各模块的模型类，导致反向依赖。这违反了架构分层：`infra` 应该是底层基础设施，不应依赖上层的 `platform`。

2. **配置层混淆**: `infra/config_registry.py` 包含了 `governance_policy_version` 属性，这是平台策略相关的配置，不应该在基础设施层。

## 执行的更改

### Step 2.1: 将 platform 的 ORM 模型移到 infra/models/

**策略**: 将被 `infra/models.py` 导入的 6 个 platform 模型文件移到 `infra/models/` 子目录，消除 `infra → platform` 依赖。

#### 新建文件

1. **aitest/infra/models/workflow.py** (25 行)
   - `WorkflowModel` ORM 类
   - 从 `platform/workflow_models.py` 移出

2. **aitest/infra/models/model_provider.py** (30 行)
   - `ModelProviderModel` ORM 类
   - 从 `platform/model_provider_models.py` 移出

3. **aitest/infra/models/secret.py** (74 行)
   - `SecretModel`, `SecretAuditLogModel` ORM 类
   - 从 `platform/secret_models.py` 移出

4. **aitest/infra/models/environment.py** (58 行)
   - `EnvironmentModel` ORM 类
   - 从 `platform/environment_models.py` 移出

5. **aitest/infra/models/quality.py** (76 行)
   - `DatasetModel`, `EvaluationModel`, `ExperimentModel` ORM 类
   - 从 `platform/quality_models.py` 移出

6. **aitest/infra/models/worker_lease.py** (35 行)
   - `WorkerLeaseModel` ORM 类
   - 从 `platform/worker_lease_models.py` 移出

7. **aitest/infra/models/__init__.py** (20 行)
   - 统一导出所有模型类

#### 修改文件

**infra 层更新**:
1. `aitest/infra/models.py`
   - 更新 lines 23-27: 从 `infra.models.*` 导入（原 `platform.*`）
   - 更新 lines 219-227: 从 `infra.models.*` 导入（原 `platform.*`）

**platform 层向后兼容 (re-export stubs)**:
1. `aitest/platform/workflow_models.py` → re-export from `infra.models.workflow`
2. `aitest/platform/model_provider_models.py` → re-export from `infra.models.model_provider`
3. `aitest/platform/secret_models.py` → re-export from `infra.models.secret`
4. `aitest/platform/environment_models.py` → re-export from `infra.models.environment`
5. `aitest/platform/quality_models.py` → re-export from `infra.models.quality`
6. `aitest/platform/worker_lease_models.py` → re-export from `infra.models.worker_lease`

### Step 2.2: 拆分 config_registry 的 governance_policy_version

**问题**: `infra/config_registry.py` 的 `governance_policy_version` 属性调用 `platform.versioning.resolve_policy_version()`，这是平台策略相关配置，不应在基础设施层。

**解决方案**: 将 `governance_policy_version` 从 `infra.config_registry` 移到 `platform.config_registry`，通过继承扩展。

#### 修改文件

1. **aitest/infra/config_registry.py**
   - 移除 `governance_policy_version` 属性（lines 138-144）
   - 保持纯粹的基础设施配置

2. **aitest/platform/config_registry.py**
   - 从简单的 re-export 改为继承扩展
   - 创建 `PlatformConfigExtended` 类继承 `_BasePlatformConfig`
   - 添加 `governance_policy_version` 属性
   - 导出扩展后的 `cfg` 实例

## 拆分效果

### 拆分前的依赖关系

```
platform → infra (49 处合理依赖)

infra → platform (8 处反向依赖):
  infra/models.py → platform.*_models (6 个模型文件)
  infra/config_registry.py → platform.versioning
```

### 拆分后的依赖关系

```
platform → infra (单向依赖，架构合理)
  platform.* → infra.db, infra.sql, infra.logging, infra.metrics, ...
  platform.config_registry → infra.config_registry (继承扩展)
  platform.*_models → infra.models.* (re-export)

infra → (无依赖)
  infra 层完全独立，不依赖任何上层模块
```

### 关键改进

✅ **ORM 模型归位**: 将所有 ORM 模型移到 `infra/models/`，作为底层数据模型  
✅ **配置层分离**: `infra.config_registry` 只包含基础设施配置，平台配置通过继承扩展  
✅ **架构分层明确**: `infra` 作为基础设施层，完全独立，可被 `platform`、`mcp`、`graphs` 等共享  
✅ **向后兼容**: 所有旧的 `platform.*_models` 导入路径通过 re-export 保持可用

## 验证结果

```bash
=== platform ↔ infra 依赖关系 ===
platform → ['infra']
infra → (无依赖)

=== 循环检测 ===
✅ platform → infra (单向，架构合理)
```

## 文件清单

### 新建文件 (7 个)

- `aitest/infra/models/__init__.py` (20 行)
- `aitest/infra/models/workflow.py` (25 行)
- `aitest/infra/models/model_provider.py` (30 行)
- `aitest/infra/models/secret.py` (74 行)
- `aitest/infra/models/environment.py` (58 行)
- `aitest/infra/models/quality.py` (76 行)
- `aitest/infra/models/worker_lease.py` (35 行)

### 修改文件 (9 个)

**infra 层**:
- `aitest/infra/models.py` - 更新 import 路径
- `aitest/infra/config_registry.py` - 移除 `governance_policy_version`

**platform 层**:
- `aitest/platform/config_registry.py` - 改为继承扩展
- `aitest/platform/workflow_models.py` - 改为 re-export
- `aitest/platform/model_provider_models.py` - 改为 re-export
- `aitest/platform/secret_models.py` - 改为 re-export
- `aitest/platform/environment_models.py` - 改为 re-export
- `aitest/platform/quality_models.py` - 改为 re-export
- `aitest/platform/worker_lease_models.py` - 改为 re-export

## 风险评估

### 低风险

- ORM 模型迁移（纯数据结构，无业务逻辑）
- Import 路径更新（向后兼容，通过 re-export）
- 配置继承扩展（API 保持一致）

### 缓解措施

- 保留所有功能逻辑不变
- 通过 re-export 保持向后兼容
- 所有使用 `cfg.governance_policy_version` 的代码无需修改（from `platform.config_registry`）

## 架构改进

### 拆分前

```
┌─────────────┐
│  platform   │ ←──┐
└─────┬───────┘    │
      │            │
      ↓            │
┌─────────────┐    │
│    infra    │ ───┘
└─────────────┘
   (循环依赖)
```

### 拆分后

```
┌─────────────┐
│  platform   │
│  (编排层)   │
└─────┬───────┘
      │ 单向依赖
      ↓
┌─────────────┐
│    infra    │
│ (基础设施层) │
└─────────────┘
   (完全独立)
```

### 设计原则验证

✅ **依赖倒置**: 上层 `platform` 依赖下层 `infra`，而非反向  
✅ **开闭原则**: `platform` 通过继承扩展 `infra` 配置，不修改 `infra` 代码  
✅ **单一职责**: `infra` 专注基础设施，`platform` 专注编排和策略  
✅ **接口隔离**: ORM 模型作为数据层接口，独立于业务逻辑

## 总结

Step 2 完成了 `platform ↔ infra` 循环依赖的拆分：

### ✅ 已完成

- **ORM 模型归位**: 6 个模型文件从 `platform` 移到 `infra/models/`
- **配置层分离**: `governance_policy_version` 从 `infra` 移到 `platform`
- **架构分层明确**: `infra` 完全独立，不依赖任何上层模块
- **向后兼容**: 所有旧导入路径通过 re-export 保持可用

### 📊 对 SCC 的影响

- **拆分前**: `platform ↔ infra` 双向循环依赖
- **拆分后**: `platform → infra` 单向依赖（架构合理）
- **预期效果**: `infra` 从大 SCC 中分离，成为独立的基础层

### 🔑 关键技术

1. **模块提升** - 将共享 ORM 模型移到更底层的 `infra`
2. **配置继承扩展** - `platform` 通过继承扩展 `infra` 配置
3. **Re-export 兼容** - 保持 API 向后兼容
4. **职责分离** - 明确 `infra`（基础设施）与 `platform`（编排策略）的边界

### 📋 下一步

**Step 3**: 拆分 `graphs ↔ infra` 循环依赖（如果存在）

继续按照 6 步计划逐步拆分剩余循环依赖：
- Step 3: graphs ↔ infra
- Step 4: platform ↔ discovery
- Step 5: platform ↔ knowledge/testing/audit_engine
- Step 6: llm ↔ adapters
