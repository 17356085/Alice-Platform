好的，我将基于模块 `personnel` 和页面 `my-exam` 进行分析。由于没有提供截图或HTML源码，我将根据常见的“人员管理”模块中“我的考试”页面的典型结构进行合理的模拟和推断，并产出完整的分析文档。

**分析假设：**
- 页面名称：我的考试 (My Exam)
- 页面功能：展示当前用户（如员工）已分配或需完成的考试/测评列表。
- 技术栈：Vue 3 + Element Plus。
- 页面结构：包含搜索区、表格、分页和查看/开始考试等操作。

---

### 产出物 1: PAGE_CONTEXT.md

```markdown
# PAGE_CONTEXT: 我的考试 (my-exam)

## 页面信息
- **页面名称**: 我的考试 (my-exam)
- **所属模块**: 人员管理 (personnel)
- **页面URL**: `/personnel/my-exam` (推测)
- **最后更新**: 2026-06-18

## 1. 页面整体结构
页面采用典型的上下布局：
- **顶部**: 页面标题“我的考试”。
- **主内容区**: 分为“搜索/筛选区”和“考试列表表格”。
- **操作按钮**: 表格上方右侧放置操作按钮。

## 2. 搜索/筛选区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| exam_name_input | 考试名称搜索框 | `el-input` | 搜索区 | 用于按考试名称模糊搜索 |
| exam_status_select | 考试状态筛选 | `el-select` | 搜索区 | 下拉选项：未开始/进行中/已完成 |
| search_btn | 搜索按钮 | `el-button` | 搜索区 | 触发搜索 |
| reset_btn | 重置按钮 | `el-button` | 搜索区 | 重置搜索条件 |

## 3. 表格/列表区

| 元素ID | 元素描述 | 列标题/控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| table_exam_list | 考试列表表格 | `el-table` | 主内容区 | 整个列表容器 |
| col_exam_name | 考试名称列 | 文本 | 表格区 | |
| col_exam_duration | 考试时长列 | 文本 | 表格区 | 格式: XX 分钟 |
| col_total_score | 总分列 | 数字 | 表格区 | |
| col_pass_score | 及格分列 | 数字 | 表格区 | |
| col_exam_status | 状态列 | `el-tag` | 表格区 | 未开始/进行中/已完成 |
| col_start_time | 开始时间列 | 日期/时间 | 表格区 | 格式: yyyy-MM-dd HH:mm |
| col_end_time | 结束时间列 | 日期/时间 | 表格区 | 格式: yyyy-MM-dd HH:mm |
| col_operation | 操作列 | `el-button` | 表格区 | 包含查看/开始考试按钮 |
| row_cell_action_start | 操作列“开始考试”按钮 | `el-button` (链接类型) | 表格区 | 状态为“未开始”时显示 |
| row_cell_action_view | 操作列“查看/查看成绩”按钮 | `el-button` (链接类型) | 表格区 | 状态为“进行中”或“已完成”时显示 |

## 4. 分页区

| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| pagination | 分页组件 | `el-pagination` | 表格底部 | 支持切换每页条数（10/20/50） |

## 5. 弹窗/对话框

| 元素ID | 元素描述 | 弹窗标题/字段/控件类型 | 所在区域 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| dialog_exam_detail | 考试详情弹窗 | `el-dialog` | 弹窗 | 标题: 考试详情 |
| dialog_exam_detail_title | 弹窗标题 | 文本 | 弹窗 | |
| dl_exam_name | 考试名称 | 文本 | 弹窗内字段 | |
| dl_exam_description | 考试说明 | 文本 | 弹窗内字段 | |
| close_detail_btn | 关闭按钮 | `el-button` | 弹窗 | |
| dialog_start_exam_confirm | 确认开始考试弹窗 | `el-dialog` | 弹窗 | 标题: 确认开始考试 |
| confirm_start_cancel_btn | 取消按钮 | `el-button` | 弹窗 | |
| confirm_start_submit_btn | 确定按钮 | `el-button` | 弹窗 | |

## 6. 页面状态

| 状态类型 | 表现 | 备注 |
| :--- | :--- | :--- |
| 加载中 | 表格区域显示骨架屏或旋转加载图标 | `el-skeleton` 或 `v-loading` |
| 空数据 | 表格区域显示“暂无数据”提示 | `el-empty` 组件 |
| 错误状态 | 页面顶部可能显示错误提示条 | 网络请求失败时 |

## 7. 权限点

| 权限ID | 描述 | 管控元素 | 备注 |
| :--- | :--- | :--- | :--- |
| perm_exam_start | 是否允许开始考试 | `row_cell_action_start` 按钮 | 状态为“未开始”且用户有权限时显示 |
| perm_exam_view_detail | 是否允许查看考试详情 | `dialog_exam_detail` 弹窗按钮 | |
```

### 产出物 2: PAGE_ELEMENT_POSITION.md

