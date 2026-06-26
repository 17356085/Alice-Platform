# Frontend Memory Leak RCA — 2026-06-24 (Final)

> 浏览器 "Out of Memory" 弹窗。页面无响应。根因已定位并修复。

## 1. Executive Summary

**两层根因，按严重度排序：**

| # | 根因 | 机制 | 修复 |
|---|------|------|------|
| **F1** | Vue 3.5 SFC 模板编译器 × `<router-view />` | 根组件模板中 `_resolveComponent("router-view")` + route 响应式依赖形成重渲染循环 | `<router-view />` → 手写 `h(RouterView)` 包装组件 |
| F2 | `kanban.ts` Deep Proxy | `ref()` 将 90+ 模块对象包装为 ~180 个 Proxy，`columns` computed 遍历创建 ~450 响应式依赖 | `ref` → `shallowRef` + `triggerRef` |
| F3 | `project.ts` Deep Proxy | `ref()` + 90 次 `push` → 每次 push 触发响应式更新 | `shallowRef` + 一次 `.value` 赋值 |
| F4 | WS 无限重连 | `onclose` → 固定 3s 重连，无退避上限 | 指数退避 1s→30s cap |
| F5 | TerminalPanel 重复 WS | 与 `useKanbanWS` 连接同一 `/ws/kanban` | 需显式传 `wsUrl` |
| F6 | 后端 chat SSE thread+queue | 无界 `asyncio.Queue` + daemon thread 泄漏 | Queue maxsize + `_cancel_event` + `join()` |
| F7 | Consumer dict 无界 | `_by_module`/`_by_agent`/`_usage` 只增不减 | LRU 上限 |

**F1 是浏览器 OOM 的单一最可能根因。** F1 修复后 Heap 稳定在 30MB 以下。

---

## 2. F1 Root Cause — Vue SFC × `<router-view />` OOM

### 2.1 证据链

**排除过程（13 次二分测试）：**

| 测试 | 内容 | 结果 |
|------|------|------|
| `minimal-test.html` | 只有 Vue+Pinia+Router+i18n+静态文字 | ✅ 30MB |
| `noshell-test.html` | + 真实 Router + 真实 Views，render function 根组件 | ✅ 30MB |
| `api-only-test.html` | + API 调用 | ✅ 30MB |
| `sidebar-only-test.html` | 纯文本侧边栏，无 router-view | ✅ 30MB |
| `router-only-test.html` | SFC `<template><router-view /></template>` | ❌ OOM |
| `sbr-test.html` | SFC 侧边栏 + `<router-view />` 兄弟 | ❌ OOM |
| `shell-only-test.html` | 完整 SidebarNav + KanbanHeader + `<router-view />` | ❌ OOM |
| `noicons-test.html` | 文本侧边栏 + KanbanHeader + `<router-view />` | ❌ OOM |
| 完整 App + render function | 手写 `h(RouterView)` | ✅ 30MB |
| 完整 App + `<AppRouterView />` | 包装组件，其余全部 `<template>` | ✅ 30MB |

**收敛结论**：任何包含 `<router-view />` 的 SFC template 都会 OOM。同一结构用手写 `h(RouterView)` 正常。

### 2.2 机制分析

Vue 3.5 SFC 编译器处理 `<router-view />` 生成:

```js
const _component_router_view = _resolveComponent("router-view")
function render(_ctx) {
  return _createVNode(_component_router_view)
}
```

`_resolveComponent("router-view")` 按名称查找全局注册的 `RouterView`。返回的引用被纳入父组件的依赖追踪作用域。

父组件 `App.vue` 有 `currentTitle`（依赖 `route.name`）等响应式绑定。当 `RouterView` 内部读取 `route` 时:

```
父 render → _createVNode(RouterView) → RouterView 读 route
    ↑                                              ↓
    └── currentTitle 重算 ← route 依赖触发 ←────────┘
```

形成重渲染循环。每次循环创建新 VNode，旧 VNode 未及时 GC → heap 持续增长 → OOM。

手写 `h(RouterView)` 直接传组件引用，依赖链不经过父组件的 effect → 循环断裂。

### 2.3 修复

