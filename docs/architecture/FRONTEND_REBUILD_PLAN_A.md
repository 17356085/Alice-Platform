# Frontend 重构方案 A — 多入口构建

> 目标：消除生产构建 OOM，保留 Vite + Vue 3.5 技术栈，最小改动。

## 原理

Dev 模式不 OOM 是因为每个 `.vue`/`.ts` 文件是独立 ESM 模块，各自持有独立闭包。Vue 的响应式依赖链被模块边界截断。

生产构建 Rollup 把所有模块打进一个文件，所有闭包合并。App 壳的 `currentTitle`/`currentViewName`（依赖 `route`）+ `RouterView`（内部读 `route`）形成完整闭合的响应式循环。

多入口让 App 壳和每个页面各自独立 chunk，模块边界不被合并 → 循环断裂。

## 任务分解

### Phase 1：环境准备（0.5h）

| # | 任务 | 文件 | 内容 |
|---|------|------|------|
| 1.1 | 备份当前 `main.ts` | — | `cp main.ts main.backup.ts` |
| 1.2 | 确认 dev 模式正常 | — | `npx vite --port 15177`，打开确认无 OOM |

**验收**：Dev 模式页面正常，Heap 稳定在 50MB 以下。

---

### Phase 2：创建入口文件（1h）

| # | 任务 | 文件 | 内容 |
|---|------|------|------|
| 2.1 | 新建 entries 目录 | `src/entries/` | 存放所有页面入口 |
| 2.2 | App 壳入口 | `src/entries/shell.ts` | 仅 App 壳（SidebarNav + KanbanHeader + RouterView），不含页面组件 |
| 2.3 | 仪表板入口 | `src/entries/dashboard.ts` | shell + DashboardView |
| 2.4 | 看板入口 | `src/entries/kanban.ts` | shell + KanbanView |
| 2.5 | 执行入口 | `src/entries/execution.ts` | shell + ExecutionView |
| 2.6 | 对话入口 | `src/entries/chat.ts` | shell + IntelligenceChatView |
| 2.7 | 终端入口 | `src/entries/terminal.ts` | shell + AgentTerminalView |
| 2.8 | 其他入口 | `src/entries/onboarding.ts`<br>`src/entries/settings.ts` 等 | 按需，每页面一个入口 |

每个入口文件结构：

```typescript
// src/entries/dashboard.ts — 示例
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from '../App.vue'
import DashboardView from '../views/DashboardView.vue'
import zh from '../locales/zh.json'
import en from '../locales/en.json'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', name: 'dashboard', component: DashboardView },
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})

const i18n = createI18n({ legacy: false, locale: 'zh', messages: { zh, en } })
const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')
```

**验收**：所有入口文件编译通过。执行 `npx vite build` 无报错。

---

### Phase 3：配置多入口构建（1h）

| # | 任务 | 文件 | 内容 |
|---|------|------|------|
| 3.1 | 多入口配置 | `vite.config.ts` | `build.rollupOptions.input` 指向所有入口 |
| 3.2 | HTML 注入 | `vite.config.ts` 或各入口 | 使用 `@vitejs/plugin-legacy` 或手写多 HTML |
| 3.3 | Code splitting | `vite.config.ts` | `output.manualChunks` 分离 vue/pinia/router 为公共 chunk |

```typescript
// vite.config.ts 关键配置
build: {
  rollupOptions: {
    input: {
      dashboard: 'src/entries/dashboard.ts',
      kanban: 'src/entries/kanban.ts',
      execution: 'src/entries/execution.ts',
      chat: 'src/entries/chat.ts',
      terminal: 'src/entries/terminal.ts',
      onboarding: 'src/entries/onboarding.ts',
      settings: 'src/entries/settings.ts',
    },
    output: {
      manualChunks: {
        vue: ['vue', 'vue-router', 'pinia', 'vue-i18n'],
        icons: ['lucide-vue-next'],
      },
    },
  },
},
```

**验收**：`npx vite build` 成功，`dist/` 下产生多个 chunk 文件，公共 chunk `vue-[hash].js` 被所有页面共享。

---

### Phase 4：HTML 入口（0.5h）