```markdown
# PAGE_ELEMENT_POSITION: 我的考试 (my-exam)

> **定位器设计依据**: 基于通用的 Element Plus 模式，`data-testid` 为假设属性，实际项目中可能不存在。
> **定位器版本**: 1.0

| 元素ID | 定位策略 | 定位值 | 稳定性评级 | 备用方案 |
| :--- | :--- | :--- | :--- | :--- |
| exam_name_input | A: `placeholder` | `(By.CSS_SELECTOR, "input[placeholder='考试名称']")` | A | B: `(By.CSS_SELECTOR, ".search-area .el-input__inner")` |
| exam_status_select | A: `data-testid` | `(By.CSS_SELECTOR, "[data-testid='exam-status-select'] .el-select__wrapper")` | A | B: `(By.CSS_SELECTOR, ".search-area .el-select")` |
| search_btn | A: `text` | `(By.XPATH, "//button[span[contains(text(), '搜索')]]")` | A | C: `(By.CSS_SELECTOR, ".search-area .el-button--primary")` |
| reset_btn | A: `text` | `(By.XPATH, "//button[span[contains(text(), '重置')]]")` | A | C: `(By.CSS_SELECTOR, ".search-area .el-button:not(.el-button--primary)")` |
| table_exam_list | B: `class` | `(By.CSS_SELECTOR, "div.el-table")` | B | C: `(By.XPATH, "//div[contains(@class, 'el-table')]")` |
| col_exam_status | B: `tag + class` (结合表头) | `(By.XPATH, "//div[contains(@class, 'el-table__body-wrapper')]//tr[1]//td[5]//span[@class='el-tag']")` | C | N/A (索引依赖) |
| row_cell_action_start | C: `text + XPATH` (含上下文) | `(By.XPATH, "//tr[1]//button[span[contains(text(), '开始考试')]]")` | C | 优先级低，需动态处理行索引 |
| pagination | B: `class` | `(By.CSS_SELECTOR, "div.el-pagination")` | B | C: `(By.XPATH, "//div[contains(@class, 'el-pagination')]")` |
| dialog_exam_detail | A: `data-testid` | `(By.CSS_SELECTOR, "[data-testid='dialog-exam-detail']")` | A | B: `(By.CSS_SELECTOR, "div.el-dialog[aria-label='考试详情']")` |
| confirm_start_submit_btn | A: `text` | `(By.XPATH, "//div[contains(@class, 'el-dialog')]//button[span[contains(text(), '确定')]]")` | A | C: `(By.CSS_SELECTOR, ".el-dialog__footer .el-button--primary")` |
```

### 产出物 3: PAGE_INTERFACE.yaml (后处理自动生成)

```yaml
# PAGE_INTERFACE.yaml for 'my-exam'
# Auto-generated from page-analysis
page:
  name: "my-exam"
  module: "personnel"
  url: "/personnel/my-exam"
  title: "我的考试"

elements:
  - id: "exam_name_input"
    locator:
      primary:
        strategy: "placeholder"
        value: "考试名称"
      backup:
        strategy: "css"
        value: ".search-area .el-input__inner"
    type: "input"
    wait: "visible"

  - id: "exam_status_select"
    locator:
      primary:
        strategy: "data-testid"
        value: "exam-status-select"
      backup:
        strategy: "css"
        value: ".search-area .el-select"
    type: "select"
    wait: "clickable"

  - id: "search_btn"
    locator:
      primary:
        strategy: "xpath"
        value: "//button[span[contains(text(), '搜索')]]"
      backup:
        strategy: "css"
        value: ".search-area .el-button--primary"
    type: "button"
    wait: "clickable"

  - id: "table_exam_list"
    locator:
      primary:
        strategy: "css"
        value: "div.el-table"
      backup:
        strategy: "xpath"
        value: "//div[contains(@class, 'el-table')]"
    type: "table"
    wait: "presence"

  - id: "dialog_exam_detail"
    locator:
      primary:
        strategy: "data-testid"
        value: "dialog-exam-detail"
      backup:
        strategy: "css"
        value: "div.el-dialog[aria-label='考试详情']"
    type: "dialog"
    wait: "visible"

  - id: "confirm_start_submit_btn"
    locator:
      primary:
        strategy: "xpath"
        value: "//div[contains(@class, 'el-dialog')]//button[span[contains(text(), '确定')]]"
      backup:
        strategy: "css"
        value: ".el-dialog__footer .el-button--primary"
    type: "button"
    wait: "clickable"

actionable_elements:
  - id: "row_cell_action_start"
    desc: "开始考试按钮（行内）"
    context: "表格行"
    locator:
      primary:
        strategy: "xpath"
        value: "//tr[1]//button[span[contains(text(), '开始考试')]]"
    type: "button"
    wait: "clickable"

  - id: "row_cell_action_view"
    desc: "查看详情按钮（行内）"
    context: "表格行"
    locator:
      primary:
        strategy: "xpath"
        value: "//tr[1]//button[span[contains(text(), '查看')]]"
    type: "button"
    wait: "clickable"
```

此分析基于常见 Web 应用模式推断。若要生成针对实际页面的精确分析，请提供该页面的**截图**或**HTML源码**。