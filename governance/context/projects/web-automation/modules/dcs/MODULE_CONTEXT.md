# MODULE_CONTEXT — dcs

## 基本信息
- 模块ID：dcs
- 模块名称：DCS 数据监控
- 所属项目：web-automation
- 创建日期：2026-06-11
- 导航路径：DCS 数据监控（一级菜单，含 5 个子页面）

## 模块定位
DCS 数据监控模块覆盖关键参数实时监控、点位数据查看与管理、数据上传日志等工业数据监控场景。目前处于骨架阶段，仅有 conftest.py 路由映射，Page Object 和测试脚本待实现。

## 当前资产清单

| 资产类型 | 文件 | 规模 |
|---------|------|------|
| Page Object | `page/dcs_page/` | 0 个 PO（仅 `__init__.py`）|
| 测试脚本 | `script/dcs/` | 0 个测试文件 |
| Fixtures | `script/dcs/conftest.py` | `driver_setup` (module 级) + 5 个路由映射 |

## 计划子页面（按 conftest.py 路由映射）

| 路由 key | 页面名称 | hash 路由 | 状态 |
|----------|---------|-----------|------|
| test_monitor | 关键参数监控 | `#/monitor` | 🔴 待开发 |
| test_all_data | 全部点位 | `#/all-data` | 🔴 待开发 |
| test_common_data | 常用点位 | `#/common-data` | 🔴 待开发 |
| test_point_config | 点位配置 | `#/point-config` | 🔴 待开发 |
| test_upload_log | 上传日志 | `#/upload-log` | 🔴 待开发 |

## 合规状态
- ⬜ Page Object 待创建（需继承 BasePage）
- ⬜ 测试脚本待创建
- conftest.py 有骨架 `driver_setup` fixture，但使用了 `time.sleep(2)` 等待页面加载 → 后续需替换为 `wait_page_ready` 或 `wait_vue_stable`

## 治理说明
- 模块状态：**scaffold-only**（骨架阶段，无 Page Object 和测试用例）
- 优先级：中 — DCS 数据监控属于工业核心场景，建议 second batch 启动
- 开发顺序建议：关键参数监控 → 全部点位 → 常用点位 → 点位配置 → 上传日志
- 每个子页面开发时，按 SOP Phase 流程推进（PAGE_CONTEXT → TEST_DESIGN → Page Object → 测试脚本）
- 注意：DCS 数据监控页面可能使用自定义 UI 组件（非标准 Element Plus），定位器策略需实地评估

## 映射状态
- ✅ MODULE_CONTEXT.md（本文档）
- ⬜ 全部子页面待开发
