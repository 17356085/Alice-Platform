好的，作为您的 AI 测试工程师搭档，我将严格依据您提供的两份“事实源” —— `AlarmConfigPage.py` Page Object 代码和 `test_alarm_config.py` 测试脚本，为您生成与代码实现完全对齐的页面上下文文档和元素定位明细。

---

### 产出文件1: `PAGE_CONTEXT.md` (完全基于代码实现)

```markdown
---
source: ai
source_agent: auto-strategy
created: 2026-06-18
---

# 页面上下文: 设备报警配置

- **页面名称**: 设备报警配置
- **所属模块**: 设备管理 (equipment)
- **URL**: `http://8.136.215.171:8081/equipment/alarm-config`
- **分析依据**: 代码实现 (AlarmConfigPage.py, test_alarm_config.py)

## 1. 页面整体结构

页面为典型的“顶部导航 + 左侧菜单 + 右侧主内容”布局。右侧主内容区自上而下分为：

1.  **统计卡片区**：位于内容区顶部，显示`报警规则总数`、`已启用`、`已禁用`、`今日报警`四个统计卡片。**注意**：卡片的数字在上，标签在下，非标准Element Plus组件，定位器需依赖XPath。
2.  **搜索/筛选区**：位于卡片区下方，采用 `el-form--inline` 布局。
3.  **数据表格区**：展示报警配置列表，表格存在 **fixed-right** 列（操作列），会导致DOM中存在克隆行，定位时需注意。
4.  **分页区**：位于表格底部，功能由测试脚本通过表格行验证间接覆盖。

## 2. 搜索/筛选区

| 元素ID | 元素描述 | 控件类型 | 定位策略 | 稳定性 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `INPUT_KEYWORD` | 报警名称/设备名称 | `el-input` | **CSS** | A | 通过 `placeholder` 属性定位，是稳定、高效的首选方案 |
| `SELECT_ALARM_TYPE` | 报警类型 | `el-select` | **XPath (索引)** | B | 依赖索引`[1]`，若搜索区元素重排会失效。`el-select`下拉面板会通过Teleport渲染到`<body>`下。 |
| `SELECT_ALARM_LEVEL` | 报警级别 | `el-select` | **XPath (索引)** | B | 依赖索引`[2]`，同上。 |
| `SELECT_STATUS` | 状态 | `el-select` | **XPath (索引)** | B | 依赖索引`[3]`，同上。 |
| `BTN_SEARCH` | 查询 | `el-button` | **XPath (文本+样式)** | A | 通过 `el-button--primary` 样式和 `查询` 文本组合定位，较稳定。 |
| `BTN_RESET` | 重置 | `el-button` | **XPath (文本)** | B | 仅通过文本匹配，页面若出现多个"重置"按钮可能导致歧义。 |
| `BTN_ADD` | 新增配置 | `el-button` | **XPath (文本)** | A | 独立于表单外，通过 `新增配置` 文本定位，是页面内的唯一按钮。 |

## 3. 表格/列表区

| 元素ID/方法 | 元素描述 | 控件类型 | 定位策略 | 稳定性 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TABLE_HEADER_CELLS` | 所有列头单元格 | `th .cell` | **CSS** | A | 直接通过CSS类选择，是稳定、高效的定位方案。 |
| `TABLE_ROWS` | 所有数据行 | `tr.el-table__row` | **CSS** | C | **存在fixed-right列，DOM中有两个tbody，定位会匹配到克隆行**。`get_table_data()`方法已特判处理此问题。 |
| `COL_ALARM_NAME` | 报警名称列索引 | `int` (常量) | N/A | A | 列索引从1开始，用于`get_table_data()`方法。 |
| `TABLE_EMPTY` | 空数据提示 | `.el-table__empty-text` | **CSS** | A | 表格无数据时的CSS提示文本。 |

## 4. 分页区

| 方法/交互 | 元素描述 | 控件类型 | 稳定性 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `get_table_data()` (间接) | 分页组件 | `el-pagination` | A | 功能在`get_table_data()`中被间接使用，通过获取所有表格行来判断是否有数据。 |

## 5. 弹窗/对话框

> **重要**：当前弹窗交互（新增/编辑/删除）均已被标记为 `@skip`，因为 `filterable el-select` 在 `is_displayed()` 判断时存在空指针异常，无法交互。
> 定位器 `DIALOG_SAVE_BTN` 和 `DIALOG_CANCEL_BTN` 已定义，但弹窗内具体表单元素尚未实现定位器。

| 元素ID | 元素描述 | 控件类型 | 定位策略 | 稳定性 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DIALOG_SAVE_BTN` | 弹窗确定/保存按钮 | `el-button` | **XPath (复合)** | B | 通过排除隐藏弹窗的样式`contains(@style,"display: none")`进行定位，逻辑较复杂，但能有效避免多个弹窗冲突。 |
| `DIALOG_CANCEL_BTN` | 弹窗取消按钮 | `el-button` | **XPath (复合)** | B | 与保存按钮同理，通过排除隐藏弹窗定位，较为健壮。 |

## 6. 页面特殊状态

| 状态 | 描述 | 处理方式 |
| :--- | :--- | :--- |
| **加载中** | `el-loading` 遮罩层 | `_wait_loading_gone()` (继承自BasePage) |
| **空数据** | 表格显示 `.el-table__empty-text` | `_wait_table_ready()` 中检查 |
| **Vue异步更新** | Vue 响应式更新导致的元素或数据变化 | `wait_vue_stable()` (继承自BasePage) |

## 7. 权限点

