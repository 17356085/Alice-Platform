# PAGE_CONTEXT — sales / contract

## 基本信息
- 页面ID：sales-contract | 页面名称：合同管理 | 所属模块：销售管理（sales）
- 路由：`#/sales/contract` | 自动化代码：`page/sales_page/ContractPage.py` + `script/sales/test_contract*.py` (6个测试文件)

## 页面职责
合同的完整生命周期管理。支持合同创建、关联客户、金额管理、状态流转。

## 核心元素（从代码推断）
- 搜索区：合同编号/名称输入 + 客户下拉 + 状态下拉 + 日期范围 + 搜索/重置
- 表格区（实际表头）：合同编号, 客户名称, 产品, 合同金额(万), 未执行额, 生效日期, 状态, 操作 (8列)
- 操作按钮：新增 / 编辑 / 删除 / 查看详情 / 审批
- 弹窗：新增/编辑表单（客户/产品/金额/日期/附件）
- 分页区：分页器

## 关键交互
- 新增合同→选客户→填金额→确认→表格刷新
- 状态流转：草稿→生效中→已完成（不可逆）
- 金额变更触发未执行额重新计算

## 权限与角色
- 可见：admin、销售经理 | 操作：admin+销售经理(CRUD)
- 特殊限制：已生效合同不可修改金额

## 自动化代码
- Page Object: `page/sales_page/ContractPage.py` | 测试: `script/sales/test_contract*.py` (6文件)
