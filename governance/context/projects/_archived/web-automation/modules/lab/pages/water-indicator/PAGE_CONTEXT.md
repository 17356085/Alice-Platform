好的，收到您的请求。作为Web端测试工程师，我将基于您提供的Page Object代码、测试脚本和页面上下文，进行页面结构分析并输出元素定位器设计。

---

## PAGE_CONTEXT — lab / water-indicator

> 基于 Phase 1 页面上下文、Page Object 代码及测试脚本分析
> **版本**: 2.0 | **最后更新**: 2026-06-18

### 1. 页面信息
- **页面ID**: `water-indicator`
- **页面名称**: 水质分析设计指标
- **所属模块**: `lab` (化验室取样)
- **页面路由**: `#/lab/water/indicator`
- **菜单路径**: 化验室取样 → 水质分析 → 水质分析设计指标
- **页面类型**: 只读展示页（无搜索、无分页、无CRUD）
- **数据行数**: 22

### 2. 页面整体结构
此页面为纯展示型页面，结构简洁，无复杂的区域划分。
- **主内容区**: 占据页面主体，核心为一个 Element Plus 的自定义表格（`el-table`），用于展示水质分析的参考/设计指标值。
- **无搜索/筛选区**: 页面不包含搜索、筛选或任何输入控件。
- **无分页区**: 22行数据一次性展示，无分页组件。

### 3. 页面元素清单

| 元素ID (ElementID) | 元素描述 | 控件类型 | 所在区域 | 备注 |
|:---|:---|:---|:---|:---|
| `table` | 水质分析设计指标展示表格 | `el-table` | 主内容区 | 只读，无操作列 |
| `loading` | 数据加载中的状态 | Vue Loading/骨架屏 | 主内容区 | `_wait_loading_gone()` 处理此状态 |
| `empty-text` | 表格无数据时的占位文本 | `el-table__empty-text` | 主内容区 | 文本内容通常为"暂无数据" |
| `dialog` | 通用弹窗组件 | `el-dialog` | 主内容区 | 代码中已定义但当前页面无使用场景，仅为通用预留 |

### 4. 表格列信息（基于 `get_table_headers` 和测试用例）

| 序号 | 列名 (Header) | 数据类型 | 示例值 | 备注 |
|:---|:---|:---|:---|:---|
| 1 | 序号 | 数字 (文本) | 1, 2 | 自动编号 |
| 2 | 指标名称 | 文本 | pH, COD, 氨氮 | **权限敏感字段** |
| 3 | 分类 | 文本 | 物理指标, 化学指标 | |
| 4 | 单位 | 文本 | mg/L, NTU | |
| 5 | 规则 | 文本 | ≤, ≥, = | 比较运算符 |
| 6 | 阈值 | 文本 (数字) | 6.5-8.5, 100 | 标准范围或单一值 |
| 7 | 备注 | 文本 | - | 可选 |

### 5. 页面状态

| 状态类型 | 表现 | 等待策略 |
|:---|:---|:---|
| **加载中** | 表格区域显示 `el-loading` 或骨架屏 | `wait_page_ready()` + `_wait_loading_gone()` |
| **空数据** | 表格内显示 `el-table__empty-text`，文本内容为"暂无数据" | `get_empty_text()` 方法识别 |
| **正常展示** | 表格加载完成，各列标题和22行数据正确渲染 | `wait_vue_stable()` + `_wait_loading_gone()` |

### 6. 权限点
- **`指标名称` 列 (`get_column_data(2)`)**:
  - 此列数据（如 pH, COD）可能包含敏感业务信息。
  - 不同角色的用户可能看到不同的指标列表或该列被完全隐藏。
  - **自动化测试建议**: 在测试用例中使用实际用户的Session登录，验证此列数据是否符合其角色权限。

---

## PAGE_ELEMENT_POSITION — lab / water-indicator

> 基于 `WaterIndicatorPage.py` 代码分析
> **版本**: 2.0 | **最后更新**: 2026-06-18

### 元素定位器设计

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `table` | **B级 - CSS Selector** | `.el-table__body-wrapper` | 高 | `(By.TAG_NAME, "table")` | 直接定位表格体，而非整个表格 |
| `table-rows` | **B级 - CSS Selector** | `.el-table__body-wrapper tbody tr` | 高 | `(By.XPATH, ".//div[contains(@class,'el-table__body-wrapper')]//tbody/tr")` | |
| `empty-text` | **B级 - CSS Selector** | `.el-table__empty-text` | 高 | `(By.XPATH, "//div[contains(@class, 'el-table__empty-text')]")` | |
| `dialog` | **B级 - CSS Selector** | `.el-dialog:not([style*="display: none"])` | 中 | `(By.XPATH, "//div[contains(@class,'el-dialog') and not(contains(@style,'display: none'))]")` | 通用定位器，稳定性依赖于弹窗的CSS类 |
| `column-header-text` | **B级 - JavaScript** | `.el-table__header-wrapper th .cell` | 高 | `(By.CSS_SELECTOR, "th.el-table__cell div.cell")` | 使用JS获取文本更稳定，避免元素不可见问题 |
| `cell-data` | **C级 - XPath** | `.//div[contains(@class,"el-table__body-wrapper")]//tbody/tr/td[{col_index}]//div[contains(@class,"cell")]` | 中 | `(By.CSS_SELECTOR, ".el-table__body-wrapper td:nth-child({col_index}) .cell")` | `col_index` 为动态参数，XPath通用性更强，但依赖页面结构 |

### 等待策略总览

| UI 交互 | 触发方式 | 等待条件 | 等待策略实现 | 超时阈值 |
|:---|:---|:---|:---|:---|
| 页面导航 (navigate) | `navigate()` 方法调用 | 菜单展开完成，页面路由变更 | `self.wait_page_ready(timeout=15)` | 15秒 |
| 数据加载 | URL导航完成 | Loading 元素消失 | `self._wait_loading_gone(timeout=10)` | 10秒 |
| Vue 响应式更新 | `get_table_headers()` 等调用前 | DOM稳定，Vue渲染完成 | `self.wait_vue_stable()` | 默认(取决于`wait_vue_stable`实现) |
| 空数据状态 | `get_empty_text()` 调用 | 无数据 | `自旋等待1-2s后直接获取文本` | 无显式等待，由调用方控制 |