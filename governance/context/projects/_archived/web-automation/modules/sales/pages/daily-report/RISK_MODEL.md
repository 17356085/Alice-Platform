# RISK_MODEL — sales / daily-report

## 页面/模块
- 名称：销售日报表 | 所属模块：sales（销仓管理）
- 路由：`#/sales/measurement`
- 自动化代码：`page/sales_page/DailyReportPage.py` (41KB) + `script/sales/test_daily_report*.py` (6个测试文件)
- 页面性质：**只读页面**，无增删改操作

## 风险清单

| 风险ID | 维度 | 风险描述 | 影响 | 等级 | 缓解措施 | 自动化覆盖 |
|--------|------|----------|------|------|----------|-----------|
| RISK-DLR-001 | 业务 | 日报表汇总指标与明细数据不一致（合计≠各行之和） | 高 | P0 | 后端事务一致性；前端汇总区与明细交叉验证 | ✅ test_daily_report_data_integrity |
| RISK-DLR-002 | 业务 | 销售日报表数据与生产报表数据不一致 | 中 | P1 | 定时对账任务；数据源统一 | ❌（跨模块） |
| RISK-DLR-003 | 数据 | 浮点数精度——汇总与明细差0.0001 | 中 | P1 | 后端decimal统一精度；前端round显示 | ✅ test_daily_report_data_integrity |
| RISK-DLR-004 | 数据 | 日期边界——查询无数据日期时汇总显示异常（NaN/负数） | 中 | P1 | 无数据日期汇总显示"0"或"—"，不显示NaN | ✅ test_daily_report_boundary |
| RISK-DLR-005 | 数据 | 日期范围跨度过大（>365天）导致查询超时或浏览器卡死 | 低 | P2 | 前端限制最大跨度；后端分批查询 | ❌ |
| RISK-DLR-006 | 接口 | 导出Excel时数据量过大导致超时或内存溢出 | 中 | P1 | 后端流式导出；前端显示导出进度 | ❌ |
| RISK-DLR-007 | 接口 | 接口返回异常格式（null/undefined）时前端崩溃 | 中 | P1 | 前端防御性编程：null → 0, undefined → "—" | 🔄 |
| RISK-DLR-008 | UI/UX | 汇总卡片数值过大时布局溢出 | 低 | P2 | CSS text-overflow: ellipsis + tooltip | — |
| RISK-DLR-009 | UI/UX | 明细表格多列在小屏下截断 | 低 | P2 | 自适应列宽 + 横向滚动 | — |
| RISK-DLR-010 | 性能 | 查询大日期范围时表格渲染慢（>1000行） | 中 | P1 | 后端分页；前端虚拟滚动 | ✅ test_daily_report_pagination |
| RISK-DLR-011 | 权限 | 非授权用户通过URL直接访问日报表数据 | 中 | P1 | 后端接口鉴权；前端路由守卫 | ✅ test_rbac |

## 高风险路径

- 日期查询 → 汇总指标计算 → 明细表格渲染 → 汇总与明细交叉验证（全链路）
- 数据一致性：当日总量 vs 当月累计 vs 明细求和

## 建议覆盖策略

- **必测（P0）**：汇总与明细一致性（RISK-DLR-001）、日期边界处理（RISK-DLR-004）
- **优先自动化**：数据完整性校验、分页、搜索（定位器B级占比高但因只读页面风险低）
- **手工保留**：导出Excel大数据量（RISK-DLR-006）、小屏适配（RISK-DLR-009）

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 2 | next_agent: test-design-agent -->
