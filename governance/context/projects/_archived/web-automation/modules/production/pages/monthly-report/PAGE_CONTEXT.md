```markdown
---
source: ai
source_agent: test-design-agent
created: 2026-06-16
---

# PAGE_ELEMENT_POSITION — production / monthly-report

## 定位器设计总则
1. **优先级策略**：A级（`data-testid` / 稳定的 `id` / 唯一的 `placeholder`） > B级（CSS Selector） > C级（XPath文本）。
2. **UI框架适配**：基于 Vue 3 + Element Plus，优先使用CSS选择器定位稳定组件（如 `month-nav`）。禁止使用绝对XPath (`/html/body/div[...]`)。
3. **动态内容处理**：对于文本可能变化的按钮或标签，使用 `contains()` 进行模糊匹配。

## 元素定位器表

### 月份选择区（自定义 month-nav 组件）

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| **current-month** | A - CSS Selector | `.current-month` | ★★★ A | `//span[contains(@class, "current-month")]` |
| **btn-prev-month** | A - CSS Selector | `.month-nav button.el-button.is-circle:first-child` | ★★☆ B | `(//*[contains(@class, "month-nav")]//button[contains(@class, "is-circle")])[1]` |
| **btn-next-month** | A - CSS Selector | `.month-nav button.el-button.is-circle:last-child` | ★★☆ B | `(//*[contains(@class, "month-nav")]//button[contains(@class, "is-circle")])[last()]` |

**定位器说明**：
- `current-month` 是自定义组件的核心文本展示元素，CSS类名稳定不变，评级最高。
- `btn-prev-month` 和 `btn-next-month` 的定位依赖于 `:first-child`/`:last-child`，若月份导航旁添加了其他按钮，此策略可能失效。备用方案通过限定在 `month-nav` 容器内查找所有 `is-circle` 按钮来增强稳健性，但索引本身仍存在风险，因此评级为B。

### 操作按钮（页面顶部）

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| **btn-generate** | B - XPath (文本) | `//button[contains(., "生成报表")]` | ★★☆ B | `//button[contains(@class, "el-button") and contains(., "生成报表")]` |
| **btn-trend** | B - XPath (文本) | `//button[contains(., "趋势")]` | ★★☆ B | `//button[contains(@class, "el-button") and contains(., "趋势")]` |
| **btn-export** | B - XPath (文本) | `//button[contains(., "导出")]` | ★★☆ B | `//button[contains(@class, "el-button") and contains(., "导出")]` |
| **btn-print** | B - XPath (文本) | `//button[contains(., "打印")]` | ★★☆ B | `//button[contains(@class, "el-button") and contains(., "打印")]` |

**定位器说明**：
- 四个按钮都使用文本定位，这是 Element Plus 按钮最通用的定位方式。虽然文本变更存在风险，但在版本迭代中相对稳定，评级为B。
- 备用方案增加了 `@class` 约束，将定位范围限定在 `el-button` 组件内，避免与其他元素（如 `span`、`a` 标签）的文本匹配。

### 统计卡片区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| **stat-cards** | A - CSS Selector | `.summary-card` | ★★★ A | `//div[contains(@class, "summary-card")]` |
| **stat-card-lng-value** | B - CSS Selector + XPath | `(By.CSS_SELECTOR, ".summary-card:nth-child(1) .value")` | ★★☆ B | `(//div[contains(@class, "summary-card")])[1]//div[contains(@class, "value")]` |

**定位器说明**：
- `stat-cards` 容器使用稳定的CSS类名，评级最高。
- `lng` 月产量值的定位采用 `:nth-child(1)` 索引，这在卡片顺序不变时有效。虽然文本依赖（如 `contains(., "LNG")`）比索引更易理解，但索引在页面结构稳定时也更可靠。备用方案使用XPath索引提供另一种选择。**建议**：如果顺序可能变化，应返回备用方案的文本匹配方式，但评级降为C。

### 数据展示区（分区卡片）

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| **section-table-rows** | A - CSS Selector | `.el-table__body-wrapper tbody tr.el-table__row` | ★★★ A | `//tr[contains(@class, "el-table__row")]` |
| **section-table-headers** | A - CSS Selector | `.el-table__header-wrapper th .cell` | ★★★ A | `//th//*[contains(@class, "cell")]` |

**定位器说明**：
- 所有分区卡片的表格结构一致，因此使用通用的表格行和表头定位器。
- `el-table__row` 和 `el-table__header-wrapper` 是 Element Plus 表格组件的标准类名，非常稳定，评级最高。

### 弹窗 / 对话框

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
|--------|----------|--------|-----------|----------|
| **dialog-by-title** | B - XPath (结构+文本) | `//div[contains(@class, "el-dialog") and .//span[contains(@class, "el-dialog__title") and contains(., "{title}")]]` | ★★☆ B | 使用 `_DIALOG_BY_TITLE_XPATH.format(title=title)` 动态构建 |

**定位器说明**：
- 使用了 `el-dialog` 和 `el-dialog__title` 两个标准 Element Plus 类名，并且通过 `{title}` 参数化，使其稳定且通用。评级为B。

## 权限相关元素
- **无**：当前页面为纯只读页面，无数据录入、编辑或删除操作，因此无需权限控制。

## 动态等待策略

| 场景 | 条件 | 等待策略 |
|------|------|----------|
| 月份切换后 | 当前月份文字变化 + 表格数据刷新 | `wait_vue_stable()` (`BasePage` 方法，等待Vue DOM更新) |
| 生成报表后 | 新数据加载完毕 | `wait_vue_stable()` + 检查表格行数是否大于0（可选） |
| 弹窗打开/关闭 | 弹窗出现/消失 | `wait_until_visible(dialog_by_title)` / `wait_until_invisible(dialog_by_title)` |

## 注意
- 所有元素尚未添加 `data-testid` 属性，目前定位策略为B级或C级。自动化执行期间如果定位失败，可优先建议开发添加 `data-testid` 以提升稳定性至A级。