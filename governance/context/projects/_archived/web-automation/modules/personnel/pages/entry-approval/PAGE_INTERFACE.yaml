好的，收到您的请求。根据 entry-approval 页面的代码、用例和上下文进行深层分析，我将生成严格对齐、结构完整的页面分析产物。

---

## 页面分析产物

我将首先提供更新后的 `PAGE_CONTEXT.md`，接着是三级定位器设计方案 `PAGE_ELEMENT_POSITION.md`，然后输出供 automation-agent 高效消费的 `PAGE_INTERFACE.yaml`，并提供执行策略与问题识别。

### 1. PAGE_CONTEXT.md

```markdown
# PAGE_CONTEXT — personnel / entry-approval

## 基本信息
- **页面ID**: entry-approval
- **页面名称**: 入场审批
- **所属模块**: 人员管理（personnel）→ 承包商管理
- **页面入口**: 左侧菜单 → 人员管理 → 承包商管理 → 入场审批
- **路由 / 标识**: `#/personnel/contractor/approval`
- **自动化代码**: `page/personnel_page/EntryApprovalPage.py` + `script/personnel/test_entry_approval.py`

## 页面职责
- 展示承包商人员的入场申请列表，支持按申请人/单位/审批状态搜索。
- 提供审批通过、审批驳回、查看详情操作。
- 审批流程核心节点，决定承包商人员是否可以进入作业区域。

## 核心元素

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 定位方式(参考) | 备注 |
|---|---|---|---|---|---|
| **搜索区** | | | | |
| search-name-input | 申请人/姓名输入框 | el-input | 搜索区 | XPath (模糊匹配 placeholder) | PO 代码中无 Reset 或 Search 按钮显式定位器，需分析 `click_search()` 方法内部实现 |
| search-unit-select | 承包商单位下拉选择器 | el-select | 搜索区 | XPath (关联上下文 + class) | 需通过下拉选项文本选择 |
| search-status-select | 审批状态下拉选择器 | el-select | 搜索区 | XPath (关联上下文 + class) | 选项: 待审批/已通过/已驳回 |
| search-btn | 搜索按钮 | el-button | 搜索区 | 暂缺 (需检测 `click_search`) | 触发异步搜索，建议在 BasePage 或 Page 类中定义并使用 `wait_clickable` |
| reset-btn | 重置按钮 | el-button | 搜索区 | 暂缺 (需检测 `click_reset`) | 重置搜索条件至默认，建议与搜索按钮并列声明定位器 |
| **表格区** | | | | |
| table | 入场审批数据表格 | el-table | 主内容区 | XPath (class) | 异步加载数据 |
| table-rows | 表格数据行 | el-table__row | 表格区 | PO 中直接用 `TABLE_ROW` 常量 | 需确认此行常量是否存在，代码中使用了 `TABLE_ROWS` 但文件未定义，可能继承自 BasePage 或未完成重构。若缺失，易导致 `NameError`，需补充。 |
| col-applicant | 申请人列 | text | 表格区 | CSS: nth-child(1) | 第1列 |
| col-unit | 承包商列 | text | 表格区 | CSS: nth-child(2) | 第2列 |
| col-id-card | 身份证号列 | text | 表格区 | CSS: nth-child(3) | PO代码列索引映射，原页面上下文缺失 |
| col-entry-date | 入场日期列 | text | 表格区 | CSS: nth-child(4) | 第4列 |
| col-work-type | 作业类型列 | text | 表格区 | CSS: nth-child(5) | 第5列 |
| col-status | 审批状态列 | el-tag | 表格区 | CSS: nth-child(6) | 使用标签显示: 待审批(橙)/已通过(绿)/已驳回(红) |
| col-desc | 入场说明列 | text | 表格区 | CSS: nth-child(7) | PO代码列索引映射，原上下文缺少此列 |
| col-actions | 操作列 | buttons | 表格区 | CSS: nth-child(7 或 8) | 动态显隐: 待审批显示(通过/驳回/详情)，已审批仅显示(详情) |
| **行内操作按钮** | | | | |
| btn-approve | 审批通过按钮 | el-button | 行内 (第1个或按文字) | XPath (text) | 点击后可能弹出确认或直接生效 |
| btn-reject | 审批驳回按钮 | el-button | 行内 (第2个或按文字) | XPath (text) | 弹出审批意见弹窗 |
| btn-detail | 详情按钮 | el-button | 行内 (第3个或按文字) | XPath (text) | 弹窗展示申请详情 |
| **弹窗区** | | | | |
| approval-dialog | 审批 / 驳回确认弹窗 | el-dialog | 弹窗 | 暂缺 | 包含审批意见输入框和确认取消按钮。Vue 条件渲染，需注意 `v-if` 导致元素不在 DOM 中。 |
| dialog-approve-title | 审批确认弹窗标题 (如“通过审批”) | el-dialog__title | 弹窗 | 暂缺 (按文字定位) | 用于区分通过/驳回弹窗，确认操作正确性。因弹窗内容可能不同，定位需结合实际文本。 |
| approval-comment-input | 审批意见/备注输入框 | el-textarea | 弹窗 | XPath (placeholder) | 驳回时必填，通过时可选 |
| dialog-confirm-btn | 弹窗确认按钮 | el-button | 弹窗 | 暂缺 (按文字) | 确认提交审批，Element Plus 通用 `el-button` 类型 |
| dialog-cancel-btn | 弹窗取消按钮 | el-button | 弹窗 | 暂缺 (按文字) | 取消审批操作，通用定位 |
| **权限 / 状态点**（需关注） | | | | |
| empty-state | 无数据/空状态提示 | text/icon | 表格区 | 待分析 | 表格无数据时显示 |
| disabled-approve-btn | 已审批状态下禁用的通过按钮 | el-button.is-disabled | 表格区 | 待分析 | 状态为已审批/已驳回时，相应按钮应禁用。 |
| loading-animation | 搜索或列表加载时的 Loading 动画 | el-loading | 全局 | 待分析 | 需等待动画消失后再进行后续操作。BasePage 中通常已有 `_wait_loading_gone` 方法。 |
| **弹窗元素扩展**（基于常规操作） | | | | |
| table-row-checkbox | 表格行前的选择复选框 | el-checkbox | 表格区 (待定) | 待分析 | 若支持多选审批，则需定义。当前用例未使用，暂定为待定。 |
```

---

### 2. PAGE_ELEMENT_POSITION.md

```markdown
# PAGE_ELEMENT_POSITION — personnel / entry-approval

