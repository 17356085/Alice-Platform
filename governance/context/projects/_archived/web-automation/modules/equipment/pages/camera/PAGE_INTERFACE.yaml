好的，作为**项目智能体 (Project Agent)**，我已收到 `PAGE_CONTEXT.md` 页面上下文。我将严格遵循 `skills: page-analysis` 的规范，基于页面上下文（AI推测版）为摄像头管理页面生成 `PAGE_ELEMENT_POSITION.md`。

本次输出将为每个关键元素设计A/B/C三级定位器，并明确WebDriverWait策略。由于是`source: ai`（推测版），所有定位器在真实页面生效后必须进行验证和调整。

---

### 文件: `PAGE_ELEMENT_POSITION.md`

```markdown
---
version: 1.0
source: ai
source_agent: page-analysis
created: 2026-06-18T11:41:00+08:00
module: equipment
page: camera
description: "摄像头管理页面元素定位器设计（AI推测版）"
---

# PAGE_ELEMENT_POSITION — 摄像头管理 (推测版)

> **定位器设计原则:**
> - **A级 (首选)**: 依赖 `data-testid`, 稳定的 `id`, 唯一的 `placeholder` 或 `aria-label`。
> - **B级 (备选)**: 依赖稳定的 CSS 类名组合。对于Element Plus组件，使用 `el-*` 类名 + 特定上下文。
> - **C级 (保底)**: 使用相对 XPath。谨慎使用 `text()`，避免因文案多语言化或微小变化导致失败。
> - **等待策略**: 基于元素状态和交互类型，选择合适的WebDriverWait条件。

## 1. 搜索/筛选区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
| :--- | :--- | :--- | :--- | :--- |
| `search-input` | **A级**: placeholder | `css: [placeholder="请输入摄像头名称或IP地址"]` | ★★★ | 如placeholder不唯一，使用B级 |
| | **B级**: CSS Class | `css: .el-form .el-input__inner[placeholder*="名称或IP"]` | ★★ | |
| | **C级**: XPath | `xpath: //label[contains(text(), '名称')]/following-sibling::div//input` | ★ | |
| `group-select` | **A级**: aria-label | `css: [aria-label="所属分组"]` | ★★★ | 依赖Element Plus渲染 `aria-label` |
| | **B级**: CSS Class | `css: .el-form .el-select .el-input__inner` | ★★ | 不精确，需结合上下文序号 |
| | **C级**: XPath | `xpath: (//label[contains(text(), '分组')]/following-sibling::div//input)[1]` | ★ | |
| `status-select` | **A级**: aria-label | `css: [aria-label="在线状态"]` | ★★★ | |
| | **B级**: CSS Class | `css: .el-form .el-select .el-input__inner` | ★★ | 不精确，需结合上下文序号 |
| | **C级**: XPath | `xpath: (//label[contains(text(), '状态')]/following-sibling::div//input)[1]` | ★ | |
| `search-btn` | **A级**: Button Text | `xpath: //button[contains(text(), '搜索')]` | ★★★ | 按钮文字通常稳定 |
| | **B级**: CSS Class | `css: button.el-button--primary:has-text("搜索")` | ★★ | `:has-text` 为playwright特性，纯selenium不可用 |
| | **C级**: CSS Class | `css: button.el-button--primary` | ★ | 此页可能唯一 |
| `reset-btn` | **A级**: Button Text | `xpath: //button[contains(text(), '重置')]` | ★★★ | |
| | **B级**: CSS Class + Text | `css: button.el-button--default:has-text("重置")` | ★★ | |
| | **C级**: XPath | `xpath: //button[contains(@class, 'el-button--default') and contains(text(), '重置')]` | ★ | |
| `add-camera-btn` | **A级**: Button Text | `xpath: //button[contains(text(), '添加摄像头')]` | ★★★ | **高权限点**，文案稳定 |
| | **B级**: CSS Class + Text | `css: button.el-button--primary:has-text("添加摄像头")` | ★★ | |
| | **C级**: XPath | `xpath: //div[contains(@class, 'header')]//button[contains(text(), '添加摄像头')]` | ★ | 通过区域限定 |

**等待策略:**
- 对于 `search-btn`, `reset-btn`, `add-camera-btn`：等待元素可点击 (`element_to_be_clickable`)。
- 对于输入框和下拉框：等待元素可见 (`visibility_of_element_located`)。

