# PAGE_CONTEXT — system-management / approval-history

> 最后诊断：2026-06-12 | 诊断脚本 artifacts/diag_approval_*.json

## 页面信息

| 属性 | 值 |
| --- | --- |
| 页面名称 | 我已审批 |
| 路由 | `#/system/workflow/history` |
| 所属模块 | 系统管理 → 工作流管理 |
| 页面类型 | 工作流列表页（含搜索筛选 + 表格 + 详情查看） |
| Page Object | [ApprovalHistoryPage.py](ZJSN_Test-master526/page/system_page/ApprovalHistoryPage.py) (~250行) |
| 测试脚本 | [test_approval_history.py](ZJSN_Test-master526/script/system/test_approval_history.py) (7 cases) |
| 测试结果 | 6P/0F/1S (2026-06-12 verified ✅) |
| 自动化状态 | ✅ 已完成 |

## 页面定位

我已审批是**工作流审批链**的历史记录页面，显示当前登录用户已经处理过的审批记录。支持按审批状态、报表日期和工厂代码筛选。

## 页面关键功能

### 搜索区

| 控件 | 类型 | 定位方式 | 说明 |
| --- | :---: | --- | --- |
| 审批状态 | `<el-select>` 下拉 | el-select + label匹配 | 已通过/已驳回 |
| 报表日期 | `<el-date-range-picker>` | BasePage 通用方法 | 日期范围选择器 |
| 工厂代码 | `<el-select>` 下拉 + `<input>` | JS label遍历 "工厂" → el-input__inner | ⚠️ 非"标题"字段！ |
| 搜索按钮 | `<el-button>` | `_js_click_search_or_reset("搜索")` | JS 点击绕过拦截 |
| 重置按钮 | `<el-button>` | `_js_click_search_or_reset("重置")` | JS 点击绕过拦截 |

### 表格列

| 列标题 | 数据类型 | 说明 |
| --- | --- | --- |
| 报表日期 | 日期 | — |
| 工厂代码 | 文本 | — |
| 申请人 | 文本 | — |
| 审批状态 | el-tag | 已通过/已驳回 |
| 审批时间 | 日期时间 | — |
| 审批意见 | 文本 | — |
| 操作 | 按钮 | 查看详情 |

### 详情弹窗

| 控件 | 类型 | 说明 |
| --- | :---: | --- |
| 详情信息 | 只读表单 | 显示申请和审批的完整信息 |
| 关闭按钮 | `<el-button>` | 关闭弹窗 |

## 搜索表单实际 DOM 结构

> ⚠️ 与待我审批不同：多了"审批状态"筛选项

```
搜索表单 (.el-form):
├── el-form-item: 审批状态
│   └── el-select (选项: 已通过/已驳回)
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
| 输入工厂代码 | `input_factory(value)` | JS 遍历 `.el-form-item__label` 找"工厂" |
| 选择审批状态 | `select_status(value)` | el-select 下拉选择 |
| 输入标题(兼容) | `input_title(value)` | 委托给 `input_factory()` + warning |
| 查看详情 | `click_first_row_detail()` | 点击第一行查看按钮 |

## 已知坑位

1. **搜索字段不是"标题"**：与待我审批一样，文本搜索字段是"工厂代码"
2. **空状态文案变体**：可能显示"暂无已审批项"，断言用 `"暂无" in empty`
3. **审批状态选项有限**：只有"已通过"和"已驳回"，不含"审批中"

## 与其他页面的关系

- 数据来源 → [待我审批](approval-todo/PAGE_CONTEXT.md) 审批操作后
- 申请来源 → [我发起的](my-application/PAGE_CONTEXT.md)
