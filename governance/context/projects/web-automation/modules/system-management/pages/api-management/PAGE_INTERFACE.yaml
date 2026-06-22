好的，作为 test-design-agent，我将基于您提供的 `PAGE_CONTEXT.md` 文件和 `system-management` 模块的 `api-management` 页面，生成专业的 `PAGE_ELEMENT_POSITION.md` 文件。

我将遵循 **A/B/C 三级定位器设计原则**，并针对 Vue 3 + Element Plus 技术栈进行优化，标注稳定的定位策略和预期的等待方式。

---

## PAGE_ELEMENT_POSITION.md

```markdown
# API管理页面元素定位器设计 (system-management/api-management)

> **版本**: 1.1
> **更新人**: test-design-agent
> **更新日期**: 2026-06-18
> **基于**: PAGE_CONTEXT.md (页面元素清单) + Element Plus 组件标准结构

## 设计原则

- **A级定位器 (首选)**: 使用 `data-testid`、`id`、`name`、`placeholder` 或唯一文本。
- **B级定位器 (备选)**: 使用基于类名或属性选择器的稳定 CSS Selector。避免依赖 Element Plus 的动态 class (如 `el-select--active`)。
- **C级定位器 (保底)**: 使用相对 XPath。利用 `contains()` 处理动态文本或 class，利用 `text()` 匹配按钮文字。禁止使用绝对 XPath。
- **通用等待策略**:
  - 所有 `el-select` 下拉框点击前: `element_to_be_clickable`
  - 所有 `el-dialog` 弹窗出现前: `visibility_of_element_located`
  - 所有 `el-table` 数据刷新后: `staleness_of` (旧表格行消失) 或 `visibility_of_element_located` (新数据行可见)
  - 所有 `el-button` 点击前: `element_to_be_clickable`

## 元素定位器表

### 1. 搜索/筛选区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 | 等待策略 |
|---|---|---|---|---|---|
| `search-apiName` | A (placeholder) | `[placeholder="请输入API名称"]` | A | C: `//input[@placeholder='请输入API名称']` | `visibility_of_element_located` (搜索区可见即可) |
| `search-status` | B (CSS Selector) | `.search-form .el-select:nth-child(2) .el-input__inner` | B | C: `//label[contains(text(),'状态')]/following-sibling::div//input` | `presence_of_element_located` |
| `search-requestMethod` | B (CSS Selector) | `.search-form .el-select:nth-child(3) .el-input__inner` | B | C: `//label[contains(text(),'请求方式')]/following-sibling::div//input` | `presence_of_element_located` |
| `search-submit` | A (text) | `button:has(span:text("搜索"))` | B (注意: `:has` 兼容性) | C: `//button[contains(@class,'el-button--primary') and contains(span, '搜索')]` | `element_to_be_clickable` |
| `search-reset` | A (text) | `button:has(span:text("重置"))` | B | C: `//button[contains(@class, 'el-button') and contains(span, '重置')]` | `element_to_be_clickable` |
| `search-form` | B (CSS Selector) | `.search-form` | A (如果存在唯一类) | A: `[data-testid="search-form"]` (如果存在) | `visibility_of_element_located` |

### 2. 表格/列表区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 | 等待策略 |
|---|---|---|---|---|---|
| `table` | B (CSS Selector) | `.el-table` | B | C: `//div[contains(@class, 'el-table')]` | `presence_of_element_located` |
| `table-header-cell-apiName` | C (XPath) | `//th[contains(@class, 'el-table__cell')][1]//div[@class='cell' and text()='API名称']` | C (列顺序敏感) | B: `.el-table__header-wrapper th:nth-child(1) .cell` | `visibility_of_element_located` (表头可见) |
| `table-cell-apiName` (第一行) | C (XPath) | `(//tr[contains(@class, 'el-table__row')])[1]/td[1]//div[@class='cell']` | C (行索引敏感) | B: `tr.el-table__row:nth-child(1) td:nth-child(1) .cell` | `visibility_of_element_located` (数据加载后) |
| `table-edit` (第一行) | A (text) | `tr.el-table__row:nth-child(1) button:has(span:text("编辑"))` | B | C: `(//tr[contains(@class,'el-table__row')])[1]//button[contains(span,'编辑')]` | `element_to_be_clickable` |
| `table-delete` (第一行) | A (text) | `tr.el-table__row:nth-child(1) button:has(span:text("删除"))` | B | C: `(//tr[contains(@class,'el-table__row')])[1]//button[contains(span,'删除')]` | `element_to_be_clickable` |
| `table-statusToggle` (第一行) | B (CSS Selector) | `tr.el-table__row:nth-child(1) .el-switch` | B | C: `(//tr[contains(@class,'el-table__row')])[1]//span[contains(@class,'el-switch')]` | `element_to_be_clickable` |
| `table-row` (动态) | C (XPath) | `//tr[contains(@class, 'el-table__row')][{row_index}]` | C (行索引敏感) | B: `tr.el-table__row:nth-child({row_index})` | `visibility_of_element_located` |
| `table-cell` (动态) | C (XPath) | `//tr[contains(@class, 'el-table__row')][{row_index}]/td[{col_index}]//div[@class='cell']` | C (行/列索引敏感) | B: `tr.el-table__row:nth-child({row_index}) td:nth-child({col_index}) .cell` | `visibility_of_element_located` |

