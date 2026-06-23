# MODULE_CONTEXT — dcs

## 基本信息
- 模块ID：dcs
- 模块名称：DCS 数据监控
- 所属项目：web-automation
- 创建日期：2026-06-11
- 导航路径：DCS 数据监控（一级菜单，含 5 个子页面）

## 模块定位
DCS 数据监控模块覆盖关键参数实时监控、点位数据查看与管理、数据上传日志等工业数据监控场景。

## 当前资产清单

| 资产类型 | 文件 | 规模 |
|---------|------|------|
| Page Object | `page/dcs_page/` | 5 个 PO (MonitorPage, AllDataPage, CommonDataPage, PointConfigPage, UploadLogPage + \_\_init\_\_) |
| 测试脚本 | `script/dcs/` | 5 个 test_*.py |
| Fixtures | `script/dcs/conftest.py` | `driver_setup` (module 级) + 5 个页面 fixture |
| 治理文档 | `governance/.../modules/dcs/pages/*/` | 5 PAGE_CONTEXT + 5 TECH_ANALYSIS + 5 AUTO_STRATEGY + 5 PAGE_INTERFACE + 5 TEST_DESIGN + 5 PAGE_ELEMENT_POSITION + 5 RISK_MODEL + 5 TEST_CASES + 1 共享 BUG_ANALYSIS |

> 更新于 2026-06-22 — 治理文档 100% (8/8 类型 × 5页)，Phase 0-9 全部完成

## 页面状态（按 conftest.py 路由映射）

| 路由 key | 页面名称 | hash 路由 | Page Object | 测试脚本 | PAGE_CONTEXT | 整体 |
|----------|---------|-----------|:-----------:|:-------:|:------------:|:----:|
| test_monitor | 关键参数监控 | `#/monitor` | ✅ DcsMonitorPage | ✅ test_monitor.py | ✅ | ready |
| test_all_data | 全部点位 | `#/all-data` | ✅ AllDataPage | ✅ test_all_data.py | ✅ | ready |
| test_common_data | 常用点位 | `#/common-data` | ✅ CommonDataPage | ✅ test_common_data.py | ✅ | ready |
| test_point_config | 点位配置 | `#/point-config` | ✅ PointConfigPage | ✅ test_point_config.py | ✅ | ready |
| test_upload_log | 上传日志 | `#/upload-log` | ✅ UploadLogPage | ✅ test_upload_log.py | ✅ | ready |

## 合规状态
- ✅ Page Object 已创建（继承 BasePage，Element Plus 通用定位器）
- ✅ 测试脚本已创建（smoke + CRUD + 分页）
- ✅ conftest.py 有 driver_setup + 5 页面 fixture
- ⚠️ 定位器为 Element Plus 通用模式，需实地验证并修正
- ⚠️ conftest.py `time.sleep(2)` 待替换为 `wait_page_ready`

## 治理说明
- 模块状态：**ready**（治理文档 100% + 代码齐全，待 E2E 验证）
- 优先级：中 — DCS 数据监控属于工业核心场景
- 定位器策略：Element Plus 标准 CSS 选择器 + XPath 文本匹配
- 注意：DCS 页面可能使用非标准 Element Plus 组件，首次 E2E 运行需留足调试时间

## 映射状态
- ✅ MODULE_CONTEXT.md（本文档）
- ✅ 5 个子页面 PO + 测试脚本 + PAGE_CONTEXT
- ✅ 5 PAGE_INTERFACE.yaml (2026-06-22)
- ✅ 5 TEST_DESIGN.md (2026-06-22)
- ✅ 5 PAGE_ELEMENT_POSITION.md (2026-06-22)
- ✅ 5 RISK_MODEL.md per-page
- ✅ 5 TEST_CASES.md per-page
- ⬜ E2E 运行验证

<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-18 10:54)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 5 (script/dcs/test_*.py) |
| Page Object | 5 (page/dcs_page/*.py) |
| 治理文档 | 36 .md 文件 |
| TECH_ANALYSIS | 6 |
| AUTO_STRATEGY | 6 |
| RISK_MODEL | 6 |
| PAGE_CONTEXT | 7 |
| PAGE_INTERFACE | 5 |
| TEST_DESIGN | 5 |
| PAGE_ELEMENT_POSITION | 5 |
| SOP 状态 | ready |
| Phase 完成 | 0-7 (治理100%，待E2E) |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->