## 2. 表格/列表区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
| :--- | :--- | :--- | :--- | :--- |
| `data-table` | **A级**: data-testid | `css: [data-testid="camera-table"]` | ★★★ | 如添加该属性 |
| | **B级**: CSS Class | `css: .el-table` | ★★★ | 页面中唯一的表格 |
| | **C级**: XPath | `xpath: //div[contains(@class, 'main-content')]//table` | ★ | 需确保`main-content`类稳定 |
| `col-name` | **A级**: 列索引 + CSS | `css: .el-table__body-wrapper tbody tr td:nth-child(1) .cell` | ★★ | 基于列顺序，顺序变化会失效 |
| | **B级**: 列头文本 + CSS | `xpath: //th[contains(@class, 'el-table__cell') and .//div[text()='摄像头名称']]/following-sibling::td` | ★★ | 更稳定，不依赖列序号 |
| | **C级**: XPath | `xpath: (//div[@class='el-table__body-wrapper']//tr/td[1])[1]` | ★ | 绝对位置，高度不稳定 |
| `col-ip` | **A级**: 列索引 + CSS | `css: .el-table__body-wrapper tbody tr td:nth-child(2) .cell` | ★★ | |
| | **B级**: 列头文本 + CSS | `xpath: //th[.//div[text()='IP地址']]/following-sibling::td` | ★★ | |
| | **C级**: XPath | `xpath: (//div[@class='el-table__body-wrapper']//tr/td[2])[1]` | ★ | |
| `col-status` | **A级**: 列索引 + CSS | `css: .el-table__body-wrapper tbody tr td:nth-child(4) .el-tag` | ★★ | |
| | **B级**: 列头文本 + CSS | `xpath: //th[.//div[text()='状态']]/following-sibling::td//span[contains(@class, 'el-tag')]` | ★★ | |
| | **C级**: XPath | `xpath: (//div[@class='el-table__body-wrapper']//tr/td[4])[1]//span` | ★ | |
| `btn-edit` | **A级**: Button Text | `xpath: //button[contains(text(), '编辑')]` | ★★★ | 同一行内最稳定 |
| | **B级**: CSS Class + Text | `css: button.el-button--text:has-text("编辑")` | ★★ | 需结合行上下文 |
| | **C级**: XPath | `xpath: (//div[@class='el-table__body-wrapper']//tr/td[last()]//span[text()='编辑'])[1]` | ★ | |
| `btn-delete` | **A级**: Button Text | `xpath: //button[contains(text(), '删除')]` | ★★★ | |
| | **B级**: CSS Class + Text | `css: button.el-button--text:has-text("删除")` | ★★ | |
| | **C级**: XPath | `xpath: (//div[@class='el-table__body-wrapper']//tr/td[last()]//span[text()='删除'])[1]` | ★ | |

**等待策略:**
- 等待表格数据加载完成：等待 `data-table` 内的行元素存在 (`presence_of_element_located`)，并结合 `staleness_of` 等待加载动画消失（如果有v-loading）。
- 对于行内操作按钮 (`btn-edit`, `btn-delete`)：需先定位到特定行，再等待按钮可点击。

