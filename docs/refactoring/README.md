# 循环依赖拆分文档索引

**执行日期**: 2026-07-14  
**状态**: ✅ 全部完成

## 📋 报告文件

| # | 模块对 | 结果 | 报告文件 |
|---|--------|------|----------|
| 总结 | 全部 7 步 | 4/4 拆分成功 | [SUMMARY.md](./SUMMARY.md) |
| 1 | platform ↔ mcp | ✅ 已拆分 | STEP1_PLATFORM_MCP_SPLIT_REPORT.md (之前完成) |
| 2 | platform ↔ infra | ✅ 已拆分 | [STEP2_PLATFORM_INFRA_SPLIT_REPORT.md](./STEP2_PLATFORM_INFRA_SPLIT_REPORT.md) |
| 3 | graphs ↔ infra | ✅ 无需拆分 | [STEP3_GRAPHS_INFRA_SPLIT_REPORT.md](./STEP3_GRAPHS_INFRA_SPLIT_REPORT.md) |
| 4 | platform ↔ discovery | ✅ 已拆分 | [STEP4_PLATFORM_DISCOVERY_SPLIT_REPORT.md](./STEP4_PLATFORM_DISCOVERY_SPLIT_REPORT.md) |
| 5 | platform ↔ knowledge/testing/audit_engine | ✅ 无需拆分 | [STEP5_PLATFORM_APPS_SPLIT_REPORT.md](./STEP5_PLATFORM_APPS_SPLIT_REPORT.md) |
| 6 | llm ↔ adapters | ✅ 无需拆分 | [STEP6_LLM_ADAPTERS_SPLIT_REPORT.md](./STEP6_LLM_ADAPTERS_SPLIT_REPORT.md) |
| 7 | knowledge ↔ mcp ↔ platform（三角循环） | ✅ 已拆分 | [STEP7_KNOWLEDGE_MCP_PLATFORM_TRIANGLE_REPORT.md](./STEP7_KNOWLEDGE_MCP_PLATFORM_TRIANGLE_REPORT.md) |

## 📊 快速统计

### 拆分成果

- **需要拆分**: 4 组（Step 1, 2, 4, 7）
- **拆分成功**: 4/4 (100%)
- **无需拆分**: 3 组（Step 3, 5, 6）- 已是单向依赖

### 代码变更

- **新建文件**: 8 个（~350 行代码）
- **修改文件**: 20 个
- **核心技术**: 模块提升、配置继承、Re-export、延迟导入、职责分离

## 🔧 拆分技术

### 1. 模块提升 (Module Elevation)
将共享类型移到更底层的模块，避免上层模块互相依赖。

**应用**:
- Step 2: ORM 模型 `platform` → `infra/models/`
- Step 4: `PageStructure` `platform.runtime` → `runtime.types`

### 2. 配置继承扩展 (Configuration Extension)
通过继承扩展配置，遵循开闭原则。

**应用**:
- Step 2: `PlatformConfigExtended` 继承 `_BasePlatformConfig`

### 3. Re-export 兼容 (Re-export Compatibility)
保持 API 向后兼容，逐步迁移。

**应用**:
- Step 2: `platform.*_models` re-export from `infra.models.*`
- Step 4: `platform.runtime.PageStructure` re-export from `runtime.types`

### 4. 延迟导入 (Lazy Import)
函数内部导入打破模块级循环。

**应用**:
- Step 4: `platform/ecosystem.py:108` 和 `discovery/browser_use.py:733`

### 5. 职责分离 (Separation of Concerns)
明确各层边界，避免越界依赖。

**分层**:
- **infra**: 基础设施层（db, logging, ORM）
- **runtime**: 运行时层（paths, context, types）
- **platform**: 平台层（编排、策略）
- **应用层**: 使用平台服务（knowledge, audit_engine）

## 🎯 架构改进

### 拆分前
```
┌───────────────────────────────┐
│  大 SCC (强连通分量)          │
│  platform ↔ infra ↔ discovery │
└───────────────────────────────┘
```

### 拆分后
```
应用层 (graphs, knowledge, audit_engine)
  ↓ 单向依赖
平台层 (platform)
  ↓ 单向依赖
基础层 (infra, runtime, discovery, mcp)
  ↓ 单向依赖
适配器层 (adapters)
```

## 📝 关键文件

### 新建文件

**infra 层 ORM 模型** (Step 2):
- `aitest/infra/models/__init__.py`
- `aitest/infra/models/workflow.py`
- `aitest/infra/models/model_provider.py`
- `aitest/infra/models/secret.py`
- `aitest/infra/models/environment.py`
- `aitest/infra/models/quality.py`
- `aitest/infra/models/worker_lease.py`

**runtime 层数据类型** (Step 4):
- `aitest/runtime/types.py`

### 主要修改文件

**infra 层**:
- `aitest/infra/models.py` - 更新 import 路径
- `aitest/infra/config_registry.py` - 移除平台配置

**platform 层**:
- `aitest/platform/config_registry.py` - 继承扩展
- `aitest/platform/runtime.py` - re-export PageStructure
- `aitest/platform/*_models.py` (6 个) - re-export ORM 模型

**discovery 层**:
- `aitest/discovery/base.py` - 直接导入 runtime.paths
- `aitest/discovery/browser_use.py` - 使用 runtime.types

**runtime 层**:
- `aitest/runtime/browser.py` - 使用 runtime.types

## 🚀 下一步建议

1. **运行完整 SCC 检测**: 验证最大 SCC 大小是否显著减少
2. **更新架构文档**: 将分层架构记录到 `docs/architecture/LAYERS.md`
3. **持续监控**: CI/CD 中添加循环依赖检测
4. **逐步清理 re-export**: 未来重构中更新导入路径

## 📚 详细说明

每个 Step 的详细报告包含：

- **循环依赖分析**: 具体的依赖关系和行号
- **问题诊断**: 循环依赖的根本原因
- **执行的更改**: 新建/修改的文件和代码片段
- **拆分效果**: 拆分前后的依赖关系对比
- **验证结果**: AST 扫描确认无循环
- **架构改进**: 设计原则验证

请查阅具体的 Step 报告获取完整技术细节。
