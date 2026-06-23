# PAGE_CONTEXT — system-management / sap-push-log

> 最后诊断：2026-06-12 | 诊断脚本 artifacts/diag_*.json

## 页面信息

| 属性 | 值 |
| --- | --- |
| 页面名称 | SAP推送日志 |
| 路由 | `#/system/workflow/sap-push-log` |
| 所属模块 | 系统管理 → 工作流管理 |
| 页面类型 | 日志列表页（含搜索筛选 + 分页 + 详情弹窗） |
| Page Object | [SapPushLogPage.py](ZJSN_Test-master526/page/system_page/SapPushLogPage.py) (~250行) |
| 测试脚本 | [test_sap_push_log.py](ZJSN_Test-master526/script/system/test_sap_push_log.py) (6 cases) |
| 测试结果 | 4P/0F/2S standalone; 3P/2F/1S full-regression |
| 自动化状态 | ⚠️ 基本完成，全量回归偶发 element click intercepted |

## 页面定位

SAP推送日志是**工作流与SAP系统集成**的日志记录页面，显示审批流程中SAP数据推送的历史记录。用于排查SAP接口调用异常。

## 页面关键功能

### 搜索区

| 控件 | 类型 | 定位方式 | 说明 |
| --- | :---: | --- | --- |
| 推送状态 | `<el-select>` 下拉 | el-select | 成功/失败 |
| 日期范围 | `<el-date-range-picker>` | BasePage 通用方法 | — |
| 搜索按钮 | `<el-button>` | BasePage `click_search_button()` | ⚠️ element click intercepted 风险 |
| 重置按钮 | `<el-button>` | BasePage `click_reset_button()` | ⚠️ element click intercepted 风险 |

### 表格列

| 列标题 | 数据类型 | 说明 |
| --- | --- | --- |
| 报表日期 | 日期 | — |
| 工厂代码 | 文本 | — |
| 推送状态 | el-tag | 成功/失败 |
| 推送时间 | 日期时间 | — |
| 错误信息 | 文本 | 失败时显示 |
| 操作 | 按钮 | 查看详情 |

### 详情弹窗

| 控件 | 类型 | 说明 |
| --- | :---: | --- |
| 推送详情 | 只读表单 | 显示SAP推送的完整信息 |
| 关闭按钮 | `<el-button>` | 关闭弹窗 |

## 关键定位策略

| 操作 | 方法 | 策略 |
| --- | --- | --- |
| 选择推送状态 | `select_status(value)` | el-select 下拉选择 |
| 点击搜索 | `click_search()` | 委托 BasePage（三级降级） |
| 点击重置 | `click_reset()` | 委托 BasePage（三级降级） |
| 查看详情 | `click_first_row_detail()` | 点击第一行查看按钮 |

## 已知坑位

1. **搜索/重置按钮被 overlay 拦截**：全量回归时频繁出现 `element click intercepted`，原因是页面存在常驻 overlay（可能为 loading 遮罩未消失），单独跑时正常
2. **分页通常只有一页**：测试环境中 SAP 推送日志数据量小
3. **操作按钮可能不可见**：部分行无详情按钮时跳过

## 与其他页面的关系

- 日志数据 → 来自 [审批链配置](approval-chain/PAGE_CONTEXT.md) 中配置的审批链触发SAP推送
- 关联页面 → [待我审批](approval-todo/PAGE_CONTEXT.md) 审批操作可能触发SAP推送
