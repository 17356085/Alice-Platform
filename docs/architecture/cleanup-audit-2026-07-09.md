# SDK 迁移依赖审计报告

**执行日期**: 2026-07-09  
**执行人**: AI Agent  
**基于**: SDK迁移执行清单 v1.0

---

## 审计结果摘要

| 检查项 | 状态 | 发现 | 优先级 |
|--------|------|------|--------|
| 1. SDK → 平台依赖 | ✅ 通过 | SDK 无 `aitest.*` 导入 | - |
| 2. CLI → SDK 公共 API | ✅ 已修复 | 混合导入策略（2 处过渡） | - |
| 3. Discovery 重复 | ✅ 非重复 | `aitest/discovery/` 是平台层 | - |
| 4. 弃用 Providers | ⚠️ 过渡代码 | 2 处导入（兼容层） | **中** |
| 5. Runtime 归属 | ✅ 已明确 | `runtime/` 是实现层，`platform/infra/` 是 re-export | - |

---

## 详细发现

### ✅ 检查 1: SDK 无平台依赖

**命令**:
```bash
cd packages/alice-engine
grep -rn "from aitest\." alice_engine/ | grep -v "__pycache__" | grep -v "/test"
```

**结果**: 空输出（Exit code 1，表示无匹配）

**结论**: ✅ **SDK 完全独立**，无任何 `aitest.*` 导入。这是最重要的成功标志。

---

### ⚠️ 检查 2: CLI 使用 SDK 公共 API

**命令**:
```bash
grep -rn "from aitest\.engine\." aitest/cli/
grep -rn "from aitest\.graphs\." aitest/cli/
grep -rn "from aitest\.llm\." aitest/cli/
```

**结果**: 发现 **3 处内部导入**

#### 问题文件：

1. **aitest/cli/adapters/engine_adapter.py:49**
   ```python
   from aitest.engine.extensions import (
   ```

2. **aitest/cli/commands/run.py:36**
   ```python
   from aitest.engine.event_bus import get_event_bus
   ```

3. **aitest/cli/commands/run.py:81**
   ```python
   from aitest.engine.extensions import (
   ```

**影响**: CLI 绕过 SDK 公共 API，直接导入平台层的 `aitest.engine` 模块。

**建议行动**:
- 重构这 3 处导入
- 使用 `from alice_engine import ...` 或 `from alice_engine.extensions import ...`
- 如果 `event_bus` 不在 SDK 公共 API → 添加到 SDK 或移至平台便利层

**优先级**: **高**（阻止 SDK 独立使用）

---

### ✅ 检查 3: Discovery 分层分析

**命令**:
```bash
grep -rn "from aitest\.discovery" . | grep -v "__pycache__"
```

**结果**: 发现 **5 个文件**使用 `aitest.discovery`

#### 使用分析：

**平台层文件**:
1. `aitest/platform/ecosystem.py` — 导入 `DiscoveryRegistry`（插件注册表）
2. `aitest/onboarding/project_onboarding_agent.py` — 导入 `BrowserUseDiscovery`（运行时发现）
3. `aitest/platform/capability_router/providers/browser.py` — 导入 `BrowserUseDiscovery`（可用性检查）
4. `aitest/tests/platform/test_ecosystem.py` — 导入 `DiscoveryRegistry`（测试）
5. `aitest/discovery/registry.py` — 自引用

#### 架构分析：

**`alice-discovery` (SDK)**:
- **定位**: 静态源码分析（Vue/React 路由、组件、API 提取）
- **输出**: `ProjectKnowledge`, `PageMetadata`, `RouteMetadata`
- **依赖**: 零平台依赖（纯 AST 解析）
- **使用场景**: 开源 SDK，外部项目可独立使用

**`aitest/discovery/` (平台)**:
- **定位**: 运行时发现机制（Registry + BrowserUse 集成）
- **核心类**:
  - `DiscoveryRegistry` — 插件注册表（管理多种发现策略）
  - `BrowserUseDiscovery` — AI 驱动的运行时页面发现（依赖 `aitest.platform.runtime`）
  - `BaseDiscovery` — 平台扩展点（抽象基类）