### 3. 分页区

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 | 等待策略 |
|---|---|---|---|---|---|
| `pagination` | B (CSS Selector) | `.el-pagination` | A (唯一组件) | C: `//div[contains(@class,'el-pagination')]` | `visibility_of_element_located` |
| `pagination-total` | C (XPath) | `//div[contains(@class,'el-pagination')]//span[contains(@class,'el-pagination__total')]` | B | C: `//span[contains(text(),'条记录')]` | `visibility_of_element_located` |
| `pagination-size-select` | B (CSS Selector) | `.el-pagination .el-select .el-input__inner` | B | C: `//div[contains(@class,'el-pagination')]//input[contains(@placeholder,'条/页')]` | `element_to_be_clickable` |
| `pagination-btn-next` | B (CSS Selector) | `.el-pagination .btn-next` | B | C: `//div[contains(@class,'el-pagination')]//button[contains(@class,'btn-next')]` | `element_to_be_clickable` |

### 4. 弹窗/对话框

#### 4.1 新增/编辑弹窗

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 | 等待策略 |
|---|---|---|---|---|---|
| `dialog` (新增/编辑) | B (CSS Selector) | `.el-dialog` (在 `.el-overlay` 内) | B | C: `//div[contains(@class,'el-overlay')]//div[contains(@class,'el-dialog')]` | `visibility_of_element_located` |
| `dialog-title` | C (XPath) | `//div[contains(@class,'el-dialog__header')]//span[contains(@class,'el-dialog__title')]` | B | C: `//span[contains(@class,'el-dialog__title') and (text()='新增API' or text()='编辑API')]` | `visibility_of_element_located` |
| `dialog-apiName` | B (CSS Selector) | `.el-dialog .el-form-item:first-child .el-input__inner` | B | C: `//div[contains(@class,'el-dialog')]//label[text()='API名称']/following-sibling::div//input` | `presence_of_element_located` |
| `dialog-apiPath` | B (CSS Selector) | `.el-dialog .el-form-item:nth-child(2) .el-input__inner` | B | C: `//div[contains(@class,'el-dialog')]//label[text()='API路径']/following-sibling::div//input` | `presence_of_element_located` |
| `dialog-requestMethod` | B (CSS Selector) | `.el-dialog .el-form-item:nth-child(3) .el-select .el-input__inner` | B | C: `//div[contains(@class,'el-dialog')]//label[text()='请求方式']/following-sibling::div//input` | `element_to_be_clickable` |
| `dialog-status` | B (CSS Selector) | `.el-dialog .el-form-item:nth-child(4) .el-switch` | B | C: `//div[contains(@class,'el-dialog')]//label[text()='状态']/following-sibling::div//span[contains(@class,'el-switch')]` | `element_to_be_clickable` |
| `dialog-remark` | B (CSS Selector) | `.el-dialog .el-form-item:nth-child(5) .el-textarea__inner` | B | C: `//div[contains(@class,'el-dialog')]//label[text()='备注']/following-sibling::div//textarea` | `presence_of_element_located` |
| `dialog-submit` | A (text) | `.el-dialog button:has(span:text("确定"))` | B | C: `//div[contains(@class,'el-dialog')]//button[contains(span,'确定')]` | `element_to_be_clickable` |
| `dialog-cancel` | A (text) | `.el-dialog button:has(span:text("取消"))` | B | C: `//div[contains(@class,'el-dialog')]//button[contains(span,'取消')]` | `element_to_be_clickable` |

