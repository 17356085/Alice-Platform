# PAGE_CONTEXT — sales / sales-order

## 基本信息
- 页面ID：sales-order | 页面名称：销售订单 | 所属模块：销售管理（sales）
- 路由：`#/sales/order` | 自动化代码：`page/sales_page/SalesOrderPage.py` + `script/sales/test_sales_order*.py` (4个测试文件)

## 页面职责
销售订单的管理。支持订单创建、关联合同、净重记录。

## 核心元素（从代码推断）
- 搜索区：销售单号/客户名称输入 + 关联合同下拉 + 日期范围 + 搜索/重置
- 表格区（实际表头）：销售单号, 客户名称, 产品名称, 净重(吨), 车牌号, 创建时间, 关联合同, 操作 (8列)
- 操作按钮：新增 / 编辑 / 删除 / 查看详情
- 弹窗：新增/编辑表单 | 分页区：分页器

## 关键交互
- 新增订单→选客户→填净重→关联合同→确认→表格刷新
- 净重自动汇总到合同"未执行额"

## 权限与角色
- 可见：admin、销售经理、销售员 | 操作：admin+销售经理(CRUD)、销售员(新增)

## 自动化代码
- Page Object: `page/sales_page/SalesOrderPage.py` | 测试: `script/sales/test_sales_order*.py`
