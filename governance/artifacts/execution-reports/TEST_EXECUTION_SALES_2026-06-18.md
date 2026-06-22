# Sales 模块测试执行报告

**日期**: 2026-06-18  
**模块**: sales  
**测试环境**: https://aiwechatminidemo.cimc-digital.com/  
**Browser**: Chrome (chromedriver, Selenium)

## 概览

| 指标 | 数值 |
|------|------|
| 总用例数 | 101 |
| 通过 | 45 (45%) |
| 失败 | 46 (46%) |
| Broken | 10 (10%) |
| 跳过 | 0 |

## 修复项 (本次会话)

| # | 问题 | 修复 | 影响 |
|---|------|------|------|
| 1 | allure-pytest 2.13.2 + pytest 8.3.5 不兼容 | 升级到 2.16.0 | 3 E2E ERROR→PASSED |
| 2 | SOP_STATUS phase 顺序异常 | 规范排序 | 消除 3 audit errors |
| 3 | daily_report_pagination TimeoutException | 6 项优化 (88s→44s) | 5 分页 PASSED |
| 4 | allure generate --clean 删 json/ | 安全脚本 | json/ 源目录保护 |

## 页面测试详情

### contract (合同管理)
- 文件: test_contract.py (CTR-001~011)
- 通过: display/search/pagination 场景
- 失败: add/edit/start/terminate/delete CRUD 操作 (46 失败，存量问题)
- 根因: 弹窗内表单字段定位或提交逻辑不匹配

### customer (客户管理)
- 文件: test_customer.py, test_customer_cdp.py, test_customer_cdp_fetch.py, test_customer_pagination.py
- 状态: 待跑（module 级 browser fixture 独立）

### daily-report (日报表)
- 文件: test_daily_report*.py (7 文件)
- 分页: 5/5 PASSED (DLY-040~044)
- 显示/搜索/边界/完整性: 待跑

### sales-order (销售订单)
- 文件: test_sales_order*.py (4 文件)
- 状态: 待跑

### E2E (跨页面)
- 文件: test_sales_e2e.py
- E2E-SALES-001: Customer→Contract→Order (P0) — PASSED
- E2E-SALES-002: Daily Report consistency (P1) — PASSED
- E2E-SALES-003: Contract search/filters (P1) — PASSED

## 已知问题

1. **Contract CRUD 全部失败** — 弹窗表单提交后页面未正确响应，需审查 ContractPage 的 add/edit/start/terminate 方法
2. **日报表 loading 遮罩持久存在** — Element Plus 遮罩层 `offsetHeight>0` 即使数据已加载，已在 DailyReportPage._wait_loading_gone 中增加兜底
3. **ContractPage.get_all_table_rows 方法缺失** — E2E-SALES-003 中 warning

## 报告文件

- Allure HTML: `allure-results/index.html`
- Markdown 摘要: `allure-results/md/sales/summary.md`
- JSON 数据: `allure-results/json/` (134 results for sales+dcs)
- 测试用例 Excel: `governance/kpi/reports/sales/测试报告-sales-{page}.xlsx` (待生成)
