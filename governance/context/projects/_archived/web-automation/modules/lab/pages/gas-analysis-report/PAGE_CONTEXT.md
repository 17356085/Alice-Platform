好的，遵照指示。我将基于你提供的 `Page Object` 代码、`测试脚本` 和初步的 `PAGE_CONTEXT.md`，以 **代码反推为主，需求文档为辅** 的双源验证模式，生成最终的 `PAGE_CONTEXT.md`。

---

## `PAGE_CONTEXT.md`

### 1. 页面基本信息
- **页面名称**: 气体分析报告单
- **模块**: `lab` (实验室)
- **路由**: `#/lab/gas/report`
- **Page Object**: `GasAnalysisReportPage` (位于 `page/lab_page/`)
- **测试脚本**: `test_gas_analysis_report.py`
- **页面概述**: 查看各取样位置的气体组分分析数据（甲烷、乙烷、氢气等），支持日期范围筛选、取样位置快速切换、新增/导出报告单。

### 2. 页面整体结构

| 区域 | 功能描述 | 备注 |
|:--- |:--- |:--- |
| **1. 搜索/筛选区 (顶部)** | 提供日期范围选择、查询、重置功能。包含新增与导出操作入口。 | 不含取样位置筛选，该功能独立为 Tab 栏。 |
| **2. 取样位置标签栏 (中部)** | 自定义 Tab 组件，非标准 `el-tabs`。用于快速筛选特定取样点的数据。 | **高风险区域**：定位依赖特定 CSS 类名或文本，单次切换后端需等待新数据加载。 |
| **3. 表格/列表区 (主体)** | 使用 `el-table` 组件展示数据。默认显示“基本信息” Tab。包含统计行。 | 列数较多(18+列)，包含大量带单位(%)字段。 |
| **4. 分页区** | 表格自带 `el-pagination` 组件，位于表格底部。 | 代码中未显式定义分页定位器，但测试脚本通过 `get_table_row_count` 验证分页行为。 |

### 3. 搜索/筛选区 元素清单

| 元素ID | 元素描述 | 控件类型 | 稳定性评级 | 定位器 (代码提取) | 备用定位器 | 备注 |
| :--- | :--- | :--- |:--- |:--- |:--- |:--- |
| `START_DATE_INPUT` | 开始日期输入框 | `el-input` (日期选择器) | **A级** | `(By.CSS_SELECTOR, 'input[placeholder*="开始日期"]')` | - | 使用 `placeholder` 属性，稳定。 |
| `END_DATE_INPUT` | 结束日期输入框 | `el-input` (日期选择器) | **A级** | `(By.CSS_SELECTOR, 'input[placeholder*="结束日期"]')` | - | 使用 `placeholder` 属性，稳定。 |
| `DATE_PICKER_TRIGGER` | 日期选择器触发图标 | `el-icon` | **B级** | `(By.CSS_SELECTOR, '.el-date-editor .el-icon-date, .el-date-editor .el-input__prefix .el-icon')` | `(By.XPATH, '//input[contains(@placeholder, "日期")]/preceding-sibling::*[contains(@class, "el-icon")]')` | 图标可能随 Element Plus 版本变化。 |
| `QUERY_BUTTON` | 查询按钮 | `el-button--primary` | **B级** | `(By.CSS_SELECTOR, '.search-form .el-button--primary:first-of-type, .el-form .el-button--primary')` | `(By.XPATH, '//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"查询")]/parent::button')` | 文本匹配作为保底。 |
| `RESET_BUTTON` | 重置按钮 | `el-button--default` | **B级** | `(By.CSS_SELECTOR, '.search-form .el-button--default, .el-form .el-button:not(.el-button--primary):first-of-type')` | `(By.XPATH, '//button[not(contains(@class,"el-button--primary"))]//span[contains(normalize-space(.),"重置")]/parent::button')` | 文本匹配作为保底。 |
| **`ADD_BUTTON`** | **新增报告单按钮** | `el-button--primary` (带 `el-icon-plus`图标) | **B级** | `(By.CSS_SELECTOR, '.toolbar .el-button--primary, button.el-button--primary:has(.el-icon-plus), .el-button--primary .el-icon-plus')` | `(By.XPATH, '//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"新增")]/parent::button')` | **权限控制点**: 可能对非授权用户隐藏。 |
| **`EXPORT_BUTTON`** | **导出按钮** | `el-button--default` (带 `el-icon-download`图标) | **B级** | `(By.CSS_SELECTOR, 'button.el-button--default .el-icon-download, .toolbar .el-button--default:last-of-type')` | `(By.XPATH, '//button[contains(@class,"el-button")]//span[contains(normalize-space(.),"导出")]/parent::button')` | **权限控制点**: 可能对非授权用户隐藏。 |