> **设计原则**：  
> - **A级（推荐）**：`data-testid`、id、name、placeholder。这些是最稳定、与 UI 结构解耦的定位器，能最大限度避免因样式或结构变化导致的元素丢失。  
> - **B级（备用）**：稳定、唯一的 CSS 选择器。当 A 级不可用且页面结构固定，使用纯 class 组合或属性选择。  
> - **C级（兜底）**：相对 XPath（或基于文本的 XPath）。在动态页面中使用 XPath 作为最后手段，谨慎使用，避免对位置的绝对依赖。
>
> **策略说明**：
> - 当前 PO 代码中主要使用 XPath，建议逐步替换为更稳定的 A 级或 B 级定位器，以降低后续维护成本。
> - 对于动态区域（弹窗、下拉选项），定位器需在交互前后调用 `wait.until` 确保元素就绪。
> - 静态常量（如 TABLE_ROWS， TOTAL_COUNT）需明确在 PO 中定义，避免依赖未声明的常量导致运行时错误。

## 定位器清单

| 元素ID | A级定位 (最优) | B级定位 (备用) | C级定位 (兜底) | 策略说明 |
|---|---|---|---|---|
| **搜索区** | | | | |
| search-name-input | `[data-testid="search-name-input"]` | `(By.CSS_SELECTOR, 'input[placeholder*="姓名"]')` | `(By.XPATH, '//input[contains(@placeholder,"姓名") or contains(@placeholder,"申请人")])` | 建议优先在元素上添加 `data-testid`；B 级用于替代直接的 XPath；当添加 `data-testid` 或 `placeholder` 时，稳定性会更高。 |
| search-unit-select | `//div[contains(@class,"search-bar")]//div[contains(@class,"el-select")]//input[@placeholder="承包商单位"]` | `(By.CSS_SELECTOR, 'div.search-bar div.el-select input[placeholder*="承包商"]')` | `(By.XPATH, '//div[contains(@class,"search-bar")]//div[contains(@class,"el-select")][.//span[contains(.,"承包商")]]`)` | 涉及级联结构，B级CSS更需精确。A级仍未解决“搜索”逻辑，但可为输入框添加 `data-testid`。 |
| search-status-select | `[data-testid="search-status-select"]` | `(By.CSS_SELECTOR, 'div.search-bar div.el-select input[placeholder*="审批状态"]')` | `(By.XPATH, '//div[contains(@class,"search-bar")]//div[contains(@class,"el-select")][.//span[contains(.,"审批状态")]]`)` | 同上，建议统一添加 `data-testid`，增强可维护性。 |
| search-btn | `[data-testid="search-btn"]` | `(By.CSS_SELECTOR, 'button.search-btn')` | `(By.XPATH, '//button[.//span[text()="搜索"]]')` | 当前PO无显式定位器。建议添加 `data-testid` 或通过按钮文字定位，CSS基于属性设计。 |
| reset-btn | `[data-testid="reset-btn"]` | `(By.CSS_SELECTOR, 'button.reset-btn')` | `(By.XPATH, '//button[.//span[text()="重置"]]')` | 同搜索按钮。 |
| **表格区** | | | | |
| table | `[data-testid="data-table"]` | `(By.CSS_SELECTOR, 'div.el-table')` | `(By.XPATH, '//div[contains(@class,"el-table")]')` | 建议在表格容器上添加 `data-testid`。 |
| table-rows | `[data-testid="data-table"] tbody tr` | `(By.CSS_SELECTOR, 'div.el-table__body-wrapper tbody tr')` | `(By.XPATH, '//div[contains(@class,"el-table__body-wrapper")]//tr[contains(@class,"el-table__row")]')` | 代码中使用了 `TABLE_ROWS` 但未定义，请检查完整性。使用 CSS 选择器更稳定。 |
| col-applicant | `[data-testid="table-header"] th:nth-child(1)` | `(By.CSS_SELECTOR, 'div.el-table__header-wrapper th:nth-child(1) div.cell')` | 略（常用B级） | 用于获取表头文本，nth-child 方式相对稳定。 |
| col-actions | `[data-testid="table-body"] tr td:last-child` | `(By.CSS_SELECTOR, 'div.el-table__body-wrapper td:last-child')` | 略（常用B级） | 操作列通常在最后，但更建议通过表头文字定位。 |
| **行内操作按钮** | | | | |
| btn-approve | `[data-testid="approve-button"]` | `(By.CSS_SELECTOR, 'button.approve-btn')` | `(By.XPATH, './/button[.//span[contains(text(),"通过")]]')` | 建议添加 `data-testid`。当前XPath会匹配所有包含“通过”的按钮，需确保上下文唯一。 |
| btn-reject | `[data-testid="reject-button"]` | `(By.CSS_SELECTOR, 'button.reject-btn')` | `(By.XPATH, './/button[.//span[contains(text(),"驳回")]]')` | 同上。 |
| btn-detail | `[data-testid="detail-button"]` | `(By.CSS_SELECTOR, 'button.detail-btn')` | `(By.XPATH, './/button[.//span[contains(text(),"详情")]]')` | 同上。 |
| **弹窗区** | | | | |
| approval-dialog | `[data-testid="approval-dialog"]` | `(By.CSS_SELECTOR, 'div.el-dialog[aria-label*="审批"]')` | `(By.XPATH, '//div[contains(@class,"el-dialog")][.//span[contains(text(),"审批")]]')` | 建议在弹窗容器上添加 `data-testid`。 |
| approval-comment-input | `[data-testid="approval-comment"]` | `(By.CSS_SELECTOR, 'textarea.el-textarea__inner')` | `(By.XPATH, '//textarea[contains(@placeholder,"审批意见") or contains(@placeholder,"备注")]')` | 同其他输入框，建议添加 `data-testid`。B级选择器较宽松，需确认唯一性。 |
| dialog-confirm-btn | `[data-testid="dialog-confirm"]` | `(By.CSS_SELECTOR, 'div.el-dialog__footer button.el-button--primary')` | `(By.XPATH, '//div[contains(@class,"el-dialog")]//button[.//span[text()="确 定"]]')` | 文字包含空格（“确 定”），需用 `normalize-space()`。建议使用 `data-testid`。 |
| dialog-cancel-btn | `[data-testid="dialog-cancel"]` | `(By.CSS_SELECTOR, 'div.el-dialog__footer button:not(.el-button--primary)')` | `(By.XPATH, '//div[contains(@class,"el-dialog")]//button[.//span[text()="取 消"]]')` | 同上。 |

**备注**：本表格中的 `data-testid` 为推荐添加的新属性，可极大提升稳定性。如无法修改前端代码，请优先使用 B 级 CSS 选择器。当 CSS 无法唯一定位时，使用 C 级 XPath 作为最终保底，并结合 `wait.until` 确保元素可交互。
```

---

### 3. PAGE_INTERFACE.yaml (自动生成)

```yaml
# Auto-generated from page-analysis
page_id: entry-approval
module_id: personnel
page_name: 入场审批
url_fragment: "#/personnel/contractor/approval"
entry_path: ["人员管理", "承包商管理", "入场审批"]
criticality: high
elements:
  - element_id: search-name-input
    locator:
      by: xpath
      value: '//input[contains(@placeholder,"姓名") or contains(@placeholder,"申请人")]'
    interaction_type: send_keys
    description: 申请人姓名的搜索输入框
  - element_id: search-unit-select
    locator:
      by: xpath
      value: '//div[contains(@class,"el-form")]//div[contains(@class,"el-select")][.//span[contains(.,"承包商")]]'
    interaction_type: select_option
    description: 选择承包商单位的下拉框
  - element_id: search-status-select
    locator:
      by: xpath
      value: '//div[contains(@class,"el-form")]//div[contains(@class,"el-select")][.//span[contains(.,"审批状态")]]'
    interaction_type: select_option
    description: 选择审批状态的下拉框
  - element_id: search-btn
    locator:
      by: xpath
      value: '//button[.//span[text()="搜索"]]'
    interaction_type: click
    description: 触发搜索的按钮
  - element_id: reset-btn
    locator:
      by: xpath
      value: '//button[.//span[text()="重置"]]'
    interaction_type: click
    description: 重置搜索条件的按钮
  - element_id: table-rows
    locator:
      by: xpath
      value: '//div[contains(@class,"el-table__body-wrapper")]//tr[contains(@class,"el-table__row")]'
    interaction_type: retrieve
    description: 表格中的所有数据行
  - element_id: col-actions
    locator: null  # 暂时无显式定义，建议通过表头文本“操作”定位
    interaction_type: click
    description: 表格中的操作列，可能需要进一步拆分为具体按钮
  - element_id: approval-dialog
    locator:
      by: css
      value: "div.el-dialog"
    interaction_type: click
    description: 审批弹窗容器，用于确认弹窗的出现
  - element_id: approval-comment-input
    locator:
      by: xpath
      value: '//textarea[contains(@placeholder,"审批意见")]'
    interaction_type: send_keys
    description: 审批弹窗内的意见输入框
  - element_id: dialog-confirm-btn
    locator:
      by: css
      value: "div.el-dialog__footer button.el-button--primary"
    interaction_type: click
    description: 审批弹窗内的提交按钮
  - element_id: dialog-cancel-btn
    locator:
      by: css
      value: "div.el-dialog__footer button:not(.el-button--primary)"
    interaction_type: click
    description: 审批弹窗内的取消按钮
```

---

### 4. 执行策略与识别问题

**关键问题识别**：

1.  **常量未定义导致的运行错误**：PO 代码中使用了 `self.TABLE_ROWS` 和 `self.TOTAL_COUNT`，但未在类中定义，也未从 BasePage 继承。这会导致运行时 `NameError`。**建议**：在 `EntryApprovalPage` 类中添加对应的 CSS 或 XPath 定位器，例如 `TABLE_ROWS = (By.CSS_SELECTOR, 'div.el-table__body-wrapper tbody tr.el-table__row')`。

2.  **搜索/重置按钮定位器缺失**：`click_search()` 和 `click_reset()` 方法无相应定位器，无法执行交互。**建议**：立即在 PO 中添加 `SEARCH_BUTTON` 和 `RESET_BUTTON` 定位器（建议使用 B 级 CSS 选择器，或为按钮添加 `data-testid`）。

3.  **动态弹窗处理策略**：Vue 动态渲染弹窗（`v-if`/`v-show`）可能导致元素不在 DOM 中。需统一使用 `wait.until(EC.visibility_of_element_located(...))` 确保弹窗加载完成。

4.  **状态依赖的操作限制**：当数据状态的审批状态为“已通过”或“已驳回”时，“通过”和“驳回”按钮将消失（或禁用）。如果用例中状态混合存在（如列表中同时包含待审批和已通过），则基于 XPath 的 `TABLE_APPROVE_BUTTON` 将只匹配到待审批行的按钮，但预期是找第几行？需设计带索引的逻辑（如基于行内 `col-status` 的动态筛选）。

5.  **代码完整性检查**：
    -   `get_table_row_count()` 使用 `self.find_all(self.TABLE_ROWS)`，但缺少 `TABLE_ROWS` 定义。
    -   `get_total_count_text()` 使用 `self.TOTAL_COUNT`，但未定义。
    -   `is_next_page_enabled()` 使用 `self.find_next_page_element()`，但未定义。
    -   `click_search()` 和 `click_reset()` 无定位器。

**下一步行动建议**：
-   立即修复 PO 中缺失的常量和方法实现。
-   为新增的定位器（搜索/重置按钮）提供明确的 A/B/C 三级建议。
-   在测试脚本中，对审批操作（通过/驳回）添加数据行索引参数，确保操作的精确性。