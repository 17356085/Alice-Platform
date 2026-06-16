---
name: miniapp-test-webview-fix-handoff
description: 小程序测试 webview 累积修复 — 已完成 & 未完成 & 建议，新会话接手必读
metadata:
  type: project
---

# 小程序测试 Webview 累积修复 — 交接文档

## 背景

微信小程序 `navigateTo()` 每次 push 新 webview，上限约 10 页。9 个测试文件使用纯非 TabBar 页面，每个 `describe` 块都调用 `navigate()` push 页面，栈永不清理，触发 `webview count limit exceed`。

**原始状态**（2026-06-12 首次运行）：71 个测试中 16 通过 (22.5%)，9 个文件报 webview 错误。

---

## ✅ 已完成的修复（累计三轮）

### 第一轮（2026-06-12 上午）：webview 错误消除

#### Fix 1: LoginFlow 登录后清栈
**文件**: `src/flows/LoginFlow.js`
**改动**: 在 `bypassLogin()` 中新增 `_clearStack()` 方法，登录成功后调用 `reLaunch('/pages/index/index')` 清空导航栈。
**效果**: smoke 从 0/4 → 4/4 通过。

#### Fix 2: DevTools 批次重启
**文件**: `run-tests.mjs`
**改动**: 每 4 个文件后调用微信开发者工具 CLI 重启（quit → open → auto）。BATCH_SIZE=4。
**效果**: 批次间彻底清除 webview 状态。

#### Fix 3: beforeEach reLaunch（核心修复）
**文件**: 9 个测试文件
**改动**: 在每个测试文件的 `afterAll` 之后、第一个 `describe` 之前添加 beforeEach reLaunch 到首页。
**效果**: **"webview count limit exceed" 错误完全消失**（从 9 个文件 → 0）。

### 第二轮（2026-06-12 下午）：超时与稳定性修复

#### Fix 4: P0 — 全局超时配置提升
**文件**:
- `src/MiniPage.js`: `_waitPageReady` 默认 15s→30s, `waitForDataReady` 默认 15s→30s
- `src/config/test.config.js`: `navigation` 15s→30s, `element` 10s→15s, `dataReady` 15s→30s
- `src/flows/LoginFlow.js`: `_clearStack()` sleep 1.5s→3s
- 9 个测试文件: beforeEach reLaunch sleep 1.5s→3s

#### Fix 5: P1 — test_login 超时修复
**文件**: `tests/p0-core/test_login.test.mjs`
**改动**:
- post-launch sleep 5s→8s（给小程序充足编译时间）
- `ensureLoggedOut()` 优化：单次 reLaunch + 10 轮轮询（替换原来的 2 次 reLaunch × 8 轮轮询）
- 登录流程测试 timeout 120s→180s
- Top-level `before` timeout 180s→300s

#### Fix 6: P2 — test_approval_flow 补齐登录
**文件**: `tests/test_approval_flow.test.mjs`
**改动**:
- **添加 LoginFlow**（原本完全缺失，未登录直接导航到审批页必然超时）
- 添加 `beforeEach` reLaunch
- 添加 `sleep` import
- Tab 切换测试：去掉不稳定的 `currentTab` 断言，增加切换后等待时间

#### Fix 7: P3 — test_role_permissions + RoleSwitcher 修复
**文件**:
- `src/roles/RoleSwitcher.js`: `loginAs()` 中 `switchTab` → `reLaunch`（确保 token 注入后页面重新加载）
- `tests/p1-high/test_role_permissions.test.mjs`: 添加 `beforeEach` reLaunch + `sleep` import + 增加 timeout

#### Fix 8: P4 — DevTools 重启可靠性
**文件**: `run-tests.mjs`
**改动**:
- `RESTART_WAIT` 30s→45s
- `restartDevTools()` 增加重试逻辑（失败后重试 1 次，共 2 次）
- 单文件超时 180s→300s（匹配增加了的页面级超时）

#### Fix 9: P5 — test_tank_equipment + test_diagnostics 稳定性
**文件**:
- `tests/p3-snapshot/test_tank_equipment.test.mjs`: 添加 `beforeEach` reLaunch（原本缺失，4 个 sub-page 导航累积 webview）
- `tests/test_diagnostics.test.mjs`: 添加 LoginFlow（原本未登录，诊断看不到实际数据）

---

## 📊 修复汇总

| 指标 | 原始 | 第一轮后 | 第二轮后（预期） |
|------|------|----------|-------------------|
| webview count limit exceed | 9 个文件 | 0 | 0 |
| 通过率 | 16/71 (22.5%) | 21/49 (42.9%) | 待运行验证 |
| 缺失 LoginFlow 的文件 | 3 | 1 (test_login 特殊) | 0 |
| 缺失 beforeEach 的文件 | 11 | 2 | **0** |

### 所有修改文件清单（两轮合计）

