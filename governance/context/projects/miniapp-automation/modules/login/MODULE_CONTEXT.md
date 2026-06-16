# MODULE_CONTEXT — miniapp / login

> 2026-06-11 | 测试层级: p0-core | Page Object: login.page.js

## 模块边界

登录/认证模块。支持微信一键登录、手机号登录、多角色切换。

## 页面清单

| 页面 | PO | 测试 | 状态 |
|------|-----|------|:--:|
| 登录页 | login.page.js | test_login.test.mjs (TC-LOGIN-001~006) | ✅ |

## 核心业务流程

1. 未登录→微信授权→获取token→进入首页
2. 多角色账号→切换角色→权限刷新

## 自动化策略

- MiniDriver.launch() 启动→LoginPage.isOnLoginPage() 检测
- 强制清token+reLaunch 确保未登录态
- 6条P0用例：登录页展示/微信登录/手机号登录/错误处理/退出登录/Token过期

## 关键风险: 已登录态下navigateTo登录页被APP重定向(DevTools超时)

<!-- status: draft | phase: Phase 0.5 | completed_by: ai-assistant | completed_at: 2026-06-11 -->
