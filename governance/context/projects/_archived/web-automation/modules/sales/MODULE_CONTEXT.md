# MODULE_CONTEXT — sales

## 基本信息
- 模块ID：sales
- 模块名称：销仓管理（销售管理）
- 所属项目：web-automation
- 入口菜单：销售管理（一级菜单）
- 相关角色：admin、销售经理、销售员

## 模块定位
销售管理是鞍集涂源管理系统的业务核心模块，涵盖客户管理、合同管理、销售订单和销售日报表四大业务。代码成熟度高（4 PageObject + 20+ 测试脚本），自动化覆盖最全面。

## 核心业务规则
- 客户→合同→销售订单形成完整销售链路
- 合同金额关联销售订单，未执行额实时计算
- 销售日报表按日汇总产量/库存数据
- 客户等级（A/B/C）影响合同审批流程

## 模块边界
- 包含：客户管理、合同管理、销售订单、销售日报表

## 文档完整度 ✅ (2026-06-12 补齐)

| 页面 | RISK_MODEL | TEST_DESIGN | TEST_CASES | TECH_ANALYSIS | AUTO_STRATEGY |
|------|-----------|-------------|------------|---------------|---------------|
| customer | ✅ | ✅ | ✅ | ✅ | ✅ |
| contract | ✅ | ✅ | ✅ | ✅ | ✅ |
| sales-order | ✅ | ✅ | ✅ | ✅ | ✅ |
| daily-report | ✅ | ✅ | ✅ | ✅ | ✅ |

> 2026-06-12：4页面 × 5文档 = 20份全部补齐。基于已有代码反向提取 TECH_ANALYSIS + AUTO_STRATEGY，基于 PAGE_CONTEXT + 业务分析正向产出 RISK_MODEL + TEST_DESIGN + TEST_CASES。

### 文档统计
- 风险模型：13+11+11+11 = 46 条风险
- 测试场景：35+37+25+22 = 119 个场景
- 测试用例：35+37+25+22 = 119 条用例
- 自动化覆盖：P0 100% (14/14)，P1 ~65% (54/83)
- 不包含：生产报表（production）、储罐数据（tank）

## 关键页面
| 页面ID | 页面名称 | 路由 | 状态 | 代码 |
|--------|----------|------|------|------|
| customer | 客户管理 | #/sales/customer | ✅ | CustomerPage.py (44KB) |
| contract | 合同管理 | #/sales/contract | ✅ | ContractPage.py (40KB) |
| sales-order | 销售订单 | #/sales/order | ✅ | SalesOrderPage.py (31KB) |
| daily-report | 销售日报表 | #/sales/measurement | ✅ | DailyReportPage.py (41KB) |

## 风险概览
| 风险ID | 描述 | 等级 | 缓解措施 |
|--------|------|------|----------|
| RISK-SALES-001 | 合同金额计算错误导致财务数据偏差 | P0 | 参数化金额校验 + 交叉验证 |
| RISK-SALES-002 | 删除有合同的客户导致数据不一致 | P0 | 后端级联校验 |
| RISK-SALES-003 | 销售日报表与生产报表数据不一致 | P1 | 定时对账 |

## 依赖关系
- 上游：system-user（用户数据）、production（生产数据）
- 下游：无

## 自动化代码
- Page Objects：`page/sales_page/`（4 文件，~156KB）
- 测试脚本：`script/sales/`（20 文件，~250KB）
- conftest：`script/sales/conftest.py`（JS hash 导航 + fixture 工厂模式）

## 治理备注
- 本文件由 module-modeling Skill 在 2026-06-11 产出
- 旧 contexts/销仓管理/ 目录为空，此为首次建模
- 代码从 `sidebar_navigator.py` 路由 "销售管理" 确认


<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-18 10:54)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 20 (script/sales/test_*.py) |
| Page Object | 4 (page/sales_page/*.py) |
| 治理文档 | 29 .md 文件 |
| TECH_ANALYSIS | 4 |
| AUTO_STRATEGY | 4 |
| RISK_MODEL | 4 |
| PAGE_CONTEXT | 5 |
| SOP 状态 | completed |
| Phase 完成 | Automation, Bug Analysis, Data Sanitization, Execute & Debug, Knowledge, Project Init, Report, Requirement, Test Design |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->