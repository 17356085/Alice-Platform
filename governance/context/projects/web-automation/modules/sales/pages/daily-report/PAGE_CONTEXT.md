# PAGE_CONTEXT — sales / daily-report

## 基本信息
- 页面ID：sales-daily-report | 页面名称：销售日报表 | 所属模块：销售管理（sales）
- 路由：`#/sales/measurement` | 自动化代码：`page/sales_page/DailyReportPage.py` + `script/sales/test_daily_report*.py` (6个测试文件)

## 页面职责
按日统计销售数据，展示产量/库存/销量等汇总指标和明细。

## 核心元素（从代码推断）
- 搜索区：日期选择器 + 产品下拉 + 搜索/重置 + 导出按钮
- 表格区：日期/产品/产量/库存/销量/操作等列
- 汇总区：当日总量/当月累计
- 分页区：分页器

## 关键交互
- 选择日期→查询→表格刷新 | 导出→Excel下载
- 数据汇总区实时计算

## 权限与角色
- 可见：admin、销售经理 | 操作：查看+导出

## 自动化代码
- Page Object: `page/sales_page/DailyReportPage.py` | 测试: `script/sales/test_daily_report*.py` (6文件)