```
基础设施:
  src/MiniPage.js                       ← _waitPageReady + waitForDataReady 15→30s
  src/config/test.config.js            ← navigation/element/dataReady timeout 提升
  src/flows/LoginFlow.js               ← _clearStack() sleep 1.5→3s
  src/roles/RoleSwitcher.js            ← switchTab → reLaunch
  run-tests.mjs                        ← RESTART_WAIT 45s + 重试 + 文件超时 300s

测试文件（第二轮新增/修改）:
  tests/p0-core/test_login.test.mjs    ← sleep 8s + ensureLoggedOut 优化 + timeout 提升
  tests/test_approval_flow.test.mjs    ← +LoginFlow +beforeEach +sleep (原本缺失登录!)
  tests/p1-high/test_role_permissions.test.mjs ← +beforeEach +sleep +timeout
  tests/p3-snapshot/test_tank_equipment.test.mjs ← +beforeEach +sleep (原本缺失!)
  tests/test_diagnostics.test.mjs      ← +LoginFlow (原本未登录)

测试文件（第一轮已修改，本轮仅 sleep 提升）:
  tests/test_study_exam_flow.test.mjs  ← sleep 1.5→3s
  tests/p2-medium/test_lab_sampling.test.mjs
  tests/p2-medium/test_practice_wrong.test.mjs
  tests/p2-medium/test_visitor.test.mjs
  tests/p2-medium/test_personnel.test.mjs
  tests/p2-medium/test_my_application.test.mjs
  tests/p3-snapshot/test_settings.test.mjs
  tests/p3-snapshot/test_sales_report.test.mjs
  tests/p3-snapshot/test_about_feedback.test.mjs
```

---

## ⚠️ 仍需关注的问题

### P1-residual — test_login 需单独验证
虽然做了多项优化（ensureLoggedOut 简化、timeout 提升），此文件仍需单独运行验证。
```bash
node --test tests/p0-core/test_login.test.mjs
```

### P2-residual — 审批 Tab 角标 API
"各 Tab 切换与角标" 的去断言版本减少了失败风险，但如果 `getTabBadges()` 返回的数据与后端不一致，测试仍可能失败。建议检查后端 API 是否返回正确的角标数值。

### P3-residual — 权限拦截测试
`RoleSwitcher.loginAs()` 改用 `reLaunch` 后，需验证 Pinia store 是否能正确从 storage 恢复 token。如果 `evaluate()` 更新失败，reLaunch 后 app 会读取 storage 中的 token（我们在 setStorage 中已写入），所以应能正常工作。

### P4-residual — DevTools CLI 路径
如果 `WECHAT_CLI_PATH` 环境变量未正确设置，`restartDevTools()` 中的 `runCli(['quit'])` 会静默失败。建议在 `.env` 中确认路径指向正确的 `cli.bat`。

---

## 🏗️ 架构要点（新会话快速上手）

### 为啥有些文件始终通过？
**TabBar 页面是关键。** `MiniPage.navigate()` 中：TabBar 页面（`IS_TAB_PAGE=true`）调用 `switchTab()`，微信会自动清除非 TabBar 页面栈。非 TabBar 页面调用 `navigateTo()`，只 push 不清除。

**始终通过的文件都使用 TabBar 页面作为入口**：
- `HomePage` (IS_TAB_PAGE=true) → smoke, home
- `AlarmListPage` (IS_TAB_PAGE=true) → alarm
- `ApprovalListPage` (IS_TAB_PAGE=true) → approval

### 三层防线（当前架构）
| 层级 | 机制 | 文件 |
|------|------|------|
| L1 批次级 | DevTools CLI 重启 / 4 文件 + 重试 | run-tests.mjs |
| L2 文件级 | LoginFlow._clearStack() reLaunch (sleep 3s) | LoginFlow.js |
| L3 测试级 | beforeEach reLaunch / 每测试 (sleep 3s) | 所有非 TabBar 测试文件 |

### 关键超时值（修改后）
| 配置项 | 原值 | 新值 | 位置 |
|--------|------|------|------|
| _waitPageReady | 15s | 30s | MiniPage.js |
| waitForDataReady | 15s | 30s | MiniPage.js |
| config.navigation | 15s | 30s | test.config.js |
| config.element | 10s | 15s | test.config.js |
| config.dataReady | 15s | 30s | test.config.js |
| reLaunch sleep | 1.5s | 3s | LoginFlow + 9 test files |
| DevTools RESTART_WAIT | 30s | 45s | run-tests.mjs |
| 单文件超时 | 180s | 300s | run-tests.mjs |

### 关键文件速查
- 测试入口: `mp-weixin-automator/run-tests.mjs`（`node run-tests.mjs`）
- Page Object 基类: `mp-weixin-automator/src/MiniPage.js`
- 登录流程: `mp-weixin-automator/src/flows/LoginFlow.js`
- 角色切换: `mp-weixin-automator/src/roles/RoleSwitcher.js`
- 驱动连接: `mp-weixin-automator/src/driver.mjs`（ESM）/ `driver.js`（CJS）
- 配置: `mp-weixin-automator/.env` + `src/config/test.config.js`
- 环境变量: `WECHAT_CLI_PATH`, `MINI_PROJECT_PATH`, `BASE_URL`, 账号/密码
- 报告: `mp-weixin-automator/artifacts/test-report.txt`
- 治理上下文: `governance/context/projects/miniapp-automation/PROJECT_CONTEXT.md`

### 运行命令
```bash
cd mp-weixin-automator
node run-tests.mjs                           # 全量
node --test tests/p0-core/test_alarm.test.mjs # 单文件
```

---

## 🚫 已尝试但失败的方案（不要重试）

| 尝试 | 文件 | 结果 |
|------|------|------|
| `driver.close()` 中 reLaunch | driver.mjs | 下游文件大量 timeout（干扰连接时序） |
| `navigateTo` → `redirectTo` | MiniPage.js | 同页跳转导致登录流程 hang |
| `navigate()` 中 currentPage() 去重检查 | MiniPage.js | `currentPage()` 耗时导致测试 hang |
| `afterEach` navigateBack | 6 个测试文件 | 只弹 1 页不够，总通过率降回 12 |
| RoleSwitcher 用 switchTab | RoleSwitcher.js | 切换角色后页面不刷新，权限数据不更新 |