### 4. 取样位置标签栏 元素清单
- **控件说明**: 项目自定义组件，非标准 Element Plus Tab。
- **风险等级**: **高**。定位策略变通，切换后必须等待后端数据响应。

| 元素ID | 元素描述 | 控件类型 | 稳定性评级 | 定位器 (代码提取) | 等待策略 |
|:---|:---|:---|:---|:---|:---|
| `LOCATION_TAB` | 取样位置标签 (通用) | 自定义 Tab | **C级** | `(By.XPATH, '//*[contains(normalize-space(.),"{text}") and not(ancestor::table)][not(ancestor::nav) and not(ancestor::ul[contains(@class,"el-menu")])]')` | 点击后需 `wait_vue_stable()` 或显式等待表格数据刷新。 |
| `LOCATION_TAB_IN_BAR` | 取样位置标签 (精确定位) | 自定义 Tab | **B级** | `(By.XPATH, '//div[contains(@class,"tab") or contains(@class,"tag")]//*[contains(normalize-space(.),"{text}")]')` | 点击后需 `wait_vue_stable()` 或显式等待表格数据刷新。 |
| `LOCATION_TAB_ACTIVE` | 当前选中的高亮标签 | 自定义 Tab | **B级** | `(By.CSS_SELECTOR, '.el-tabs__item.is-active, [class*="tab"][class*="active"], [class*="tag"][class*="active"]')` | 用于获取状态，无需等待。 |

**已知取样位置列表 (共20个, 从代码方法 `get_all_location_names` 提取):**

| 界区原料气 | 除雾除尘出口原料气 | 脱油脱萘 | 低温水洗塔 | 甲烷化产品气 |
| :--- | :--- | :--- | :--- | :--- |
| **精脱硫1A** | **精脱硫1B** | **精脱硫2A** | **精脱硫2B** | **超精入口** |
| **超精出口** | **冷箱入口原料气** | **富氢** | **富氮** | **LNG冷箱** |
| **LNG储罐** | **LNG装车站** | **制冷剂** | **合成氨入塔气** | **合成氨出塔气** |
| **液氨** | **加样** | | | |

### 5. 表格/列表区 元素清单

| 元素ID | 元素描述 | 控件类型 | 稳定性评级 | 定位器 (代码推断) | 备注 |
|:---|:---|:---|:---|:---|:---|
| `INFO_TAB` | “基本信息” Tab 页签 | `el-tabs__item` | **A级** | `(By.XPATH, '//div[contains(@class,"el-tabs__item") and normalize-space(.)="基本信息"]')` | 文本匹配，稳定。 |
| `TABLE_HEADERS` | 表格列标题行 | `el-table` 表头 | **B级** | `(By.CSS_SELECTOR, '.el-table__header-wrapper th .cell')` | 获取列名。 |
| `TABLE_ROWS` | 表格数据行 | `el-table` 行 | **B级** | `(By.CSS_SELECTOR, '.el-table__body-wrapper tbody tr.el-table__row')` | 通用行选择器。 |
| `STATISTICS_ROW` | 表格统计汇总行 | `tfoot` / 自定义行 | **B级** | `(By.CSS_SELECTOR, 'tfoot tr, .el-table__footer-wrapper tr, tr.average-row, [class*="statistics"]')` | 可能不存在，需判断。 |
| `PAGINATION` | 底部分页器 | `el-pagination` | **B级** | `(By.CSS_SELECTOR, '.el-pagination')` | 代码未显式定义，此为推断选择器。 |
| `EMPTY_STATE` | 无数据时的空状态提示 | 表格组件 | **C级** | `(By.CSS_SELECTOR, '.el-table__empty-text, .el-empty__description p')` | 用于判断空数据场景。 |

