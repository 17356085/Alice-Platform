# MODULE_CONTEXT — production

## 基本信息
- 模块ID：production
- 模块名称：生产管理
- 所属项目：web-automation
- 更新日期：2026-06-12
- 导航路径：生产管理（一级菜单，含 5 个子页面）

## 模块定位
生产管理模块覆盖生产线日报/月报、交接班、班次班组配置与业务类型配置等生产业务场景。包含报表类和 CRUD 类两种页面类型。

## 子页面状态

| 路由 key | 页面名称 | hash 路由 | 类型 | 状态 | 测试结果 |
|----------|---------|-----------|------|------|----------|
| test_daily_report | 日报表管理 | `#/production/daily-report` | 报表（4分区+4弹窗） | 🟢 完成 | 8/0/2 |
| test_monthly_report | 生产月报表 | `#/production/monthly-report` | 报表（4分区+弹窗） | 🟢 完成 | 8/0/1 |
| test_shift_team_config | 班次班组配置 | `#/production/shift-team-config` | CRUD（6字段） | 🟢 完成 | 5/0/0 |
| test_business_type_config | 业务类型配置 | `#/production/business-type-config` | CRUD（17字段） | 🟢 完成 | 8/0/0 |
| test_shift_report | 交接班日报表 | `#/production/shift-report` | 未知 | ⏭️ 阻塞 | — |

## 资产清单

| 资产类型 | 文件 | 规模 |
|---------|------|------|
| Page Object | `page/production_page/DailyReportPage.py` | 41 方法 |
| Page Object | `page/production_page/MonthlyReportPage.py` | 28 方法 |
| Page Object | `page/production_page/ShiftTeamConfigPage.py` | 23 方法 |
| Page Object | `page/production_page/BusinessTypeConfigPage.py` | 26 方法 |
| 测试脚本 | `script/production/test_daily_report.py` | 10 用例 |
| 测试脚本 | `script/production/test_monthly_report.py` | 9 用例 |
| 测试脚本 | `script/production/test_shift_team_config.py` | 5 用例 |
| 测试脚本 | `script/production/test_business_type_config.py` | 8 用例 |
| Fixtures | `script/production/conftest.py` | driver_setup + 4 page fixtures |

## 治理文档覆盖

| 子页面 | PAGE_CONTEXT | RISK_MODEL | TEST_DESIGN | TEST_CASES | TECH_ANALYSIS | AUTO_STRATEGY | PAGE_ELEMENT_POSITION |
|--------|:-----------:|:----------:|:-----------:|:----------:|:------------:|:------------:|:---------------------:|
| daily-report | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| monthly-report | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| shift-team-config | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| business-type-config | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| shift-report | ⏭️ | ⏭️ | ⏭️ | ⏭️ | ⏭️ | ⏭️ | ⏭️ |

## 测试结果（2026-06-12）

```
模块总计: 29 passed / 0 failed / 3 skipped

daily-report:       8/0/2  (export_dialog不稳定 + enter_data需清理策略)
monthly-report:     8/0/1  (export_dialog共用问题)
shift-team-config:  5/0/0  ✅ 零缺陷
business-type-config: 8/0/0 ✅ 零缺陷
shift-report:       —      (前端未实现)
```

## 关键发现与沉淀

| 发现 | 影响范围 | 解决方案 | 编号 |
|------|----------|----------|------|
| Vue SPA hash 导航不可靠 | monthly-report (~90%失败) | SidebarNavigator + 页面身份验证 + retry | — |
| 月份切换后按钮 disabled 状态不更新 | monthly-report | force-enable + JS click | — |
| 多按钮 native click 被遮挡 | production 全模块 | `_js_click_by_text()` 统一处理 | FP-005 |
| 弹窗残留污染后续用例 | production 全模块 | fixture teardown JS 清理 + Escape | FP-006 |
| 同名 class 跨 Vue 组件标签不一致 | daily-report | `//*` 通配标签 XPath | FP-007 |

## 合规状态
- ✅ 所有 Page Object 继承 BasePage
- ✅ 无绝对 XPath、无 time.sleep (SidebarNavigator 内部除外)、无 print
- ✅ 导航统一使用 SidebarNavigator + 页面身份验证 + retry 模式
- ✅ conftest driver_setup 仅负责登录，导航下沉到各 page fixture
- ✅ 治理文档 4/5 子页面齐全（shift-report 除外）

## 开发顺序
1. ✅ daily-report — 完成
2. ✅ monthly-report — 完成（含 SPA 渲染问题修复）
3. ⏭️ shift-report — 前端未实现
4. ✅ shift-team-config — 完成
5. ✅ business-type-config — 完成


<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-17 21:52)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 5 (script/production/test_*.py) |
| Page Object | 4 (page/production_page/*.py) |
| 治理文档 | 27 .md 文件 |
| TECH_ANALYSIS | 4 |
| AUTO_STRATEGY | 4 |
| RISK_MODEL | 4 |
| PAGE_CONTEXT | 5 |
| SOP 状态 | completed |
| Phase 完成 | Automation, Bug Analysis, Data Sanitization, Execute & Debug, Knowledge, Project Init, Report, Requirement, Test Design |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->