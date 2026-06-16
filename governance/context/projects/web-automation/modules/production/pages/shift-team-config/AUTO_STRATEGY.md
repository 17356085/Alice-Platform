# AUTO_STRATEGY — production / shift-team-config

> 基于 TECH_ANALYSIS + TEST_CASES + 现有代码 | 2026-06-12
> CRUD 管理页（搜索+表格+弹窗），环境无种子数据。首轮 5 passed / 0 failed ✅

## 自动化目标
覆盖班次班组配置的页面展示、搜索/重置、新增弹窗交互。写操作（新增确定/编辑/删除）待环境有种子数据后补充。

## 推荐策略
- 脚本层级：ShiftTeamConfigPage（23方法PO）→ conftest.py（fixture + teardown）→ test_shift_team_config.py（5用例）
- 断言层级：页面级（元素可见/表头正确）+ 交互级（弹窗开闭/表单填写/搜索执行）
- 数据策略：只读型测试，新增表单填写后取消（不点确定），无脏数据
- 清理策略：conftest teardown JS 关闭弹窗 + Escape 兜底

## 覆盖矩阵

| 用例编号 | 标题 | 优先级 | 自动化 | 理由 |
|----------|------|--------|--------|------|
| TC-PROD-STC-001 | 页面基本元素加载 | P0 | ✅ | 冒烟必测：搜索区+表格+表头 |
| TC-PROD-STC-002 | 打开新增弹窗 | P1 | ✅ | 弹窗标题+字段完整性 |
| TC-PROD-STC-003 | 填写表单后取消 | P1 | ✅ | 表单交互+弹窗关闭 |
| TC-PROD-STC-004 | 按工厂搜索 | P2 | ✅ | 搜索功能不报错 |
| TC-PROD-STC-005 | 重置搜索条件 | P2 | ✅ | 输入框清空验证 |

## PageObject 拆分

```
ShiftTeamConfigPage ← 搜索区 + 表格 + 弹窗（23方法）
  ├── 搜索区：4输入 + 3按钮（搜索/重置/新增）
  ├── 表格：8列（含 checkbox + 操作列）+ 分页
  ├── 弹窗：6字段 + 确定/取消 + ×关闭
  │   └── 参数化 _DIALOG_FIELD_XPATH 按 label 定位
  ├── 行操作：编辑/删除
  └── 导航：SidebarNavigator + _is_on_page() 身份验证 + retry
```

## 公共组件复用

| 方法 | 来源 | 复用状态 |
|------|------|----------|
| navigate_to() | BasePage → SidebarNavigator | ✅ |
| wait_vue_stable() | BasePage | ✅ |
| is_visible() | BasePage | ✅ |
| _js_click_by_text() | 本 PO（从 MonthlyReportPage 复用模式） | ✅ |
| fill_dialog_field() | 本 PO（按 label 参数化） | ✅ |
| _is_on_page() | 本 PO（从 MonthlyReportPage 复用模式） | ✅ |

## ROI 分析

| 指标 | 值 |
|------|----|
| 页面类型 | 标准 CRUD，Element Plus 标准组件 |
| 开发耗时 | ~0.5h（23方法PO + 5用例，模板复用效益高） |
| 维护成本 | 低（CRUD 结构稳定，字段变更仅改定位器） |
| 首轮质量 | **5 passed / 0 failed** — 零缺陷交付 |

---
<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 -->
