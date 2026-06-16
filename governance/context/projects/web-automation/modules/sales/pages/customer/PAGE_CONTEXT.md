# PAGE_CONTEXT — sales / customer

## 基本信息
- 页面ID：sales-customer | 页面名称：客户管理 | 所属模块：销售管理（sales）
- 路由：`#/sales/customer` | 自动化代码：`page/sales_page/CustomerPage.py` + `script/sales/test_customer.py` (43KB)

## 页面职责
客户的 CRUD 管理。支持客户编码、名称、联系人、等级维护。

## 核心元素（从代码推断）
- 搜索区：客户编码/名称输入 + 等级下拉 + 合作状态下拉 + 搜索/重置
- 表格区（实际表头）：客户编码, 客户名称, 联系人, 联系电话, 客户等级, 合作状态, 操作 (7列)
- 操作按钮：新增 / 行内编辑 / 删除 / 查看详情
- 弹窗：新增/编辑表单 + 客户详情
- 分页区：分页器

## 关键交互
- 搜索→异步刷新 | CRUD→弹窗→提交→表格刷新
- 客户等级变更影响合同审批流程

## 权限与角色
- 可见：admin、销售经理、销售员 | 操作：admin+销售经理(CRUD)、销售员(查看)

## 自动化代码
- Page Object: `page/sales_page/CustomerPage.py` | 测试: `script/sales/test_customer.py`