#### 4.2 确认删除弹窗 (`el-message-box`)

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 | 等待策略 |
|---|---|---|---|---|---|
| `confirm-dialog` | B (CSS Selector) | `.el-message-box` | A | C: `//div[contains(@class,'el-message-box')]` | `visibility_of_element_located` |
| `confirm-dialog-msg` | C (XPath) | `//div[contains(@class,'el-message-box')]//div[contains(@class,'el-message-box__message')]//p` | B | C: `//p[text()='确认删除该API吗？']` | `visibility_of_element_located` |
| `confirm-dialog-confirm` | A (text) | `.el-message-box button:has(span:text("确定"))` | B | C: `//div[contains(@class,'el-message-box')]//button[contains(span,'确定')]` | `element_to_be_clickable` |
| `confirm-dialog-cancel` | A (text) | `.el-message-box button:has(span:text("取消"))` | B | C: `//div[contains(@class,'el-message-box')]//button[contains(span,'取消')]` | `element_to_be_clickable` |

### 5. 页面状态

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 | 等待策略 |
|---|---|---|---|---|---|
| `loading-mask` (v-loading) | B (CSS Selector) | `.el-loading-mask` | A | C: `//div[contains(@class,'el-loading-mask')]` | `visibility_of_element_located` (加载中) / `invisibility_of_element_located` (加载完成) |
| `empty-state` | B (CSS Selector) | `.el-empty` | A | C: `//div[contains(@class,'el-empty')]` | `visibility_of_element_located` (无数据时) |
| `error-toast` | B (CSS Selector) | `.el-message--error` | A (如果存在) | C: `//div[contains(@class,'el-message') and contains(@class,'el-message--error')]` | `visibility_of_element_located` (出现后等待断言) |

## 注意事项

1.  **定位器维护**:
    - 若页面进行 UI 重构，优先检查 A 级定位器 (`data-testid` / `placeholder`) 是否受影响。
    - 若 Element Plus 组件升级，请重点验证 B 级 CSS Selector 是否仍然有效，特别是 `el-table`、`el-dialog` 的内部类名。

2.  **等待策略强化**:
    - 对于 `el-table` 的行内操作 (如 `编辑` / `删除` / `状态切换`)，建议执行操作后等待表格 `staleness_of` 或特定文本重新出现，以确认操作成功。
    - 对于 `el-message-box`，关闭后需等待其 `invisibility_of_element_located`，再进行后续页面操作，避免遮罩层干扰。

3.  **权限兼容**:
    - `table-edit`、`table-delete`、`table-statusToggle` 等受权限控制的元素，在自动化测试中需预先通过接口或登录用户权限绕开。如果元素因权限不存在，定位时应使用 `presence_of_element_located` 并显式处理 `NoSuchElementException`，而非直接断言失败。

4.  **数据驱动**:
    - 建议将 `{row_index}` 和 `{col_index}` 等动态参数作为方法参数传递，避免硬编码。
    - 建议封装寻找包含期望文本的行 (例如: `//tr[contains(@class,'el-table__row') and ./td[@class='el-table__cell']//div[text()='{expectedName}']]//button[contains(span,'编辑')]`)，以替代固定行索引。

## 更新历史
- **1.1 (2026-06-18)**: 基于 PAGE_CONTEXT.md v1.0 初版生成。
```

---

### 分析与说明

- **遵守 A/B/C 三级原则**: 对搜索框 (用 `placeholder`) 和按钮 (用文本) 优先使用了 A 级策略。对表单和弹窗尽量使用 B 级 CSS Selector (基于 `.el-form-item` 的顺序)。对表格中的特定单元格才使用 C 级 XPath，并注明了其 `行/列索引敏感` 的稳定性风险。
- **Element Plus 适配**: 定位器明确针对了 `el-table`, `el-dialog`, `el-message-box`, `el-switch`, `el-select`, `el-loading-mask`, `el-empty` 等组件。`el-table` 的行内操作定位器直接引用了组件标准类 `el-table__row`，并提供了备用方案。
- **Selenium 等待**: 对 `<el-select>` 点击、`<el-dialog>` 出现、`<el-table>` 刷新都标注了具体的 `WebDriverWait` 期望条件 (`element_to_be_clickable`, `visibility_of_element_located`, `staleness_of`)。
- **测试友好**: 在“注意事项”中提供了关于 **维护、等待策略强化、权限兼容、数据驱动** 的最佳实践建议，方便自动化工程师落地。