| 权限点 | 关联元素 | 备注 |
| :--- | :--- | :--- |
| 新增配置 | `BTN_ADD` | P0基线测试 (`test_ac_04`) 已覆盖其可见性 |
| 编辑 | （表格操作列） | 经确认admin用户可操作，但UI自动化目前跳过 |
| 删除 | （表格操作列） | 经确认admin用户可操作，但UI自动化目前跳过 |

## 8. 已知问题与处理

- **`fixed-right`列克隆**：`el-table`的固定列特性会导致DOM存在双份`el-table__row`。`get_table_data()`和表格列索引方法均已特殊处理此问题，保证数据唯一性。
- **`filterable el-select` 弹窗坑**：Element Plus 2.x 中，`filterable`模式下 el-select的下拉面板（popper）在`is_displayed()`判断时可能抛出空指针异常。此问题导致所有弹窗交互测试被跳过。
- **`el-select`索引定位**：搜索区的三个下拉框通过 `[1]`、`[2]`、`[3]` 索引定位，当搜索区组件调整顺序时，此定位会失效。未来可考虑通过其关联的 `label` 或 `placeholder` 属性进行优化。

```

---

### 产出文件2: `PAGE_ELEMENT_POSITION.md` (与代码实现对齐)

```markdown
---
source: ai
source_agent: auto-strategy
created: 2026-06-18
---

# 页面元素定位: 设备报警配置

- **页面名称**: 设备报警配置
- **所属模块**: 设备管理 (equipment)
- **分析依据**: Page Object 代码 (AlarmConfigPage.py)

## 元素定位明细

### 统计卡片区

| 元素ID / 方法 | 元素描述 | 定位策略 | 定位值 (Selector) | 稳定性 | 代码位置 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `STAT_VALUE_XPATH` | 统计卡片数值（XPath模板） | **XPath, 关系定位** | `//*[contains(normalize-space(.),"{label}")]/preceding-sibling::*[1]` | C | 类属性，全局，用于`_parse_stat`方法。**风险**：依赖`preceding-sibling`，若标签与数字的层级结构发生变化（如被其他div包裹），定位会失效。 |
| `STAT_CARD_CONTAINER` | 统计卡片容器 | **CSS** | `.stat-value` | A | 类属性。此CSS类名与代码中的注释吻合，定位稳定。 |

### 搜索/筛选区

| 元素ID | 元素描述 | 定位策略 | 定位值 (Selector) | 稳定性 | 代码变量名 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `INPUT_KEYWORD` | 关键词搜索框 | **CSS (属性选择器)** | `input[placeholder="报警名称/设备名称"]` | A | `INPUT_KEYWORD` |
| `SELECT_ALARM_TYPE` | 报警类型下拉 | **XPath (索引)** | `(//form[contains(@class,"el-form--inline")]//div[contains(@class,"el-select")])[1]` | B | `SELECT_ALARM_TYPE` |
| `SELECT_ALARM_LEVEL` | 报警级别下拉 | **XPath (索引)** | `(//form[contains(@class,"el-form--inline")]//div[contains(@class,"el-select")])[2]` | B | `SELECT_ALARM_LEVEL` |
| `SELECT_STATUS` | 状态下拉 | **XPath (索引)** | `(//form[contains(@class,"el-form--inline")]//div[contains(@class,"el-select")])[3]` | B | `SELECT_STATUS` |
| `BTN_SEARCH` | 查询按钮 | **XPath (文本 + 样式)** | `//form[contains(@class,"el-form--inline")]//button[contains(@class,"el-button--primary")][contains(.,"查询")]` | A | `BTN_SEARCH` |
| `BTN_RESET` | 重置按钮 | **XPath (文本)** | `//form[contains(@class,"el-form--inline")]//button[contains(.,"重置")]` | B | `BTN_RESET` |
| `BTN_ADD` | 新增配置按钮 | **XPath (文本)** | `//button[contains(.,"新增配置")]` | A | `BTN_ADD` |

### 数据表格区

| 元素ID | 元素描述 | 定位策略 | 定位值 (Selector) | 稳定性 | 代码变量名 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TABLE_HEADER_CELLS` | 所有列头单元格 | **CSS (层级选择器)** | `.el-table__header-wrapper th .cell` | A | `TABLE_HEADER_CELLS` |
| `TABLE_ROWS` | 所有数据行 | **CSS (层级选择器)** | `.el-table__body-wrapper tbody tr.el-table__row` | C | `TABLE_ROWS`。**存在fixed-right列克隆风险**，会匹配到两个`<tbody>`下的`<tr>`。 |
| `TABLE_EMPTY` | 空数据提示 | **CSS** | `.el-table__empty-text` | A | `TABLE_EMPTY` |

### 弹窗/对话框区

| 元素ID | 元素描述 | 定位策略 | 定位值 (Selector) | 稳定性 | 代码变量名 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DIALOG_SAVE_BTN` | 弹窗确定/保存按钮 | **XPath (复合, 排除隐藏)** | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(@class,"el-button--primary")][contains(.,"确定")]` | B | `DIALOG_SAVE_BTN` |
| `DIALOG_CANCEL_BTN` | 弹窗取消按钮 | **XPath (复合, 排除隐藏)** | `//div[contains(@class,"el-dialog") and not(contains(@style,"display: none"))]//button[contains(.,"取消")]` | B | `DIALOG_CANCEL_BTN` |

> **说明**:
> - 稳定性评级: A (稳定) / B (相对稳定) / C (不稳定或有风险)。
> - 当前 `PAGE_ELEMENT_POSITION.md` 严格基于 `AlarmConfigPage.py` 中声明的定位器，**不包含**代码中未实现的（弹窗内部表单）元素。
> - 对于通过方法间接操作的元素（如`_parse_stat`方法中的动态XPath、`get_text`方法），此处已列出其核心策略。

```