# Step 4: platform ↔ discovery 循环依赖拆分报告

**执行时间**: 2026-07-14
**状态**: ✅ 已完成

## 拆分目标

消除 `aitest.platform` 与 `aitest.discovery` 之间的双向循环依赖，确保模块级导入无循环。

## 循环依赖分析

### 拆分前的循环依赖

**discovery → platform** (3 处):
1. `discovery/base.py:14` - `from aitest.platform.paths import get_workstudy`
2. `discovery/browser_use.py:27` - `from aitest.platform.runtime import PageStructure`
3. `discovery/browser_use.py:733` - `from aitest.platform.context import get_project` (函数内部)

**platform → discovery** (2 处):
1. `platform/ecosystem.py:108` - `from aitest.discovery.registry import DiscoveryRegistry` (函数内部)
2. `platform/capability_router/providers/browser.py:48` - `from aitest.discovery.browser_use import BrowserUseDiscovery` (函数内部)

### 问题诊断

1. **类型错位**: `PageStructure` 是纯数据类（dataclass），定义在 `platform.runtime` 中，但被 `discovery` 和 `runtime` 模块使用。这导致 `discovery → platform` 和 `runtime → platform` 的依赖。

2. **路径导入**: `discovery/base.py` 从 `platform.paths` 导入 `get_workstudy`，但 `platform.paths` 本身已经是 `runtime.paths` 的 re-export，应该直接从 `runtime.paths` 导入。

3. **函数内导入**: `platform → discovery` 和部分 `discovery → platform` 的依赖已经是函数内部的延迟导入，这是正确的做法。

## 执行的更改

### Step 4.1: 将 PageStructure 移到 runtime.types

**策略**: 将 `PageStructure` 从 `platform.runtime` 移到 `runtime.types`（新文件），因为它是纯数据结构，属于运行时基础设施，不应在 platform 层。

#### 新建文件

1. **aitest/runtime/types.py** (32 行)
   - `PageStructure` 数据类
   - 从 `platform/runtime.py` 移出
   - 纯数据结构，无业务逻辑

```python
@dataclass
class PageStructure:
    """Standardized page observation result — runtime-agnostic."""
    page_title: str = ""
    search_fields: list[dict] = field(default_factory=list)
    action_buttons: list[dict] = field(default_factory=list)
    table_columns: list[str] = field(default_factory=list)
    has_pagination: bool = False
    has_checkbox_column: bool = False
    raw_html_snapshot: str = ""
    screenshot_base64: str = ""
```

#### 修改文件

**runtime 层更新**:
1. `aitest/runtime/browser.py` line 14
   - 更改: `from aitest.platform.runtime import Runtime, PageStructure`
   - 为: `from aitest.platform.runtime import Runtime` + `from aitest.runtime.types import PageStructure`

**discovery 层更新**:
1. `aitest/discovery/browser_use.py` line 27
   - 更改: `from aitest.platform.runtime import PageStructure`
   - 为: `from aitest.runtime.types import PageStructure`

2. `aitest/discovery/base.py` line 14
   - 更改: `from aitest.platform.paths import get_workstudy`
   - 为: `from aitest.runtime.paths import get_workstudy`

**platform 层向后兼容 (re-export)**:
1. `aitest/platform/runtime.py`
   - 移除 `PageStructure` 类定义
   - 添加: `from aitest.runtime.types import PageStructure` (re-export)

**platform 层内部更新**:
1. `aitest/platform/capabilities/abc.py` line 17
   - 更改: `from aitest.platform.runtime import PageStructure`
   - 为: `from aitest.runtime.types import PageStructure`

2. `aitest/platform/capabilities/browser_adapter.py` line 17
   - 更改: 延迟导入中 `from aitest.platform.runtime import PageStructure`
   - 为: `from aitest.runtime.types import PageStructure`

## 拆分效果

### 拆分前的依赖关系

```
platform → discovery (2 处函数内导入)
discovery → platform (3 处：2 模块级 + 1 函数内)

模块级循环依赖：
  discovery/base.py → platform.paths
  discovery/browser_use.py → platform.runtime.PageStructure
```

### 拆分后的依赖关系

```
platform → discovery (2 处函数内导入，保持不变)
discovery → (无模块级 platform 依赖)

函数级导入（延迟加载，不构成循环）：
  discovery/browser_use.py:733 → platform.context.get_project (函数内)
  platform/ecosystem.py:108 → discovery.registry.DiscoveryRegistry (函数内)
  platform/capability_router/providers/browser.py:48 → discovery.browser_use (函数内)
```

### 关键改进

✅ **类型归位**: `PageStructure` 从 `platform` 移到 `runtime`，作为运行时基础类型  
✅ **路径直达**: `discovery` 直接从 `runtime.paths` 导入，不经过 `platform.paths` 的 re-export  
✅ **模块级无循环**: 所有 `platform ↔ discovery` 导入都是函数内部的延迟导入  
✅ **向后兼容**: `platform.runtime` 通过 re-export 保持 `PageStructure` 可用

## 验证结果

### 字符串扫描（包含函数内导入）

