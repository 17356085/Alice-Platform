# AUTO_STRATEGY — lab / gas-analysis-report

> 自动化策略 | 2026-06-11

## PageObject 拆分
- **单PO策略** ✅：GasAnalysisReportPage (27方法)，页面功能集中，无需拆分
- navigate_to_gas_analysis_report() — JS hash路由直达

## 覆盖矩阵
| 功能 | 方法 | 测试覆盖 | ROI |
|------|------|:--:|:--:|
| 导航 | navigate_to_gas_analysis_report | ✅ GAS-01 | 高 |
| 取样位置 | click_location_tab / get_active_location | ✅ GAS-06/07 | 高 |
| 日期筛选 | filter_by_date_range / click_query / click_reset | ✅ GAS-04/05 | 高 |
| 新增弹窗 | click_add / fill_report_form / save_report | ✅ GAS-08 | 高 |
| 表格数据 | get_table_headers / get_column_data_by_header | ✅ GAS-01/04 | 高 |
| 统计行 | get_statistics_data / get_average_value | ✅ GAS-09 | 中 |
| 导出 | click_export | ✅ GAS-10 | 中 |

## 合规状态
- 继承BasePage ✅
- CSS/相对XPATH，无绝对XPATH ✅
- wait_vue_stable/WebDriverWait，time.sleep 已治理（仅 TIMEOUT_CONFIG["micro_wait"] 轮询间隔） ✅ (2026-06-12 修复)
- navigate_to() 导航 ✅
- 无print()，使用logger ✅
- PageObject无assert ✅

## ROI评估
- 已有10条用例，100%自动化覆盖
- 核心功能全量覆盖（展示/筛选/切换/新增）
- 缺失：权限场景、异常场景（P1优先级，非阻塞）
