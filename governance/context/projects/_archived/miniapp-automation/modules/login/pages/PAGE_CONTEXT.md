# PAGE_CONTEXT — miniapp / login

> 从 login.page.js + test_login.test.mjs 提取 | 2026-06-11

## 页面信息

| 属性 | 值 |
|------|-----|
| 路径 | `/pages/login/index` |
| Page Object | `login.page.js` (extends MiniPage) |
| 测试脚本 | `tests/p0-core/test_login.test.mjs` (TC-LOGIN-001~006) |

## 核心元素

| 元素 | 类型 | data key | 说明 |
|------|------|----------|------|
| 手机号输入 | input | `d` (phone) | 微信小程序编译后混淆名 |
| 密码输入 | input | `h` (password) | 同上 |
| 登录按钮 | button | bindtap `l` | 提交登录 |
| 密码可见切换 | icon | bindtap `j` | 显示/隐藏密码 |
| 用户协议链接 | text | bindtap `o` | |
| 隐私政策链接 | text | bindtap `p` | |
| 容器 | view | `.login-page` | 页面根容器 |

## 关键交互

1. 手机号+密码输入→点击登录→调用登录API→跳转首页
2. 密码可见性切换
3. 多角色账号登录后角色选择

## 检测方法

- `isOnLoginPage()`: 检查 data.d(phone) 和 data.h(password) 同时为字符串
- `waitForReady()`: 等待 `.login-page` 容器出现

## 已知风险

- 已登录态下 navigateTo 登录页→APP重定向→DevTools超时
- 微信授权弹窗不可控（需mock或手动处理）

<!-- status: draft | phase: Phase 1 | completed_by: ai-assistant | completed_at: 2026-06-11 -->
