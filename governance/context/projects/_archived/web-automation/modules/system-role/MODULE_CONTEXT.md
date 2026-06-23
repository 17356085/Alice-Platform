# MODULE_CONTEXT — system-role

## 基本信息
- 模块ID：system-role
- 模块名称：角色管理
- 所属项目：web-automation
- 存量来源：d:\Desktop\Alice\TestIntern_library\02-项目文档\contexts\system-role\
- 关联旧文档：ROLE_CONTEXT.md / RBAC_TEST_PLAN.md / TEST_ANALYSIS.md

## 模块定位
角色管理是 RBAC 权限配置中心，负责角色 CRUD、权限分配、数据范围配置和分配用户。

## 当前页面清单
- role-list - 已完成 PAGE_CONTEXT 与 ANALYSIS 映射

## 模块级专题文档
- RBAC_TEST_PLAN.md
- TEST_ANALYSIS.md

## 治理说明
- 当前先将旧专题文档映射为模块级资产
- 页面细节统一沉到 pages/role-list/
- 后续逐步把 ROLE_CONTEXT 内容拆入 MODULE_CONTEXT 与 PAGE_CONTEXT

## 映射状态
- role-list 已完成 PAGE_CONTEXT、ANALYSIS 映射
- RBAC_TEST_PLAN 已完成模块级映射


<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-18 10:54)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 6 (script/system-role/test_*.py) |
| Page Object | 1 (page/system-role_page/*.py) |
| 治理文档 | 15 .md 文件 |
| TECH_ANALYSIS | 1 |
| AUTO_STRATEGY | 1 |
| RISK_MODEL | 2 |
| PAGE_CONTEXT | 3 |
| SOP 状态 | completed |
| Phase 完成 | Automation, Bug Analysis, Data Sanitization, Execute & Debug, Knowledge, Project Init, Report, Requirement, Test Design |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->