| # | 任务 | 文件 | 内容 |
|---|------|------|------|
| 4.1 | 创建每页面 HTML | `dashboard.html` 等 | 或用一个 `index.html` + `historyApiFallback` |
| 4.2 | SPA fallback | 后端 / Nginx | 所有路由请求返回对应 HTML |

如果使用 SPA 模式（推荐）：保持一个 `index.html`，路由由 Vue Router 管理。多入口仅用于 chunk 分离，不影响 URL 结构。

**验收**：浏览器打开 `http://localhost:15180/dashboard.html` 可正常访问。

---

### Phase 5：路由整合（1h）

| # | 任务 | 文件 | 内容 |
|---|------|------|------|
| 5.1 | App 壳保持 | `App.vue` | 保持不变，带 `<router-view />` |
| 5.2 | 路由懒加载 | `router/index.ts` | 确保每个页面是 `() => import(...)` 懒加载 |
| 5.3 | **关键**：壳与页面分离 | `router/index.ts` | 壳组件不 import 任何页面组件 |
| 5.4 | 移除 WS 在壳中的调用 | `App.vue` | `useKanbanWS().connect()` 移到页面组件 `onMounted` |

**验收**：路由切换正常，不同页面加载对应 chunk。Chrome DevTools Network 显示独立 JS 文件加载。

---

### Phase 6：生产构建验证（1h）

| # | 任务 | 预期结果 |
|---|------|---------|
| 6.1 | `npx vite build` | 无报错，多个 JS chunk |
| 6.2 | `npx vite preview` | 启动生产预览 |
| 6.3 | 打开每个页面 | 各页面正常渲染 |
| 6.4 | Heap 监控（`?debug=1`） | 每个页面 Heap 稳定在 30-60MB |
| 6.5 | 页面切换 10 次 | Heap 不单调增长，GC 回收旧页面内存 |
| 6.6 | 聊天功能 | SSE 流正常，Agent 执行正常 |
| 6.7 | 看板功能 | fetchModules 正常，KanbanBoard 渲染正常 |
| 6.8 | 长时间运行 | 挂机 30 分钟，Heap 不增长 |

**验收**：所有页面 Heap 稳定，页面切换无泄漏，30 分钟挂机无 OOM。

---

### Phase 7：回退和清理（0.5h）

| # | 任务 | 内容 |
|---|------|------|
| 7.1 | 删除旧 `main.ts`（备份已保留） | 新入口替代 |
| 7.2 | 恢复 `index.html` Google Fonts 移除 | 已在源文件中移除 |
| 7.3 | 更新 `CLAUDE.md` | 记录多入口架构变更 |

---

## 验收测试矩阵

| 测试 | 方法 | 通过标准 |
|------|------|---------|
| Dev 模式 | `npx vite --port 15177` | 页面正常，Heap < 50MB |
| 生产构建 | `npx vite build` | 无报错，多 chunk 输出 |
| 预览服务 | `npx vite preview --port 15181` | 所有页面可访问 |
| 仪表板 | 打开页面 | Heap 稳定 |
| 看板 | 切换到看板 | KanbanBoard 正常渲染 |
| 对话 | 发送消息 | SSE 流正常 |
| 页面切换 | 连续切换 10 次 | Heap 不单调增长 |
| 长时间挂机 | 挂机 30 分钟 | 无 OOM |
| 后端 API | 聊天/看板/终端 | 所有 API 正常响应 |

---

## 风险

| 风险 | 概率 | 缓解 |
|------|------|------|
| 多入口仍 OOM | 低（Dev 已验证模块隔离有效） | 方案 B（换 esbuild） |
| Code splitting 配置错误 | 中 | Phase 3 仔细验证 chunk 输出 |
| 路由懒加载与多入口冲突 | 低 | 保持 SPA 架构，仅 chunk 分离 |
| 公共 chunk 过大 | 低 | `manualChunks` 精细拆分 |

---

## 总工作量

**4-5 小时**（不含方案 B/C 备选）。

核心改动：新增 6-8 个入口文件 + `vite.config.ts` 15 行配置。不修改任何 Vue 组件、Store、样式。
