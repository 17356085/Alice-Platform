好的，收到指令。作为自动化测试专家，我将对 **workflow** 模块下的 **approval-chain**（审批链）页面进行深入分析。

根据项目规范和最佳实践，我将遵循以下步骤：
1.  **页面结构分析**：从元素布局与功能区域出发。
2.  **元素清单构建**：形成 `PAGE_CONTEXT.md`。
3.  **定位器策略设计**：形成 `PAGE_ELEMENT_POSITION.md`。
4.  **自动化技术分析**：融入 `MODULE_CONTEXT.md` 中关于 `BasePage` 和 Element Plus 规范。
5.  **接口自动生成**：产出 `PAGE_INTERFACE.yaml`。

---

### **产出物 1: PAGE_CONTEXT.md**

---

# 页面上下文: approval-chain

-   **页面名称**: 审批链
-   **URL**: `{{基地址}}/workflow/approval-chain`
-   **所属模块**: workflow
-   **创建日期**: 2024-05-24
-   **分析版本**: v1.0

## 1. 页面整体结构

该页面是“工作流”模块下的审批配置功能。页面主要分为三个核心区域：

1.  **顶部搜索/筛选区**: 用于过滤审批流程。
2.  **主列表区**: 以表格形式展示已配置的审批链。
3.  **（推测）弹窗/对话框**: 用于新增、编辑或查看审批链的详细信息。

## 2. 搜索/筛选区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注与定位思路 |
| :--- | :--- | :--- | :--- | :--- |
| search-form.name | 流程名称输入框 | `el-input` | 搜索区 | 通过 `placeholder` 属性定位 |
| search-form.status | 流程状态筛选 | `el-select` | 搜索区 | 通过 `el-select` 组件的 `aria-label` 或关联的 `el-form-item` 标签定位 |
| search-form.date-range | 创建日期范围 | `el-date-picker` | 搜索区 | 通过 `type="daterange"` 属性或关联标签定位 |
| search-form.search-btn | 搜索按钮 | `el-button` | 搜索区 | 通过 `type="primary"` 和 `native-type="submit"` 组合定位 |
| search-form.reset-btn | 重置按钮 | `el-button` | 搜索区 | 通过 `plain` 属性或 `native-type="reset"` 定位 |

## 3. 表格区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注与定位思路 |
| :--- | :--- | :--- | :--- | :--- |
| table.header.name | 列头：流程名称 | `<th>` | 表格区 | 使用列索引或CSS选择器 |
| table.header.status | 列头：状态 | `<th>` | 表格区 | 同上 |
| table.header.creator | 列头：创建人 | `<th>` | 表格区 | 同上 |
| table.header.updated | 列头：更新时间 | `<th>` | 表格区 | 同上 |
| table.header.actions | 列头：操作 | `<th>` | 表格区 | 同上 |
| table.row.nth-cell | 第n行某一单元格 | `el-table-column` | 表格区 | 数据行定位通过行索引+列索引 |
| table.actions.edit | 操作列：编辑按钮 | `el-button` | 表格区 | 每行操作列的按钮，通过文本`text()`定位 |
| table.actions.delete | 操作列：删除按钮 | `el-button` | 表格区 | 每行操作列的按钮，通过文本`text()`定位 |
| table.actions.detail | 操作列：查看详情按钮 | `el-button` | 表格区 | 每行操作列的按钮，通过文本`text()`定位 |

## 4. 分页区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注与定位思路 |
| :--- | :--- | :--- | :--- | :--- |
| pagination | 分页组件 | `el-pagination` | 表格下方 | 使用 `class="el-pagination"` 定位 |
| pagination.total | 总条数显示 | `<span>` | 分页区 | 包含在 `el-pagination` 内部 |
| pagination.page-size | 每页条数选择器 | `el-select` | 分页区 | 包含在 `el-pagination` 内部 |
| pagination.pager | 页码按钮组 | `<button>` | 分页区 | 通过 `pager` 或具体数字定位 |
| pagination.next | 下一页按钮 | `<button>` | 分页区 | 通过 `aria-label="next"` 定位 |
| pagination.prev | 上一页按钮 | `<button>` | 分页区 | 通过 `aria-label="prev"` 定位 |

## 5. 弹窗/对话框

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注与定位思路 |
| :--- | :--- | :--- | :--- | :--- |
| dialog.create | 新增审批链弹窗 | `el-dialog` | 页面顶层 | 通过 `title` 属性或内容 `text()` 匹配 |
| dialog.create.form.name | 弹窗内流程名称输入框 | `el-input` | 弹窗 | 通过 `el-dialog` 内的 `placeholder` 或 `v-model` 属性定位 |
| dialog.create.form.approvers | 弹窗内审批人选择 | `el-select` | 弹窗 | 同上 |
| dialog.create.save-btn | 保存按钮 | `el-button` | 弹窗 | 通过 `dialog` 内的 `type="primary"` 定位 |
| dialog.create.cancel-btn | 取消按钮 | `el-button` | 弹窗 | 通过 `dialog` 内的 `plain` 或 `text()` 定位 |

## 6. 页面状态

-   **加载中**: 页面出现 `v-loading` 状态，`el-loading-mask` 元素可见。
-   **空数据**: 表格内显示 `el-empty` 组件，提示“暂无数据”。
-   **错误**: 全局或局部出现 `el-alert` 或 API 请求失败后的UI提示。
-   **无权限**: 部分按钮或操作无法点击，或整个页面提示“无权访问”。

