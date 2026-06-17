# MODULE_CONTEXT — lab

> 版本: 2.0 | 2026-06-12 | Phase 1-4 全闭环

## 基本信息
- 模块ID：lab
- 模块名称：化验室取样
- 所属项目：web-automation
- 菜单路径：化验室取样 → 气体分析(3页) / 水质分析(3页)

## 页面清单（6页全覆盖）

### 气体分析 (gas) — 3页

| 页面 | 路由 | PAGE_CONTEXT | POSITION | RISK | TEST_DESIGN | TEST_CASES | TECH | AUTO_STRATEGY | PageObject | Test |
|------|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 气体分析报告单 | #/lab/gas/report | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ GasAnalysisReportPage | ✅ |
| 气体分析对比 | #/lab/gas/compare | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ LabComparePage | ✅ |
| 气体分析设计指标 | #/lab/gas/indicator | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ LabIndicatorPage | ✅ |

### 水质分析 (water) — 3页

| 页面 | 路由 | PAGE_CONTEXT | POSITION | RISK | TEST_DESIGN | TEST_CASES | TECH | AUTO_STRATEGY | PageObject | Test |
|------|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 水质分析报告单 | #/lab/water/report | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ WaterAnalysisReportPage | ✅ |
| 水质分析对比 | #/lab/water/compare | ✅ | — | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ✅ LabComparePage | ✅ |
| 水质分析设计指标 | #/lab/water/indicator | ✅ | — | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ✅ LabIndicatorPage | ✅ |

## 代码资产

| 类型 | 文件 | 说明 |
|------|------|------|
| PageObject | GasAnalysisReportPage.py | 气体报告单(27方法，已有) |
| PageObject | WaterAnalysisReportPage.py | 水质报告单(新) |
| PageObject | LabComparePage.py | 气体+水质对比(参数化，新) |
| PageObject | LabIndicatorPage.py | 气体+水质设计指标(参数化，新) |
| 测试 | test_gas_analysis_report.py | 10用例(已有) |
| 测试 | test_water_report.py | 水质报告单(新, 1 case) |
| 测试 | test_gas_compare.py + test_water_compare.py | 对比页(新, 各2 cases) |
| 测试 | test_gas_indicator.py + test_water_indicator.py | 设计指标(新, 各2 cases) |
| conftest | conftest.py | 7个page fixtures |

## 治理文档
| 文档 | 位置 | 说明 |
|------|------|------|
| RISK_MODEL | `RISK_MODEL.md` | 模块级，11条风险 |
| TEST_DESIGN | `TEST_DESIGN.md` | 模块级，19条用例 |
| TEST_CASES | `TEST_CASES.md` | 模块级，100%自动化 |
| TECH_ANALYSIS | `TECH_ANALYSIS.md` | 模块级，组件识别+定位器 |
| AUTO_STRATEGY | `AUTO_STRATEGY.md` | 模块级，统一PO设计 |
| TEST_SUMMARY | `../../artifacts/test-summaries/TEST_SUMMARY_lab_2026-06-12.md` | Phase 8 |

## 合规状态
- 所有 PageObject 继承 BasePage ✅
- 无绝对XPath ✅
- 无 time.sleep 硬等待 ✅
- check_code_quality: 新文件全部 PASS ✅


<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-17 16:53)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 9 (script/lab/test_*.py) |
| Page Object | 9 (page/lab_page/*.py) |
| 治理文档 | 40 .md 文件 |
| TECH_ANALYSIS | 5 |
| AUTO_STRATEGY | 5 |
| RISK_MODEL | 5 |
| PAGE_CONTEXT | 7 |
| SOP 状态 | completed |
| Phase 完成 | Automation, Bug Analysis, Data Sanitization, Execute & Debug, Knowledge, Project Init, Report, Requirement, Test Design |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->