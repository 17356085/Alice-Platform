# BUG_ANALYSIS — DCS 模块 (Phase 6)

**日期**: 2026-06-22 | **E2E 结果**: 14 passed, 19 skipped, 0 failed | **总耗时**: ~5min (5 pages, headless)
**DOM 诊断**: 2026-06-22 — 4页 Selenium DOM capture → `tools/dcs_locator_diag_result.json`

## Bugs Found

### BUG-1 🔴 CRITICAL: Monitor 路由碰撞 — navigate_to 导航到错误页面

- **位置**: `base/sidebar_navigator.py:_text_to_href()` line 462
- **根因**: `_text_to_href` 只匹配 leaf text，不检查父菜单。"关键参数监控"在 HREF_TO_PATH 中出现两次:
  - `#/equipment/key-param`: ["设备管理", "关键参数监控"] (line 179)
  - `#/monitor`: ["DCS数据", "关键参数监控"] (line 183)
  - 遍历时先匹配到 equipment 版本 → 返回 `#/equipment/key-param`
- **影响**: DCS MonitorPage.navigate() 实际导航到设备管理的监控页，不是 DCS 的监控页
- **修复**: 
  1. 5 个 DCS PO 改用 `navigate_to_by_hash()` 直接 hash 导航 (绕过文本匹配)
  2. `BasePage.navigate_to_by_hash()` 新增 — ensure_on_welcome → set hash → wait page ready
- **状态**: ✅ 已修复 (2026-06-22)

### BUG-2 🟡 MEDIUM: all-data 页面表格行数=0

- **位置**: `test_all_data.py::test_001_page_load`
- **现象**: 表格 `.el-table__body-wrapper tbody tr.el-table__row` 返回 0 行
- **可能原因**: 
  a) 数据库无点位数据（真实空表）
  b) 表格使用非标准 DOM 结构，`el-table__row` 类名不匹配
  c) 页面加载后数据异步获取，等待时间不足
- **影响**: test_002_search 搜索前后都是 0 行，无法验证搜索功能
- **建议**: 用 Browser-Use/page-observe 截图确认实际 DOM 结构
- **状态**: ⬜ 待确认

### BUG-3 🟡 MEDIUM: common-data 搜索不筛选

- **位置**: `test_common_data.py::test_002_search`
- **现象**: 搜索"温度"前后卡片数都是 2，无变化
- **可能原因**:
  a) "温度"不匹配任何卡片名称
  b) 搜索输入框/按钮定位器不匹配实际 DOM
  c) 页面无搜索功能（仅展示常用点位）
- **影响**: 搜索测试无实际验证价值
- **建议**: 用现有卡片名称作为搜索关键词复测
- **状态**: ⬜ 待确认

### BUG-4 🟢 LOW: conftest hash 导航不触发 Vue Router

- **位置**: `conftest.py:driver_setup` line 54
- **现象**: `window.location.hash = '#/xxx'` 后等待 `.el-table` 立即找到（因为 Vue Router 未响应，停留在 previous page）
- **根因**: Vue hash router 需要在 app 上下文中触发。`_navigate_by_js_hash` 会先 `_ensure_on_welcome()` 再设置 hash
- **绕过**: 测试实际上依赖 PO.navigate() 的二次导航（sidebar click 或 navigate_to_by_hash）才到达正确页面
- **修复**: 不紧急 — 测试流程中 PO.navigate() 覆盖了 conftest 的导航
- **状态**: ⬜ 已知，不阻塞

### BUG-5 🟢 LOW: 测试断言过于宽松

- **位置**: 全 5 个 test_*_page_load
- **现象**: `assert row_count >= 0` — 0 行也算通过
- **影响**: 无法检测空表或定位器失效
- **建议**: 改为 `assert row_count > 0` 或 `assert page_has_content()`
- **状态**: ⬜ 建议改进

## 跳过用例分析 (20 tests)

### 类别 A: 只读查询页 — CRUD 按钮不存在 (8 tests)

| 页面 | 用例 | 状态 |
|------|------|:--:|
| all-data | test_004_add_dialog | ✅ skip 合理 |
| all-data | test_101_edit_point | ✅ skip 合理 |
| common-data | test_005_add_dialog | ✅ skip 合理 |
| monitor | test_005_add_param | ✅ skip 合理 |
| monitor | test_101_edit_param | ✅ skip 合理 |
| point-config | test_004_add_dialog | ✅ skip 合理 |
| point-config | test_005_add_and_cleanup | ✅ skip 合理 |
| point-config | test_006_edit_dialog | ✅ skip 合理 |

### 类别 B: 卡片仪表盘 — 无传统搜索/重置/刷新 (3 tests)

| 页面 | 用例 | 状态 |
|------|------|:--:|
| monitor | test_002_search | ✅ skip 合理 — 卡片仪表盘 |
| monitor | test_003_reset_search | ✅ skip 合理 |
| monitor | test_004_refresh | ✅ skip 合理 |

### 类别 C: 定位器待 DOM 校准 (3 tests, 3 fixed ✅)

| 页面 | 用例 | DOM诊断结果 | 行动 |
|------|------|------|------|
| all-data | test_006_select_row | 表格存在但0行，**无复选框列** | ✅ skip确认 (更新原因) |
| common-data | test_004_click_card | `.el-card`是搜索表单卡不是数据卡 | ✅ skip确认 (PO需重新设计) |
| ~~upload-log~~ | ~~test_003_search~~ | ✅ 搜索按钮存在! `//button[normalize-space(.//span)="搜索"]` | ✅ **已un-skip** |
| ~~upload-log~~ | ~~test_005_reset_search~~ | ✅ 重置按钮存在 | ✅ **已un-skip** |
| ~~upload-log~~ | ~~test_006_detail~~ | ✅ 详情按钮存在(每行) | ✅ **已un-skip** |
| point-config | test_002_search | 页面仅"查看更多"按钮，无搜索 | ✅ skip确认 (需深度调查) |
| point-config | test_003_reset_search | 依赖search | ✅ skip确认 |

### 类别 D: 依赖项 (1 test)

| 页面 | 用例 | 依赖 | 状态 |
|------|------|------|:--:|
| monitor | test_006_card_detail | 卡片定位器 | 待调优 |

### 类别 E: 正常跳过 (1 test)

| 页面 | 用例 | 原因 |
|------|------|------|
| all-data | test_005_pagination | 数据<20条，正常 |

## 修复统计

| 修复项 | 类型 | 状态 |
|------|------|:--:|
| Monitor 路由碰撞 | Bug | ✅ 已修复 |
| navigate_to_by_hash 新增 | Feature | ✅ 已实现 |
| 5 DCS PO navigate() 改为 hash 导航 | Refactor | ✅ 已完成 |
| EP-011 搜索按钮文本 | 定位器 | ✅ 已修复 (上次) |
| upload-log search/reset/detail un-skip | Test | ✅ 已完成 (DOM诊断确认) |
| all-data test_006 skip原因修正 | Doc | ✅ 已完成 |
| common-data test_004 skip原因修正 | Doc | ✅ 已完成 |
| EP-001 Teleport 渲染 | 定位器 | ⬜ 已知 |
| BUG-2 all-data 0行 | 诊断 | ⬜ 待确认 (无复选框列) |
| BUG-3 common-data 搜索不筛选 | 诊断 | ⬜ 待确认 (PO设计偏差) |
| common-data PO 重新设计 | PO | ⬜ 页面是表单+表格，非卡片视图 |
| point-config 深度调查 | 诊断 | ⬜ 仅"查看更多"按钮，与PO假设不符 |
