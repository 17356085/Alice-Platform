# PAGE_CONTEXT — system-management / approval-todo

> 最后诊断：2026-06-12 | 诊断脚本 artifacts/diag_approval_*.json

## 页面信息

| 属性 | 值 |
| --- | --- |
| 页面名称 | 待我审批 |
| 路由 | `#/system/workflow/todo` |
| 所属模块 | 系统管理 → 工作流管理 |
| 页面类型 | 工作流列表页（含搜索筛选 + 表格 + 审批操作） |
| Page Object | [ApprovalTodoPage.py](ZJSN_Test-master526/page/system_page/ApprovalTodoPage.py) (~300行) |
| 测试脚本 | [test_approval_todo.py](ZJSN_Test-master526/script/system/test_approval_todo.py) (8 cases) |
| 测试结果 | 6P/0F/2S (2026-06-12 verified ✅) |
| 自动化状态 | ✅ 已完成 |

## 页面定位

待我审批是**工作流审批链**的入口页面之一，显示当前登录用户需要审批的申请列表。支持按工厂代码和报表日期筛选，支持审批操作（通过/驳回）和详情查看。

## 页面关键功能

### 搜索区

| 控件 | 类型 | 定位方式 | 说明 |
| --- | :---: | --- | --- |
| 工厂代码 | `<el-select>` 下拉 + `<input>` | JS label遍历 "工厂" → el-input__inner | ⚠️ 非"标题"字段！ |
| 报表日期 | `<el-date-range-picker>` | BasePage 通用方法 | 日期范围选择器 |
| 搜索按钮 | `<el-button>` | `_js_click_search_or_reset("搜索")` | JS 点击绕过拦截 |
| 重置按钮 | `<el-button>` | `_js_click_search_or_reset("重置")` | JS 点击绕过拦截 |

### 表格列

| 列标题 | 数据类型 | 说明 |
| --- | --- | --- |
| 报表日期 | 日期 | — |
| 工厂代码 | 文本 | — |
| 申请人 | 文本 | — |
| 审批状态 | el-tag | 待审批/已通过/已驳回 |
| 申请时间 | 日期时间 | — |
| 操作 | 按钮组 | 通过/驳回/查看详情 |

### 审批弹窗

| 控件 | 类型 | 说明 |
| --- | :---: | --- |
| 审批意见 | `<textarea>` | 必填，输入审批意见 |
| 确认按钮 | `<el-button primary>` | 提交审批 |
| 取消按钮 | `<el-button>` | 关闭弹窗 |

## 搜索表单实际 DOM 结构

> ⚠️ 关键发现：工作流页面的搜索字段是"工厂代码"而非"标题"（与CRUD页面不同）

```
搜索表单 (.el-form):
├── el-form-item: 报表日期
│   └── el-date-range-picker
├── el-form-item: 工厂代码
│   └── el-select > input.el-input__inner (placeholder="请选择")
├── button: 搜索
└── button: 重置
```

## 关键定位策略

| 操作 | 方法 | 策略 |
| --- | --- | --- |
| 输入工厂代码 | `input_factory(value)` | JS 遍历 `.el-form-item__label` 找"工厂" → 关联 input |
| 输入标题(兼容) | `input_title(value)` | 委托给 `input_factory()` + warning |
| 点击搜索 | `click_search()` | 委托 BasePage |
| 点击重置 | `click_reset()` | 委托 BasePage |
| 审批操作 | `click_approve(row)` / `click_reject(row)` | 行内按钮点击 |

## 已知坑位

1. **搜索字段不是"标题"**：与 CRUD 页面不同，工作流页面的文本搜索字段是"工厂代码"（`el-select` 下拉），而非 `<el-input>` 文本框
2. **空状态文案变体**：可能显示"暂无待审批项"而非"暂无数据"，断言用 `"暂无" in empty` 前缀匹配
3. **审批弹窗可能被拦截**：确认按钮可能被 overlay 拦截，需 JS 点击或重试

## 与其他页面的关系

- 审批操作 → 数据流转到 [我已审批](approval-history/PAGE_CONTEXT.md)
- 数据来源 → [我发起的](my-application/PAGE_CONTEXT.md) 提交的申请
- 审批链规则 → [审批链配置](approval-chain/PAGE_CONTEXT.md) 定义