- **依赖**: `aitest.platform.runtime`, `aitest.platform.paths`
- **使用场景**: 平台内部，协调 SDK 和运行时发现

#### 类对比：

| 类名 | alice-discovery (SDK) | aitest/discovery/ (平台) | 关系 |
|------|----------------------|-------------------------|------|
| `BaseDiscovery` | ✅ 有（纯抽象） | ✅ 有（平台扩展点，依赖 `aitest.platform`） | 平台版本扩展 SDK |
| `PageRecord` | ✅ 有（作为 `PageMetadata`） | ✅ 有（平台格式，包含 `raw_dom_snapshot`） | 两者略有差异 |
| `MenuNode` | ✅ 有 | ✅ 有 | 相同结构 |
| `DiscoveryRegistry` | ❌ 无 | ✅ 有 | 平台特定 |
| `BrowserUseDiscovery` | ❌ 无 | ✅ 有 | 平台特定 |

**结论**: ✅ **不是重复代码，是分层设计**

- SDK 提供静态分析能力
- 平台提供运行时发现 + 插件管理
- 两者配合使用（Registry 可注册 SDK 的 `SourceDiscoveryPipeline`）

**建议行动**: 无需迁移，保留 `aitest/discovery/` 作为平台层

**优先级**: 无（误判已澄清）

---

### ⚠️ 检查 4: 弃用 Providers 使用

**命令**:
```bash
grep -rn "from aitest\.llm\.providers" . | grep -v "__pycache__"
```

**结果**: 发现 **2 处导入**

#### 使用文件：

1. **aitest/adapters/llm/interface.py:27-32**
   ```python
   # Legacy imports for backward compatibility (deprecated, will be removed in Phase 9)
   from aitest.llm.providers.claude import ClaudeProvider
   from aitest.llm.providers.openai import OpenAIProvider
   from aitest.llm.providers.ollama import OllamaProvider
   from aitest.llm.providers.deepseek import DeepSeekProvider
   from aitest.llm.providers.mimo import MiMoProvider
   from aitest.llm.providers.mock import MockProvider
   ```

2. **aitest/llm/providers/mock.py** （内部自引用）

**分析**:
- 这是**已规划的过渡代码**
- `interface.py` 明确标注 "deprecated, will be removed in Phase 9"
- 作为兼容层，委托给 `alice_engine.providers`

**建议行动**:
- **保留** `aitest/llm/providers/` 目录（暂时）
- 但需要验证：是否还有外部代码直接导入 `aitest.llm.providers.*`？
- 如果没有外部使用 → 可以删除，仅保留 `interface.py` 的 SDK 委托

**优先级**: **中**（已有迁移计划，非紧急）

---

### ✅ 检查 5: aitest/runtime/ 架构分析

**命令**:
```bash
grep -rn "from aitest\.runtime" . | grep -v "__pycache__"
```

**结果**: 发现 **40 处使用**，分布在 **19 个文件**

#### 架构现状：

**`aitest/runtime/` (实现层)**:
- **5 个文件**: `_paths_core.py`, `config.py`, `context.py`, `paths.py`, `error_handling.py`
- **依赖关系**: 零或最小平台依赖（`paths.py` 可选导入 `platform.context`）
- **被 40 处代码使用**

**`aitest/platform/` (兼容层)**:
- `platform/_paths_core.py` — re-export `runtime._paths_core`
- `platform/paths.py` — re-export `runtime.paths` 的 12 个函数

**`aitest/infra/` (兼容层)**:
- `infra/paths.py` — re-export `runtime._paths_core` 的 2 个函数
- `infra/error_logger.py` — 弃用警告，re-export `runtime.error_handling`

#### 历史迁移：

**v3.2 注释** (来自 `platform/paths.py`):
```python
# Re-export — 原 paths.py 已搬到 runtime/paths.py，此文件保证向后兼容
```