## 3. 弹窗/对话框

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
| :--- | :--- | :--- | :--- | :--- |
| `camera-dialog` | **A级**: data-testid | `css: [data-testid="camera-dialog"]` | ★★★ | 如添加该属性 |
| | **B级**: CSS Class | `css: .el-dialog` | ★★★ | 页面唯一弹窗 |
| | **C级**: XPath | `xpath: //div[contains(@class, 'el-dialog') and .//span[contains(text(), '摄像头')]]` | ★ | 通过标题文字定位 |
| `dialog-name-input` | **A级**: label + input | `css: .el-dialog .el-form-item:has(label:has-text("摄像头名称")) input` | ★★ | |
| | **B级**: placeholder | `css: .el-dialog [placeholder="请输入摄像头名称"]` | ★★ | |
| | **C级**: XPath | `xpath: //div[contains(@class, 'el-dialog')]//label[contains(text(), '名称')]/following-sibling::div//input` | ★ | |
| `dialog-ip-input` | **A级**: label + input | `css: .el-dialog .el-form-item:has(label:has-text("IP地址")) input` | ★★ | |
| | **B级**: placeholder | `css: .el-dialog [placeholder="请输入IP地址"]` | ★★ | |
| | **C级**: XPath | `xpath: //div[contains(@class, 'el-dialog')]//label[contains(text(), 'IP')]/following-sibling::div//input` | ★ | |
| `dialog-group-select` | **A级**: label + select | `css: .el-dialog .el-form-item:has(label:has-text("所属分组")) .el-select` | ★★ | |
| | **B级**: XPath | `xpath: //div[contains(@class, 'el-dialog')]//label[contains(text(), '分组')]/following-sibling::div//input` | ★ | |
| | **C级**: XPath | `xpath: (//div[contains(@class, 'el-dialog')]//div[contains(@class, 'el-select')])[1]` | ★ | |
| `dialog-save-btn` | **A级**: Button Text | `xpath: //div[contains(@class, 'el-dialog')]//button[contains(text(), '确定') or contains(text(), '保存')]` | ★★★ | |
| | **B级**: CSS Class + Text | `css: .el-dialog .el-button--primary:has-text("确定")` | ★★ | |
| | **C级**: XPath | `xpath: //div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--primary')]` | ★ | |
| `dialog-cancel-btn` | **A级**: Button Text | `xpath: //div[contains(@class, 'el-dialog')]//button[contains(text(), '取消')]` | ★★★ | |
| | **B级**: CSS Class + Text | `css: .el-dialog .el-button--default:has-text("取消")` | ★★ | |
| | **C级**: XPath | `xpath: //div[contains(@class, 'el-dialog__footer')]//button[contains(@class, 'el-button--default')]` | ★ | |

**等待策略:**
- 等待弹窗出现：等待 `camera-dialog` 元素可见 (`visibility_of_element_located`)，或者等待其 `style.display` 不为 `none`。
- 对于弹窗内输入框：等待元素可交互 (`element_to_be_clickable`) 后再输入。
- 对于弹窗按钮：等待元素可点击 (`element_to_be_clickable`)。

## 4. 页内其他元素

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
| :--- | :--- | :--- | :--- | :--- |
| `pagination` | **A级**: data-testid | `css: [data-testid="pagination"]` | ★★★ | |
| | **B级**: CSS Class | `css: .el-pagination` | ★★★ | 页面唯一 |
| | **C级**: XPath | `xpath: //div[contains(@class, 'el-pagination')]` | ★ | |
| `loading-mask` | **A级**: CSS Class | `css: .el-loading-mask` | ★★★ | 常用于等待表格数据加载完成 |
| `empty-state` | **A级**: data-testid | `css: [data-testid="empty-state"]` | ★★★ | |
| | **B级**: CSS Class | `css: .el-empty` | ★★★ | 符合Element Plus规范 |
| | **C级**: XPath | `xpath: //div[contains(@class, 'el-empty')]` | ★ | |

**等待策略:**
- 等待加载完成：使用 `invisibility_of_element_located` 等待 `loading-mask` 消失。
- 等待空数据状态：使用 `visibility_of_element_located` 等待 `empty-state` 出现。

---

## 重要说明

1.  **版本标记**: 本文件标记为 `source: ai`，表示所有定位器均为**AI推测版本**。在将其用于自动化脚本之前，必须在目标环境上进行严格验证。依赖于 `placeholder`、`aria-label`、`text()` 或特定CSS类名的定位器可能会因为前端代码的微小变动而失败。
2.  **真实环境验证**: 强烈建议在真实的页面上（或开发/测试环境中）使用浏览器开发者工具（Elements面板）检查上述定位器是否能正确定位到目标元素。
3.  **优先级选择**: 在编写Page Object时，应优先使用稳定性评级最高的定位器（A级）。如果A级定位器不存在或不稳定，再选择B级或C级定位器。
4.  **权限元素**: `add-camera-btn` 和行内 `btn-edit`、`btn-delete` 可能受权限控制。在自动化脚本中，需要预先判断这些元素是否存在或可见，以确定当前用户的权限状态。
5.  **动态内容**: 表格内容、弹窗、下拉框选项等都是动态渲染的。所有对应的定位策略（如 `col-name`, `dialog-name-input`, `dialog-group-select`）都依赖于这些动态内容正确加载。因此，在尝试与这些元素交互之前，必须使用恰当的WebDriverWait策略等待它们变得可用。
```