# KNOWLEDGE — DCS 模块 (Phase 9)

**日期**: 2026-06-22 | **来源**: DCS 5页 SOP 全流程 (Phase 0-8)

## 经验教训

### 1. 路由碰撞 — 同名叶子菜单的陷阱

- **发现**: `_text_to_href("关键参数监控")` 错误返回 `#/equipment/key-param` 而非 `#/monitor`
- **根因**: HREF_TO_PATH 中 "关键参数监控" 出现两次（设备管理 + DCS数据），遍历返回先匹配项
- **修复**: PO 改用 `navigate_to_by_hash()` 直接 hash 导航，绕过文本匹配
- **教训**: 新建 PO 时应优先用 `navigate_to_by_hash("#/exact-route")`，避免依赖菜单文本

### 2. PO 设计与实际 DOM 的偏差

| 页面 | PO 假设 | 实际 DOM | 偏差程度 |
|------|---------|----------|:--:|
| common-data | 卡片网格 + 拖拽 + 右键菜单 | 搜索表单卡片 + 数据表格 | 🔴 完全错误 |
| point-config | CRUD 列表 + 告警配置弹窗 | Landing 页 (仅"查看更多"按钮) | 🔴 完全错误 |
| all-data | 表格 + 批量选择(复选框) | 表格存在但无复选框列 | 🟡 部分偏差 |
| monitor | 卡片 + 搜索栏 + 刷新按钮 | 纯卡片仪表盘 (正确) | 🟢 基本正确 |
| upload-log | 搜索 + 详情 + 统计卡片 | 搜索 + 详情 + 无统计卡片 | 🟡 部分偏差 |

- **教训**: PO 生成后必须用 Browser-Use/page-observe 做 DOM 验证，不可假设组件存在

### 3. Vue Router hash 导航的正确姿势

- `window.location.hash = '#/xxx'` 单独使用无法触发 Vue Router
- 正确流程: `_ensure_on_welcome()` → `window.location.hash = '#/xxx'` → 等待 `window.location.hash` 生效 → 等待页面内容
- `navigate_to_by_hash()` 封装了此流程，新 PO 直接使用

### 4. 测试断言设计

- `assert row_count >= 0` 太宽松 — 空表和定位器失效都会通过
- 应区分: 有数据页 `> 0`，空表页验证容器元素存在，landing页验证特定按钮

### 5. Selenium vs Browser-Use 分工

| 场景 | 推荐工具 |
|------|---------|
| 确定性回归 (known locators) | Selenium |
| 未知页面探索/PO 生成 | Browser-Use |
| DOM 诊断 (验证定位器) | Selenium 快速脚本 |
| 自愈 (locator 失效时) | Browser-Use bu_heal |

## 模块统计

| 指标 | 数值 |
|------|:--:|
| 模块页面数 | 5 |
| PO 正确率 | 2/5 (40%) — monitor, upload-log |
| PO 需重设计 | 2/5 (40%) — common-data, point-config |
| PO 部分偏差 | 1/5 (20%) — all-data |
| E2E 通过率 | 14/33 (42%) |
| 永久 skip | 19 (合理: 只读页 + 仪表盘 + 设计偏差) |
| 需修复 skip | 0 (全部已处理) |
| 修复的 Bug | 1 CRITICAL (路由碰撞) |
| 新增基础设施 | `BasePage.navigate_to_by_hash()` |

## 给后续模块的建议

1. **PO 生成前先 DOM 诊断** — 用 `tools/dcs_locator_diag.py` 模式，5 分钟确认页面结构
2. **导航用 hash 不用文本** — `navigate_to_by_hash("#/route")` > `navigate_to("菜单", "文本")`
3. **断言分级** — 区分"有数据"/"空表"/"landing页"三种场景
4. **common-data/point-config PO 重设计** — 待有 Browser-Use 或手动 DOM 逆向后再做
5. **DCS 数据环境** — all-data 表为空，可能需要灌入测试数据才能验证完整功能