**v3.2 注释** (来自 `infra/paths.py`):
```python
# v3.2: Created to break infra → platform reverse dependency.
# Infra modules import from here instead of aitest.platform.paths.
```

**迁移历史**:
1. 最初：`platform/paths.py` 包含实现
2. v3.2：移至 `runtime/paths.py`（打破 infra → platform 依赖）
3. 兼容层：`platform/paths.py` 和 `infra/paths.py` 变为 re-export

#### 依赖分析：

| 文件 | 行数 | 外部依赖 | 性质 |
|------|------|---------|------|
| `runtime/_paths_core.py` | 19 | 零依赖 | 叶子模块 |
| `runtime/config.py` | 97 | 零依赖 | 环境变量读取 |
| `runtime/context.py` | 339 | `runtime._paths_core` | 上下文管理 |
| `runtime/paths.py` | 194 | `runtime._paths_core`, `platform.context`（可选） | 路径解析 |
| `runtime/error_handling.py` | 237 | `runtime.paths` | 错误日志 |

**`paths.py` 的循环依赖处理**:
```python
# 注入模式打破循环
_project_resolver = None

def register_project_resolver(resolver) -> None:
    global _project_resolver
    _project_resolver = resolver

def _get_project(project_id: str = None):
    if _project_resolver is not None:
        return _project_resolver(project_id)
    from aitest.platform.context import get_project  # 回退
    return get_project(project_id)
```

#### 架构合理性：

**为何 `runtime/` 是正确归属**:

1. **分层清晰**:
   - `runtime/` — 底层基础设施（配置、路径、上下文）
   - `platform/` — 平台层（项目管理、生态系统）
   - `infra/` — 基础设施（数据库、缓存、队列）

2. **依赖方向**:
   - `runtime/` ← `platform/` ← 上层
   - `runtime/` ← `infra/` （打破 `infra` → `platform` 反向依赖）

3. **零平台依赖**（几乎）:
   - 5 个文件中 4 个零外部依赖
   - `paths.py` 使用注入模式，可选导入 `platform.context`

**结论**: ✅ **`runtime/` 是正确的架构位置**

- 它是基础设施的**实现层**
- `platform/` 和 `infra/` 的 re-export 提供便利导入
- 历史迁移 `platform/ → runtime/` 是为了打破依赖循环

**建议行动**: 保留现状，无需迁移

**优先级**: 无（架构合理）

---

## 决策建议

### 高优先级（立即处理）

#### 1. 重构 CLI 内部导入（3 处）

**文件**: 
- `aitest/cli/adapters/engine_adapter.py`
- `aitest/cli/commands/run.py`（2 处）

**行动**:
```python
# 之前
from aitest.engine.extensions import AuditExtension
from aitest.engine.event_bus import get_event_bus

# 之后
from alice_engine.extensions import AuditExtension
from alice_engine.events import EventBus  # 或从 SDK 公共 API 获取
```

**工作量**: 半天

---

#### 2. 迁移 Discovery 导入（4 处）

**文件**:
- `aitest/platform/ecosystem.py`
- `aitest/onboarding/project_onboarding_agent.py`
- `aitest/platform/capability_router/providers/browser.py`
- `aitest/tests/platform/test_ecosystem.py`

**行动**:
```python
# 之前
from aitest.discovery import ...

# 之后
from alice_discovery import ...
```

**前提**: 验证 `alice-discovery` 包含所需 API

**工作量**: 1 天

---

#### 3. 明确 aitest/runtime/ 归属

**推荐方案**: **移至平台 infra**

**理由**:
- 19 个使用文件**全部**在 `aitest/` 平台层
- 无 SDK 使用（SDK 已独立）
- 主要是配置和路径工具

**行动**:
```bash
# 移动文件
mv aitest/runtime/config.py aitest/infra/runtime_config.py
mv aitest/runtime/paths.py aitest/infra/runtime_paths.py
mv aitest/runtime/context.py aitest/infra/runtime_context.py
mv aitest/runtime/error_handling.py aitest/infra/runtime_error_handling.py
mv aitest/runtime/_paths_core.py aitest/infra/_paths_core.py

# 更新导入（批量替换）
find aitest -name "*.py" -type f -exec sed -i 's/from aitest\.runtime/from aitest.infra/g' {} \;

# 删除空目录
rmdir aitest/runtime
```

