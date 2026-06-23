# MODULE_CONTEXT — miniapp / alarm

> 2026-06-11 | 测试层级: p0-core | Page Object: alarm.page.js

## 模块边界

报警模块。展示实时报警列表、报警详情、报警处理。

## 页面清单

| 页面 | PO | 测试 | 状态 |
|------|-----|------|:--:|
| 报警列表 | alarm.page.js | test_alarm.test.js (p0) | ✅ |
| 报警详情 | alarm.page.js | 同上 | ✅ |

## 核心元素

- 报警列表（按时间倒序）
- 报警级别标签（红/黄/橙）
- 报警详情（数值/阈值/时间）
- 报警处理按钮（确认/忽略）

## 自动化策略

- 登录→导航到报警Tab→列表加载→点击查看详情→处理报警

<!-- status: draft | phase: Phase 0.5 | completed_by: ai-assistant | completed_at: 2026-06-11 -->
