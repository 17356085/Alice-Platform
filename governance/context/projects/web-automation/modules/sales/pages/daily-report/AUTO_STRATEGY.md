# AUTO_STRATEGY — sales / daily-report

> 基于 TECH_ANALYSIS + TEST_CASES + 现有代码 | 2026-06-12
> 只读页面，无弹窗CRUD。自动化重点：数据完整性校验

## 自动化目标
覆盖销售日报表的稳定功能：页面展示、汇总指标校验、日期搜索、明细表格、分页、数据完整性（汇总=明细求和）。

## 推荐策略
- 脚本层级：DailyReportPage（41KB PO）→ conftest.py → test_daily_report*.py（6文件，sales模块最多）
- 断言层级：页面级 + 数据级（汇总值/明细求和）+ 一致性级（当日≤当月）
- 数据策略：只读页面无需创建数据，依赖环境已有业务数据
- 清理策略：N/A（只读页面）
- 特殊处理：浮点数 round(x, 4) 统一精度后比较

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| TC-DLR-001 | 页面正常加载 | P0 | ✅ | 冒烟 |
| TC-DLR-002 | 汇总指标完整性 | P0 | ✅ | 核心验证 |
| TC-DLR-003 | 汇总与明细一致性 | P0 | ✅ | test_daily_report_data_integrity.py |
| TC-DLR-004~005 | 单日/日期范围查询 | P1 | ✅ | test_daily_report_search.py |
| TC-DLR-006 | 产品筛选 | P1 | 🔄 | Select popper 适配 |
| TC-DLR-007 | 重置搜索 | P1 | ✅ | |
| TC-DLR-008 | 无数据日期边界 | P1 | ✅ | test_daily_report_boundary.py |
| TC-DLR-009 | 表头完整性 | P1 | ✅ | test_daily_report_display.py |
| TC-DLR-010 | 空数据加载 | P1 | 🔄 | 需清空数据 |
| TC-DLR-012~013 | 数据完整性(2条) | P1 | ✅ | test_daily_report_data_integrity.py |
| TC-DLR-014 | 切换日期汇总刷新 | P1 | 🔄 | 待开发 |
| TC-DLR-015~016 | 分页 | P1 | ✅ | test_daily_report_pagination.py |
| TC-DLR-018 | 导出按钮可见 | P1 | ✅ | |
| TC-DLR-019~020 | 导出Excel | P2 | ❌ | 浏览器下载，Selenium难验证 |
| TC-DLR-021~022 | 异常格式/Token | P2 | ❌ | 手工/Mock |

## PageObject 拆分

```
DailyReportPage  ← 汇总指标区 + 搜索区 + 明细表格 + 分页（41KB，只读）
  ├── 搜索区：日期范围 + 产品下拉 + 查询/重置/导出
  ├── 汇总区：指标卡片（多选择器CSS fallback）
  ├── 表格区：明细数据（多列）
  └── 分页区

无弹窗子组件（只读页面）
```

## 公共组件复用

| 方法 | 来源 | 复用状态 |
|------|------|----------|
| navigate_to() | BasePage | ✅ |
| wait_loading_disappear() | BasePage | ✅ |
| get_table_data() | ElementPlusHelper | ✅ |
| get_pagination_info() | ElementPlusHelper | ✅ |
| get_summary_metrics() | DailyReportPage (自定义) | ✅ 但CSS fallback链长 |

## ROI 分析

| 指标 | 值 |
|------|----|
| 已投入开发时间 | ~4 小时（41KB PO + 6测试文件，覆盖最全） |
| 维护成本 | ~0.3 小时/月（只读页面，变更少） |
| 手工执行时间 | 10 分钟/次 |
| 年化 ROI | 10min × 52 − 4h − 0.3h×12 = 约 1 小时节省 |
| 当前状态 | P0/P1稳定，数据完整性校验是特色亮点 |

## 遗留技术债

1. **汇总卡片CSS fallback链过长**：非BEM命名导致定位器脆弱，建议推动前端加 `data-testid`
2. **time.sleep 硬等待**：`DailyReportPage.py` L22 有 `import time`，需替换为 WebDriverWait
3. **print() 调试输出**：`test_daily_report.py` 中多处 `print()` 需替换为 `logger.info()`

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 4 | next_agent: automation-agent -->
