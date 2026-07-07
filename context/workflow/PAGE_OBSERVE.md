# PAGE_CONTEXT: workflow/approval-todo

## 页面概述
审批待办列表页面，显示当前用户需要处理的审批任务。

---

## 可测元素

### 1. 搜索/筛选表单区域

| 元素名称 | 类型 | 交互方式 | CSS选择器 | XPath选择器 |
|---------|------|---------|----------|-------------|
| 申请单号输入框 | input | 输入文本 | `#applyNo` 或 `.search-form input[name='applyNo']` | `//input[@placeholder='请输入申请单号']` |
| 审批类型下拉框 | select | 点击选择 | `#approvalType` 或 `.ant-select[name='approvalType']` | `//select[@id='approvalType']` |
| 申请日期范围 | datepicker | 日期选择 | `.date-range-picker` | `//div[contains(@class,'date-range')]` |
| 搜索按钮 | button | 点击 | `.btn-search` 或 `button[type='submit']` | `//button[contains(text(),'搜索')]` |
| 重置按钮 | button | 点击 | `.btn-reset` | `//button[contains(text(),'重置')]` |

---

### 2. 数据表格区域

| 元素名称 | 类型 | 交互方式 | CSS选择器 | XPath选择器 |
|---------|------|---------|----------|-------------|
| 数据表格 | table | 读取数据 | `.ant-table` 或 `table.approval-table` | `//table[contains(@class,'approval')]` |
| 表格第一行 | tr | 点击行 | `.ant-table-row:first-child` | `//tbody/tr[1]` |
| 申请单号链接 | a | 点击跳转 | `.apply-no-link` | `//a[contains(@class,'apply-no')]` |
| 审批状态标签 | span | 读取文本 | `.status-tag` | `//span[contains(@class,'status')]` |
| 操作列-审批按钮 | button | 点击 | `.btn-approve` | `//button[contains(text(),'审批')]` |

---

### 3. 分页区域

| 元素名称 | 类型 | 交互方式 | CSS选择器 | XPath选择器 |
|---------|------|---------|----------|-------------|
| 分页容器 | div | 容器 | `.ant-pagination` | `//ul[contains(@class,'pagination')]` |
| 下一页按钮 | li | 点击 | `.ant-pagination-next` | `//li[contains(@class,'next')]` |
| 页码输入 | input | 输入跳转 | `.ant-pagination-options-quick-jumper input` | `//div[@class='quick-jumper']//input` |

---

### 4. 批量操作区域

| 元素名称 | 类型 | 交互方式 | CSS选择器 | XPath选择器 |
|---------|------|---------|----------|-------------|
| 全选复选框 | checkbox | 点击选中 | `.ant-checkbox-wrapper input[type='checkbox']` | `//thead//input[@type='checkbox']` |
| 批量审批按钮 | button | 点击 | `.btn-batch-approve` | `//button[contains(text(),'批量审批')]` |
| 批量退回按钮 | button | 点击 | `.btn-batch-reject` | `//button[contains(text(),'批量退回')]` |

---

## 页面状态

### 加载状态
- 表格加载中: `.ant-spin-spinning` 或 `.loading-mask`
- 空数据状态: `.ant-empty` 或 `.no-data`

### 交互弹窗
- 审批弹窗: `.ant-modal` 包含审批意见输入和确认/取消按钮
- 确认弹窗: `.confirm-dialog`

---

## 选择器优先级建议
1. 优先使用 `data-testid` 属性 (如存在)
2. 其次使用唯一 ID 选择器
3. 最后使用 class 组合或 XPath