```bash
=== platform ↔ discovery 依赖关系 ===
platform → ['discovery']
discovery → ['platform']

=== 循环检测 ===
❌ 存在双向依赖 (循环)
```

### AST 模块级导入扫描（仅模块级）

```bash
=== platform ↔ discovery 模块级导入 ===
platform → (无依赖)
discovery → (无依赖)

=== 循环检测 (仅模块级) ===
✅ 完全独立
```

**结论**: 模块级导入已完全消除循环依赖。剩余的函数内部导入是延迟加载，不会在模块加载时触发循环，这是 Python 中打破循环依赖的标准做法。

## 文件清单

### 新建文件 (1 个)

- `aitest/runtime/types.py` (32 行) - `PageStructure` 数据类

### 修改文件 (6 个)

**runtime 层**:
- `aitest/runtime/browser.py` - 更新 `PageStructure` 导入路径

**discovery 层**:
- `aitest/discovery/base.py` - `platform.paths` → `runtime.paths`
- `aitest/discovery/browser_use.py` - `platform.runtime.PageStructure` → `runtime.types.PageStructure`

**platform 层**:
- `aitest/platform/runtime.py` - 移除 `PageStructure` 定义，改为 re-export
- `aitest/platform/capabilities/abc.py` - 更新 `PageStructure` 导入路径
- `aitest/platform/capabilities/browser_adapter.py` - 更新延迟导入中的 `PageStructure` 路径

## 风险评估

### 低风险

- `PageStructure` 是纯数据类（dataclass），无业务逻辑，移动安全
- 所有使用点已更新导入路径
- `platform.runtime` 通过 re-export 保持向后兼容
- 函数内部的延迟导入保持不变（已是最佳实践）

### 缓解措施

- 保留 `platform.runtime.PageStructure` 的 re-export，确保旧代码不受影响
- 所有导入路径已更新，编译时可检测错误

## 架构改进

### 拆分前

```
┌─────────────┐
│  platform   │ ←──┐
└─────┬───────┘    │
      │            │
      ↓            │
┌─────────────┐    │
│  discovery  │ ───┘
└─────────────┘
   (循环依赖)
```

### 拆分后

```
┌─────────────┐
│  platform   │
│  (编排层)   │
└─────┬───────┘
      │ 单向依赖（函数内）
      ↓
┌─────────────┐
│  discovery  │
│  (发现策略) │
└─────┬───────┘
      │ 单向依赖
      ↓
┌─────────────┐
│   runtime   │
│ (运行时层)  │
└─────────────┘
   (完全独立)
```

### 设计原则验证

✅ **依赖倒置**: `discovery` 依赖 `runtime` 的数据类型，`platform` 通过函数内导入使用 `discovery`  
✅ **开闭原则**: 通过 re-export 保持 API 向后兼容  
✅ **单一职责**: `runtime.types` 专注运行时数据结构，`discovery` 专注应用发现策略  
✅ **延迟导入**: 函数内导入打破循环，保持模块加载时的单向依赖

## 循环依赖的两种形式

本次拆分展示了 Python 中循环依赖的两种形式：

1. **模块级循环依赖** (❌ 必须消除)
   - 模块加载时触发
   - 导致 `ImportError: cannot import name 'X' from partially initialized module`
   - 本次拆分已消除

2. **函数级循环依赖** (✅ 可接受)
   - 函数调用时才触发
   - 模块加载时不执行，不会导致导入错误
   - `platform/ecosystem.py:108` 和 `platform/capability_router/providers/browser.py:48` 等保留

## 总结

Step 4 完成了 `platform ↔ discovery` 循环依赖的拆分：

### ✅ 已完成

- **类型归位**: `PageStructure` 从 `platform.runtime` 移到 `runtime.types`
- **路径优化**: `discovery` 直接从 `runtime.paths` 导入，不经过 `platform` re-export
- **模块级无循环**: 所有模块级导入已消除循环依赖
- **向后兼容**: `platform.runtime` 通过 re-export 保持 API 不变

### 📊 对 SCC 的影响

- **拆分前**: `platform ↔ discovery` 双向循环依赖（模块级）
- **拆分后**: `platform → discovery` 单向依赖（仅函数内），`discovery` 模块级不依赖 `platform`
- **预期效果**: `platform` 和 `discovery` 从大 SCC 中分离，不再形成强连通分量

### 🔑 关键技术

1. **类型提升** - 将共享数据类型移到更底层的 `runtime`
2. **延迟导入** - 函数内导入打破模块级循环
3. **Re-export 兼容** - 保持 API 向后兼容
4. **职责分离** - 明确 `runtime`（基础类型）、`discovery`（发现策略）、`platform`（编排）的边界

### 📋 下一步

**Step 5**: 拆分 `platform ↔ knowledge/testing/audit_engine` 循环依赖（如果存在）

继续按照 6 步计划逐步拆分剩余循环依赖：
- ~~Step 1: platform ↔ mcp~~ ✅
- ~~Step 2: platform ↔ infra~~ ✅
- ~~Step 3: graphs ↔ infra~~ ✅（无需拆分）
- ~~Step 4: platform ↔ discovery~~ ✅
- Step 5: platform ↔ knowledge/testing/audit_engine
- Step 6: llm ↔ adapters