**工作量**: 1 天（含测试）

---

### 中优先级（第 2 周处理）

#### 4. 清理弃用 Providers（待验证）

**前提**: 确认无外部代码直接使用 `from aitest.llm.providers import ClaudeProvider`

**行动**:
- 如果确认无使用 → 删除 `aitest/llm/providers/` 目录
- 保留 `aitest/adapters/llm/interface.py` 作为 SDK 委托层

**工作量**: 半天

---

## 更新的执行顺序

### 第 1 周（修订）

**Day 1-2**: ✅ 审计完成（本报告）

**Day 3**: 
- [x] 重构 CLI 内部导入（3 处）✅ 2026-07-09 完成
  - [x] `aitest/cli/adapters/engine_adapter.py:48-51` — 混合导入
  - [x] `aitest/cli/commands/run.py:36` — 保持 `get_event_bus()` 单例
  - [x] `aitest/cli/commands/run.py:80-83` — 混合导入
- [ ] 测试 CLI 命令（需要 Python 3.11+ 环境）

### 第 2 周

**Day 4**:
- [ ] 验证 `alice-discovery` API 完整性
- [ ] 迁移 Discovery 导入（4 处）
- [ ] 测试相关功能

**Day 5-6**:
- [ ] 移动 `aitest/runtime/` → `aitest/infra/`
- [ ] 批量更新导入
- [ ] 运行完整测试套件

**Day 7**:
- [ ] 验证弃用 Providers 无外部使用
- [ ] 删除 `aitest/llm/providers/`（如果安全）

---

## 附录：完整的 grep 输出

### CLI 内部导入（完整）
```
aitest/cli/adapters/engine_adapter.py:49:            from aitest.engine.extensions import (
aitest/cli/commands/run.py:36:    from aitest.engine.event_bus import get_event_bus
aitest/cli/commands/run.py:81:            from aitest.engine.extensions import (
```

### Discovery 使用（完整）
```
aitest/tests/platform/test_ecosystem.py
aitest/platform/ecosystem.py
aitest/onboarding/project_onboarding_agent.py
aitest/platform/capability_router/providers/browser.py
aitest/discovery/registry.py
```

### Providers 使用（完整）
```
aitest/adapters/llm/interface.py:27-32 (兼容层)
aitest/llm/providers/mock.py (自引用)
```

### Runtime 使用（完整）
```
aitest/adapters/llm/interface.py
aitest/tests/platform/test_provider_adapter.py
aitest/graphs/checkpoint.py
aitest/llm/provider_base.py
aitest/platform/ecosystem.py
aitest/platform/versioning.py
aitest/config.py
aitest/runtime/paths.py (内部)
aitest/runtime/context.py (内部)
aitest/adapters/event/interface.py
aitest/runtime/error_handling.py (内部)
aitest/adapters/llm/provider_base.py
aitest/adapters/audit/state.py
aitest/adapters/audit/sop.py
aitest/platform/_paths_core.py
aitest/platform/paths.py
aitest/platform/context.py
aitest/infra/paths.py
aitest/infra/error_logger.py
```

---

## 成功标准更新

| 标准 | 当前状态 | 目标 |
|------|----------|------|
| SDK 无平台依赖 | ✅ 已达成 | 保持 |
| CLI 使用 SDK 公共 API | ⚠️ 3 处内部导入 | 0 处 |
| 无重复模块 | ⚠️ Discovery 重复使用 | 删除 `aitest/discovery/` |
| 无弃用代码 | ⚠️ Providers 兼容层保留 | 评估后决定 |
| Runtime 归属明确 | ⚠️ 19 处使用待迁移 | 移至 `aitest/infra/` |

---

**报告结束**  
**下一步**: 执行第 1 周 Day 3 任务（重构 CLI 导入）
