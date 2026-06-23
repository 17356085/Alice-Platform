# AUTO_STRATEGY — lab / water-indicator

> **策略版本**: 1.0  
> **分析日期**: 2026-06-18  
> **作者**: Agent (auto-strategy)  
> **页面ID**: `water-indicator` | **模块**: `lab`  
> **页面类型**: 只读展示页（无搜索、无分页、无CRUD）

---

## 1. 自动化覆盖矩阵

| 用例编号 | 标题                                     | 优先级 | 是否自动化 | 理由                           |
| -------- | ---------------------------------------- | ------ | ---------- | ------------------------------ |
| WI-01    | 正常显示水质分析设计指标列表及相关字段     | P0     | ✅         | 基础冒烟，定位器稳定，必须自动化 |
| WI-02    | 表格列数据可读                           | P1     | ✅         | 核心列验证，定位器中等稳定，建议自动化 |

**说明**  
- 两个用例均为页面基础功能验证，无一次性操作风险。  
- 定位器均为 `.el-table__body-wrapper`、`.el-table__header-wrapper` 等稳定 CSS 类，风险低。  
- `get_column_data` 使用的 XPath 定位器评级为 **C 级（中）**，但在实际运行时已通过 `_wait_loading_gone` 确保表格渲染完毕，稳定性可接受。建议监控：若该列数据频繁为空或抛出 `StaleElementReferenceException`，可降级为备用 CSS 定位器 `td:nth-child(2) div.cell`。

---

## 2. PageObject 拆分方案

| Page 类                 | 职责                                     | 说明                                                 |
| ----------------------- | ---------------------------------------- | ---------------------------------------------------- |
| `WaterIndicatorPage`    | 水质分析设计指标页面的所有操作             | 只读展示页，无复杂弹窗或子组件，无需额外拆分           |
| （无独立 Dialog 类）     | 页面中的 `el-dialog` 仅为通用预留，当前无实际交互 | 当后续版本增加弹窗功能时，可独立为 `WaterIndicatorDialog` |

**建议**  
- 遵循“一个页面一个 Page 类”原则，当前页面复杂度低，无需拆分。  
- 若未来新增搜索/分页/CRUD 功能，应扩展此类而非拆分为多个 Page 类。  
- 对称页面 `GasIndicatorPage` 结构完全一致，可复用相同的 Page 设计模式。

---

## 3. 公共组件复用分析

| 已有 BasePage 方法                | 当前使用情况 | 是否需要扩展           |
| --------------------------------- | ------------ | ---------------------- |
| `navigate_to(menu, submenu)`      | ✅ 已使用     | 无需扩展               |
| `wait_page_ready(timeout)`        | ✅ 已使用     | 无需扩展               |
| `wait_vue_stable()`               | ✅ 已使用     | 无需扩展               |
| `_wait_loading_gone(timeout)`     | ✅ 已使用     | 无需扩展               |
| `get_table_headers`（自定义）      | ✅ 已实现     | 当前页面专用，无需上移基类 |
| `get_table_row_count`（自定义）    | ✅ 已实现     | 可考虑通用化 → 若其他页面同样使用 `.el-table__body-wrapper tbody tr`，可提取到 `ElementPlusHelper` |
| `get_column_data`（自定义）        | ✅ 已实现     | 逻辑通用（列序号参数），推荐提取到 `ElementPlusHelper.get_column_data(col_index, table_locator=None)` |
| `get_empty_text`（自定义）         | ✅ 已实现     | 逻辑通用，推荐提取到 `ElementPlusHelper.get_empty_text(table_locator=None)` |

**扩展建议**  
- 将 `get_column_data` 和 `get_empty_text` 通用化为 `ElementPlusHelper` 方法，减少重复代码。  
- 当前页面仅 4 个交互方法，全部可在 Page 类内维护，不急于重构。

---

## 4. 等待策略建议

### 页面异步行为分析  
| 行为                      | 触发条件                      | 等待策略                                                     | 当前已实现？ |
| ------------------------- | ----------------------------- | ------------------------------------------------------------ | ------------ |
| 页面路由/菜单跳转           | `navigate()`                  | `wait_page_ready()`（内置 `document.readyState`） + `wait_vue_stable()`（Vue 渲染完成） | ✅            |
| 数据加载（`el-loading`）    | 进入页面或刷新                | `_wait_loading_gone()`：等待 `.el-loading-mask` 消失或 10s 超时 | ✅            |
| 表格 DOM 稳定               | 数据加载后                    | `wait_vue_stable()` 确保 Vue 异步更新完成                       | ✅            |
| 无数据场景的渲染            | 后端返回空数组                | `get_empty_text()` 依赖 `.el-table__empty-text` 的隐式存在，无需额外等待 | ✅            |

### 建议的等待封装  
当前等待策略已覆盖所有场景，无需新增。  
**注意事项**：`_wait_loading_gone` 使用隐式等待 + 显式循环，若未来 Element Plus 升级导致 `el-loading-mask` 类名变化，需同步更新。建议在 `ElementPlusHelper` 中维护 `wait_table_ready` 方法，统一处理表格加载等待。

---

## 5. ROI 分析

### 估算参数

| 参数                   | 估计值         | 说明                                                         |
| ---------------------- | -------------- | ------------------------------------------------------------ |
| 开发时间（首次）         | X = **2 小时** | PageObject 编写（0.5h） + 测试脚本编写（0.5h） + 调试（1h）  |
| 维护成本（每月）         | Y = **0.5 小时** | 页面极少变更，仅需维护等待超时或 Element Plus 升级           |
| 手工执行时间（每次）     | Z = **2 分钟** | 手动打开页面、检查表头和列数据（使用肉眼比对）                 |
| 回归执行频率             | **4 次/月**    | 假设每周一次回归测试                                         |
| 自动化执行时间（每次）   | **0.5 分钟**   | 运行两个用例（含 setup/teardown）                             |
| 自动化脚本生命周期       | **24 个月**    | 假设页面结构 2 年内不发生重大变化                             |

### ROI 计算

**手工执行总成本（24 月）**  
= Z × 执行频率 × 24  
= 2 min × 4 次/月 × 24 月 = **192 分钟** ≈ **3.2 小时**

**自动化总成本（24 月）**  
= 开发时间 + 维护成本 × 24  
= 2 小时 + 0.5 小时/月 × 24 月 = **14 小时**

**净收益**  
= 手工总成本 - 自动化总成本  
= 3.2 小时 - 14 小时 = **-10.8 小时**（负收益）

**分析**  
- 当前页面复杂度极低，手工执行时间很短，自动化投入在 2 年内无法回收成本。  
- **建议**：仍保留自动化 P0 用例（WI-01）用于冒烟回归，WI-02 可降为手动检查（或作为探索性测试）。  
- 若页面未来增加搜索/分页/CRUD 功能或手工执行频率提升，自动化收益将转为正。

### 风险标注  
- **定位器风险**：`get_column_data` 使用 XPath（C 级），若 DOM 结构调整或 Element Plus 升级可能导致失败，增加维护成本。  
- **一次性操作**：无。  
- **数据依赖**：测试需要真实用户 Session 以验证权限（列数据可能因角色不同而变化），建议在 CI 中使用固定测试账号。

---

## 附件

- PageObject 源码：`modules/lab/pages/water-indicator/WaterIndicatorPage.py`  
- 测试脚本：`modules/lab/tests/test_water_indicator.py`  
- 技术分析：`modules/lab/pages/water-indicator/TECH_ANALYSIS.md`  

> **最终建议**：按 P0 自动化 WI-01，WI-02 暂不自动化为自动化，待页面功能扩展后再重新评估。