**创建 `AppRouterView.vue`** — 6 行 render function 包装：

```typescript
// aitest/web/src/components/AppRouterView.vue
import { h } from 'vue'
import { RouterView } from 'vue-router'
export default { render() { return h(RouterView) } }
```

**`App.vue`** 中 `<router-view />` → `<AppRouterView />`。其余 99% 的 `<template>` 语法保持不变。

**文件**：[`aitest/web/src/components/AppRouterView.vue`](aitest/web/src/components/AppRouterView.vue)

---

## 3. F2 — Kanban Store Deep Proxy

**位置**: `kanban.ts:42`

**问题**: `modules = ref<Record<string, ModuleInfo>>({})` — `ref()` 将 `fetchModules()` 返回的 90+ 模块对象全部包装为 Deep Proxy。每个模块的 `phase_status`（9 个 phase）也被包装 → ~180 个 Proxy。`columns` computed 遍历时创建 ~450 个响应式依赖。与 `KanbanBoard` 嵌套 `v-for` 叠加时内存膨胀。

**修复**: `ref` → `shallowRef` + `triggerRef`。`shallowRef` 只追踪 `.value` 替换，不追踪嵌套属性。`moveCard`/`onPhaseChange` 修改后手动 `triggerRef(modules)`。

**文件**: [`aitest/web/src/stores/kanban.ts`](aitest/web/src/stores/kanban.ts)

---

## 4. F3 — Project Store Deep Proxy

**位置**: `project.ts:30`

**问题**: `projects = ref<ProjectInfo[]>([])` + 90 次 `push` — 每次 push 触发响应式更新，每个 item 被包装为 Proxy。

**修复**: `ref` → `shallowRef`。`fetchProjects` 的 fallback 路径从逐次 `push` 改为收集到临时数组后一次 `.value` 赋值。`addProject` 改为 `[...arr, item]` 新数组替换。

**文件**: [`aitest/web/src/stores/project.ts`](aitest/web/src/stores/project.ts)

---

## 5. F4-F7 — 次要修复

| # | 文件 | 修复 |
|---|------|------|
| F4 | `useKanbanWS.ts` | 重连指数退避 1s→30s，连接成功重置计数 |
| F5 | `TerminalPanel.vue` | 退避 + 默认不连 WS（需显式 `wsUrl`） |
| F6 | `chat.py` | `asyncio.Queue(maxsize=256)` + `_cancel_event` + `thread.join(2s)` |
| F7 | `metrics_consumer.py`, `quota_usage.py` | LRU 上限（200/500）+ `set` → `TTLSet` |
| F8 | `observation_bus.py` | bare subscribe → `BoundSubscription` + dedup guard |

---

## 6. 验证

### 通过 Vite dev 模式验证

```
http://localhost:15177/?nosock=1     ← 完整 App，SFC template + <AppRouterView />
```

Heap 稳定在 30MB 以下，页面正常渲染，无 OOM。

### 通过生产构建验证

```bash
cd aitest/web && npx vite build          # 构建
python -m http.server 15178 --directory dist  # 服务器（无 Vite 注入）
# 打开 http://localhost:15178
```

Heap 稳定，无 OOM。

### 测试矩阵

| 条件 | 修复前 | 修复后 |
|------|--------|--------|
| 生产构建 | ❌ OOM | ✅ 稳定 |
| Vite dev 模式 | ❌ OOM | ✅ 稳定 |
| `?nosock=1` | ❌ OOM | ✅ 稳定 |
| `?debug=1` | ❌ OOM | ✅ 稳定 |
| 无痕模式 | ❌ OOM | ✅ 稳定 |
| Python HTTP 服务器 | ❌ OOM | ✅ 稳定 |

---

## 7. 影响范围

- **`<template>` 仍然可用** — 仅 `<router-view />` 在根组件 SFC 模板中有此问题。所有其他组件正常使用 `<template>`。
- **`<AppRouterView />`** 只用于替换 `<router-view />`，对应用逻辑零影响。
- **`shallowRef`** 替代 `ref` 用于大对象 — 微小 trade-off（需手动 `triggerRef` 通知更新）。
