# MODULE_CONTEXT — miniapp / home

> 2026-06-11 | 测试层级: smoke | Page Object: home.page.js

## 模块边界

首页数据看板。展示关键指标卡片、快捷入口、待办提醒。

## 页面清单

| 页面 | PO | 测试 | 状态 |
|------|-----|------|:--:|
| 首页看板 | home.page.js | test_home.test.js (smoke) | ✅ |

## 核心元素

- 统计卡片（今日产量/库存/报警数）
- 快捷入口网格（设备/储罐/化验室/审批）
- 待办列表
- 底部Tab导航

## 自动化策略

- 冒烟测试：登录后首页加载→统计卡片可见→快捷入口可点击
- 角色差异：不同角色首页卡片内容不同

<!-- status: draft | phase: Phase 0.5 | completed_by: ai-assistant | completed_at: 2026-06-11 -->