**表格列清单 (共18列，与 `TABLE_COLUMNS` 常量一致):**

| 列标题 | 数据类型 | 示例值 | 备注 |
|:---|:---|:---|:---|
| 日期 | 日期 (YYYY-MM-DD) | 2025-06-01 |  |
| 取样时间 | 时间 (HH:mm) | 14:30 |  |
| 取样位置 | 文本 | 界区原料气 | 与标签栏对应。 |
| 班组 | 文本 | 甲班 |  |
| 检验员 | 文本 | 张三 |  |
| 复核员 | 文本 | 李四 |  |
| 备注 | 文本 | - | 可能为空。 |
| 甲烷(%) | 百分比数值 | 98.50 | 核心分析数据。 |
| 乙烷(%) | 百分比数值 | 0.55 |  |
| 乙烯(%) | 百分比数值 | 0.02 |  |
| 乙炔(%) | 百分比数值 | 0.01 |  |
| 丙烷(%) | 百分比数值 | 0.10 |  |
| 丙烯(%) | 百分比数值 | 0.00 |  |
| H2(%) | 百分比数值 | 0.05 |  |
| CO2(%) | 百分比数值 | 0.30 |  |
| O2(%) | 百分比数值 | 0.20 |  |
| N2(%) | 百分比数值 | 0.15 |  |
| CO(%) | 百分比数值 | 0.01 |  |

### 6. 弹窗/对话框

| 元素 | 推断描述 | 状态 | 待确认 |
|:---|:---|:---|:---|
| **新增报告单弹窗** | 点击“新增”按钮后弹出。预期包含表单字段（日期、位置、检验数据等）和“确认/取消”按钮。 | **推断存在** | **需DOM确认**。代码中定义了 `ADD_BUTTON` 定位器，但未定义弹窗内容及交互方法。 |
| **导出确认弹窗** | 点击“导出”按钮后或直接触发下载。 | **未知** | **需DOM确认**。`EXPORT_BUTTON` 行为待明确。 |

### 7. 页面状态与边界条件

| 状态类型 | 触发条件 | 预期表现 | 测试覆盖 (代码中所见) |
|:--- |:--- |:--- |:--- |
| **加载中** | 切换取样位置、执行数据查询后。 | 页面可能出现骨架屏或加载动画。 | 代码使用 `wait_page_ready()` 或 `wait_vue_stable()` 隐式等待。 |
| **空数据** | 搜索无结果 / 某取样位置无数据。 | 表格显示空状态组件（如“暂无数据”），`get_empty_text()` 应有返回值。 | 测试用例 `GAS-03` 通过 `get_table_row_count()` 和 `get_empty_text()` 验证。 |
| **错误状态** | 网络异常、后端错误。 | 可能提示“请求失败”或超时。 | 现有测试脚本未覆盖，**待补充异常场景**。 |
| **权限限制** | 用户无“新增”或“导出”权限。 | “新增”或“导出”按钮不显示，或点击后提示无权限。 | **需确认**。`ADD_BUTTON` & `EXPORT_BUTTON` 已标记为权限控制点。 |

### 8. 权限敏感点

| 权限点 | 受控元素 | 表现 | 注释 |
|:---|:---|:---|:---|
| `新增报告单` | `ADD_BUTTON` | 按钮可能隐藏或置灰。 | 代码定义为独立定位器。 |
| `导出数据` | `EXPORT_BUTTON` | 按钮可能隐藏或报错。 | 代码定义为独立定位器。 |