## 7. 权限点

-   表格操作列中的**编辑**、**删除**按钮。
-   **新增**审批链的入口按钮（如果存在）。
-   **查看详情**按钮（通常对所有人可见）。

---

### **产出物 2: PAGE_ELEMENT_POSITION.md**

---

# 元素定位器设计: approval-chain

-   **页面名称**: 审批链
-   **技术栈**: Vue 3 + Element Plus
-   **遵循规范**: 优先 A 级，其次 B 级，最后 C 级。

## 元素定位器清单

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
| :--- | :--- | :--- | :--- | :--- |
| search-form.name | **A级 (CSS)** | `input[placeholder*="流程名称"]` **或** `[data-testid="name-input"]` | 高 | **B级**: `.search-form .el-input__inner` |
| search-form.status | **A级 (CSS)** | `[data-testid="status-select"]` | 高 | **B级**: `.el-select[aria-label="状态"]` |
| search-form.date-range | **A级 (CSS)** | `[data-testid="date-range"]` | 高 | **B级**: `.el-date-editor--daterange` |
| search-form.search-btn | **A级 (CSS)** | `button[type="submit"]` **或** `[data-testid="search-btn"]` | 高 | **B级**: `button:has-text("搜索")` |
| search-form.reset-btn | **A级 (CSS)** | `[data-testid="reset-btn"]` | 高 | **B级**: `button:has-text("重置")` |
| table.actions.edit | **A级 (B级)** | `text()` 文本匹配 | 中 | **C级 (XPath)**: `//button[contains(text(), '编辑')]` |
| table.actions.delete | **C级 (XPath)** | `//button[contains(text(), '删除')]` | 低 | 使用 `contains()` 处理动态class |
| table.actions.detail | **B级 (CSS)** | `.el-button--text:has-text("详情")` | 中 | **C级 (XPath)**: `//button[contains(@class, 'detail')]` |
| dialog.create | **A级 (CSS)** | `div.el-dialog[aria-label="新增审批链"]` | 高 | **B级**: `.el-dialog__wrapper.visible` |
| dialog.create.form.name | **B级 (CSS)** | `.el-dialog--visible input[placeholder*="审批链名称"]` | 中 | **C级**: `//div[contains(@class,'el-dialog')]//input` |
| pagination | **A级 (CSS)** | `ul.el-pagination` | 高 | **B级**: `.el-pagination` |

## 注意事项

1.  **EP-001 坑位 (Teleport 渲染)**: `el-select` 下拉选项和 `el-date-picker` 面板通过`Teleport`渲染到`<body>`下。
    -   **定位**: `body > .el-popper`
    -   **交互**: 使用 `wait_for_visible` 等待弹窗出现，避免使用 `is_displayed()`。
2.  **异步加载**: 表格数据通过API异步加载。使用 `wait_for_element` 等待表格行 `tr.el-table__row` 出现，或监听 `axios` 请求完成。
3.  **索引依赖**: 表格内的编辑/删除操作依赖于行索引，定位时需结合 `el-table__row` 的第n个实例或数据属性。
4.  **动态class**: `el-dialog__wrapper` 的 `visible` / `` 状态切换，定位时应优先使用 `aria-label` 或 `[style*="display: none"]`。

---

### **产出物 3: PAGE_INTERFACE.yaml**

---

```yaml
# PAGE_INTERFACE.yaml for approval-chain page
page:
  name: approval-chain
  module: workflow
  base_url: "{{base_url}}/workflow/approval-chain"
  description: "Workflow approval chain configuration page."

  elements:
    - id: search_name_input
      locator: "input[placeholder*='流程名称']"
      type: "el-input"
    - id: search_status_select
      locator: "data-testid=status-select"
      type: "el-select"
    - id: search_date_range_picker
      locator: ".el-date-editor--daterange"
      type: "el-date-picker"
    - id: search_button
      locator: "button[data-testid='search-btn']"
      type: "el-button"
    - id: table_first_row_edit_button
      locator: "xpath=//tr[1]//button[contains(text(),'编辑')]"
      type: "el-button"
    - id: create_dialog
      locator: "div.el-dialog[aria-label='新增审批链']"
      type: "el-dialog"
    - id: create_dialog_name_input
      locator: ".el-dialog input[placeholder*='审批链名称']"
      type: "el-input"
    - id: create_dialog_save_button
      locator: ".el-dialog button.el-button--primary"
      type: "el-button"

  operations:
    # 页面导航入口
    - name: navigate()
      description: "Navigate to the approval chain page."
      type: "navigation"
      element_id: null
    # 搜索操作
    - name: search(name, status, date_range)
      description: "Fill in the search form and click search."
      type: "complex"
      steps:
        - action: "type"
          element_id: "search_name_input"
          value: "name"
        - action: "select"
          element_id: "search_status_select"
          value: "status"
        - action: "click"
          element_id: "search_button"
      result_wait: "wait_for_table_load"
    # 表格操作
    - name: click_first_edit()
      description: "Click the 'Edit' button in the first row of the table."
      type: "click"
      element_id: "table_first_row_edit_button"
    # 弹窗操作
    - name: save_create_dialog()
      description: "Click the save button inside the create dialog."
      type: "click"
      element_id: "create_dialog_save_button"

  # 等待策略
  wait_strategies:
    - id: wait_for_table_load
      description: "Wait for the table to finish loading after a search action."
      type: "disappear" # 等待加载动画消失
      element_locator: ".el-loading-mask"

```