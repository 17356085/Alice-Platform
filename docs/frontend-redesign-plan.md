# Alice Studio 前端视觉重构方案

> 版本 v1.0 | 2026-07-12
> 依据: Figma Make 设计稿 (Design AI Platform UI) + 现有代码调研 (aitest/web)
> 范围: 仅前端 (aitest/web/src)，不改动后端代码
> 原则: 复用现有 API、不臆测接口、Mock 数据明确标注 TODO

## 0. 现状基线（调研结论摘要）

现有前端已经是 React 18 + TS + Vite + shadcn/ui + Tailwind + Zustand + react-router-dom，
技术栈与 Figma 设计稿一致，不存在跨框架迁移问题。17 个 View 已经按 Figma 的页面结构建好了骨架，
真正要做的是"视觉换肤 + 补全占位页 + 侧边栏改版"，不是从零重建。

### 样式体系现状（3 层混杂，需要统一到 shadcn+Tailwind）

| 层级 | 占比 | 代表页面 |
|---|---|---|
| 旧体系 `.alice-*` 自定义 class | ~15% | ProjectsView (Dashboard) |
| 过渡期内联 `<style>` + `var(--*)` | ~25% | ExecutionView, LiveAgentGraph, TerminalPanel |
| 新体系 shadcn/ui + Tailwind utility | ~60% | RunInspectorView, ArtifactsView, ObservabilityView, BuildView, GlobalRunsView |

### 主题系统现状（存在冲突，本次一并解决）

`main.tsx` 同时引入 `tokens.css`（定义 `alice`/`aoko`/`soujuurou`）和 `themes/all.css`
（定义 `default`/`aoko`/`soujuurou`），两套变量并存。已确认：**统一使用一套主题系统**，
以 `tokens.css` 的 Alice/Aoko/Soujuurou 三态命名为准（`all.css` 里的 `default` 需要改名对齐或废弃）。

### 后端 API 支持情况（16 个业务域逐一核实，禁止臆测）

| 业务域 | 状态 | 说明 |
|---|---|---|
| Dashboard | ✅ 已支持 | `/api/v1/kpi/summary`, `/api/v1/kpi/operational`, `/api/v1/agents/list`, `/api/v1/registry`, `/api/v1/observability/snapshot` |
| Workflow Builder | ✅ 已支持 | `/api/v1/workflows` CRUD + publish/validate/debug |
| Execution Center | ✅ 已支持 | `/api/v1/kanban/sop/start`, `/api/v1/runs`, `/api/v1/kanban/phases/{module}`, `/api/v1/agents/run` |
| Kanban Board | ⚠️ 部分支持 | 查询接口齐全；拖拽移动 phase 缺 POST/PUT 端点，需要后端补充或前端先做乐观更新 |
| Run Inspector | ✅ 已支持 | `/api/runs/{run_id}/inspector`, `/timeline`, `/report`，`/api/v1/kpi/timeline/replay/{run_id}` |
| Reports | ✅ 已支持 | `/api/v1/kpi/product`, `/api/reports`, `/api/v1/bugs/list`, `/api/v1/bugs/trends` |
| Gap Discovery | ❌ 无支持 | 未找到 `/api/gaps` 类端点，需要后端新增 |
| Memory Explorer | ⚠️ 部分支持 | 只有 `/api/debug/memory` 调试接口，缺业务层 Memory Block CRUD/搜索，需要后端新增 |
| Knowledge Base | ❌ 无支持 | `aitest/knowledge/` 有实现但未暴露 REST API，需要后端新增 |
| Knowledge Graph | ❌ 无支持 | 无图数据接口，需要后端新增 |
| Artifacts | ✅ 已支持 | `/api/v1/kpi/artifacts/{project_id}` 系列，含下载、血缘、全量列表 |
| Intelligence Chat | ✅ 已支持 | `/api/v1/chat/sessions` 系列，SSE 流式 |
| Observability | ✅ 已支持 | `/api/v1/observability/*` 四个端点 |
| Run History | ✅ 已支持 | `/api/v1/runs`（列表+过滤），`/api/history` |
| Settings | ⚠️ 部分支持 | Provider/Environment/Secret/Billing 已有 CRUD；主题/语言目前是本地存储，无需后端 |
| Agent Detail | ✅ 已支持 | `/api/v1/registry`, `/api/v1/agents/list`, `/api/v1/agents/status/{module}` |

**结论**：13/16 业务域后端已就位，3 个域（Gap Discovery、Knowledge Base、Knowledge Graph）
及 Kanban 拖拽落库、Memory 业务层需要后端排期。这些页面本次先用 Mock 数据实现视觉，
所有 Mock 处会用 `// TODO(backend): 需要 XXX 接口` 明确标注，不假装已经对接。

---

## 1. 主题系统统一方案

**目标文件**: `aitest/web/src/styles/tokens.css`（保留，作为唯一真源）
**废弃/合并**: `aitest/web/src/styles/themes/all.css`（`default` 主题下的变量差异需人工比对后合并进
`tokens.css` 的 `alice` 分支，若有冲突以 Figma 设计稿的 Cyan Magic (#22d3ee) + Moonlight Gold (#f0c040)
+ Night Sky (#080c14) 为准，因为这与 `tokens.css` 现有 Alice 主题已高度一致）

改动步骤：
1. 核对 `all.css` 里 `default`/`aoko`/`soujuurou` 与 `tokens.css` 里 `alice`/`aoko`/`soujuurou`
   的变量差异（逐条 diff，不假设一致）
2. 以 `tokens.css` 为唯一定义源，删除 `all.css` 中的重复/冲突定义
3. `main.tsx` 中移除 `import './styles/themes/all.css'`
4. 全局搜索 `data-theme="default"` 引用，统一改为 `data-theme="alice"`
5. 搜索所有页面里直接写死的 Tailwind 调色板类（如 Figma 稿中的 `text-cyan-400`、`bg-emerald-400/10`），
   替换为语义 token 类（`text-primary`、`bg-success/10` 等），确保主题切换时颜色跟随变量变化

---

## 2. 侧边栏导航重构（7 项扁平 → 6 分组 16 页）

**目标文件**: `aitest/web/src/components/SidebarNav.tsx`

现有结构（7 项扁平）：
```
Dashboard, Workflow, Execution, Memory, Knowledge, Tools, History
```

改为 Figma 设计稿的 6 分组结构：
```
CORE         Dashboard
RUN          Workflow / Execution / Kanban / Run Inspector
QUALITY      Reports / Gap Discovery
KNOWLEDGE    Memory / Knowledge Base / Knowledge Graph / Artifacts
INTELLIGENCE Intelligence Chat
MONITOR      Observability / Run History
底部固定      Settings
```

路由映射（对齐现有 `App.tsx` 里已注册的路由，不新增/不猜测路径）：

| 分组 | 页面 | 路由 |
|---|---|---|
| CORE | Dashboard | `/dashboard` |
| RUN | Workflow | `/projects/:id/build` |
| RUN | Execution | `/projects/:id/run/execute` |
| RUN | Kanban | `/projects/:id/run/kanban` |
| RUN | Run Inspector | `/projects/:id/runs/:runId` |
| QUALITY | Reports | `/projects/:id/quality/reports` |
| QUALITY | Gap Discovery | `/projects/:id/quality/gaps` |
| KNOWLEDGE | Memory | (现无独立路由，需要新增 `/projects/:id/assets/memory`，前端路由层新增，不涉及后端) |
| KNOWLEDGE | Knowledge Base | `/projects/:id/assets/knowledge` |
| KNOWLEDGE | Knowledge Graph | `/projects/:id/assets/graph` |
| KNOWLEDGE | Artifacts | `/projects/:id/assets/artifacts` |
| INTELLIGENCE | Intelligence Chat | `/projects/:id/chat` |
| MONITOR | Observability | `/projects/:id/observability` |
| MONITOR | Run History | `/runs` |
| 底部 | Settings | `/settings` |

**注意**：Memory Explorer 目前在 `App.tsx` 路由表里没有独立入口（现有 `SidebarNav` 里的 "Memory"
指向的路径需要在现有代码里核实后再定，不能凭 Figma 稿猜测）。这是实施阶段第一件要做的核实工作。

分组视觉参考 Figma 稿：分组标题用 `text-[9px] font-semibold uppercase tracking-[0.12em]`
弱化处理，配合现有 `NavBtn` 组件的 active/hover 样式，改动仅是加一层分组容器，不改变按钮组件本身。

---

## 3. 16 页面逐一重构计划

图例：**[改视觉]** 仅换肤，数据逻辑不动 / **[补功能]** 需要补充交互逻辑 / **[待后端]** Mock 数据先行

### Phase 1 — 核心页面（优先级最高，用户日常主路径）

**3.1 Dashboard** (`views/global/ProjectsView.tsx`) — [改视觉]
- 现状：`.alice-*` 自定义 class，数据硬编码（agents/recentRuns mock）
- 改造：迁移到 Tailwind + shadcn Card，样式对齐 Figma 稿的 StatCard/AgentCard 网格布局
- 数据：`/api/v1/kpi/summary`、`/api/v1/kpi/operational`、`/api/v1/agents/list` 已支持，
  替换掉现有硬编码的 `agents`/`recentRuns` 常量为真实请求
- 保留：现有的 "Execution in progress" banner 交互逻辑

**3.2 Execution Center** (`views/project/run/ExecutionView.tsx`) — [改视觉] + [补功能]
- 现状：内联 `<style>` + `var(--*)`，存在 `phase_status` 数据模型未对齐的技术债（L80）
- 改造：内联样式抽取为 Tailwind utility class，SOP Stepper 圆点进度对齐 Figma 稿视觉
- 技术债处理：先修复 `phase_status`（string→bool map）与 `completed_phases`（数值索引）的对齐问题，
  这是功能 bug 不是视觉问题，必须先修，否则换肤后进度条仍然错
- 数据：`/api/v1/kanban/sop/start`、`/api/v1/kanban/phases/{module}` 已支持

**3.3 Run Inspector** (`views/project/run/RunInspectorView.tsx`) — [改视觉]
- 现状：已是 shadcn+Tailwind 体系，680 行完整实现，8 个 KPI 卡片 + 7 个 Tab
- 改造：仅需视觉微调对齐 Figma 稿的 KPI 卡片间距/圆角/配色，Tab 结构、Timeline、Agent Calls
  等交互逻辑均已完整，不动
- 数据：已完整对接 `/api/runs/{run_id}/inspector` 等接口，无需改动

### Phase 2 — 质量分析

**3.4 Reports** (`views/project/quality/ReportsView.tsx`) — [改视觉] + [补功能]
- 现状：仅占位（3 个统计卡 + 空状态），技术债
- 改造：补全为 Figma 稿的"通过率/覆盖率/缺陷数 KPI + 最近测试运行表格 + Top Failing Tests"
- 数据：`/api/v1/kpi/product`、`/api/reports`、`/api/v1/bugs/list`、`/api/v1/bugs/trends` 已支持，
  之前是占位是因为没接，接口是有的，本次要把这些接上

**3.5 Gap Discovery** (`views/project/quality/GapDiscoveryView.tsx`) — [改视觉]
- 现状：`.filter-chip`/`.btn-mini` 内联样式，但已用真实 `useGapScanner` hook 完整实现
- 改造：内联样式改为 shadcn Badge + Tailwind，卡片布局对齐 Figma 稿的严重程度分色（HIGH/MED/LOW）
- 数据：已对接 `/api/v1/gap-scanner/*`，不动数据层

**3.6 Kanban Board** (`views/project/run/KanbanView.tsx` + `components/KanbanBoard.tsx`) — [改视觉] + [待后端]
- 现状：Tailwind + Zustand + WS 已完整实现拖拽
- 改造：视觉对齐 Figma 稿的 9 列布局、卡片配色
- **待后端**：拖拽后的 phase 变更目前没有对应 POST/PUT 落库端点，需要确认现有拖拽是否只是前端乐观更新、
  刷新后是否会还原——这一点需要先跟你核实现有行为，而不是假设它已经落库

### Phase 3 — 知识管理

**3.7 Memory Explorer** — [待后端] 新建页面
- 现状：现有代码库中**没有找到**对应的 Memory Explorer View 文件，需要先核实是否确实不存在
  （不能假设，需要在实施时用 Glob 再次确认）
- 数据：后端只有 `/api/debug/memory` 调试接口，业务层 Memory Block CRUD/搜索/tag 需要后端新增，
  本页面先用 Mock 数据实现视觉（对齐 Figma 稿的 episodic/semantic/procedural 三色分类卡片）

**3.8 Knowledge Base** (`views/project/assets/KnowledgeView.tsx`) — [改视觉] + [待后端]
- 现状：仅占位（3 个统计卡 + 空状态）
- **待后端**：Knowledge Base 的 collections/documents 列表无 REST API（`aitest/knowledge/` 有实现
  但未暴露），本次先用 Mock 数据渲染 Figma 稿的 Collections 表格 + Recent Additions 列表，
  接口就位后再替换

**3.9 Knowledge Graph** (`views/project/assets/KnowledgeGraphView.tsx`) — [改视觉] + [待后端]
- 现状：已有 SVG force-directed 可视化，但节点坐标硬编码，缩放/重置按钮无实际功能
- **待后端**：无图数据接口，节点/边仍用 Mock 数据
- 改造：优先修复缩放/重置的交互 bug（这是功能缺失不是视觉问题），视觉对齐 Figma 稿配色

**3.10 Artifacts** (`views/project/assets/ArtifactsView.tsx`) — [改视觉]
- 现状：427 行完整实现，shadcn Sheet + Card + ScrollArea
- 改造：仅视觉微调对齐 Figma 稿的卡片网格、类型图标配色，交互逻辑（搜索/过滤/预览/下载）不动
- 数据：已完整对接 `/api/v1/kpi/artifacts/*`

**3.11 Agent Detail** (`views/project/assets/AgentDetailView.tsx`) — [改视觉]
- 现状：完整实现，Badge/Card/Progress
- 改造：视觉对齐 Figma 稿的 Overview/Tools/Runs 三 Tab 布局
- 数据：Zustand（kanban modules + timeline events），已对接

**3.12 Agent Terminal** (`views/project/assets/AgentTerminalView.tsx`) — [改视觉]
- 现状：213 行完整实现，WS 连接
- 改造：视觉对齐 Figma 稿的终端配色（等宽字体、日志分级颜色）
- 数据：`/api/v1/terminal/ws` 已对接

### Phase 4 — 智能交互与构建

**3.13 Intelligence Chat** (`views/cross-cutting/IntelligenceChatView.tsx`) — [改视觉]
- 现状：202 行完整实现，Zustand + SSE
- 改造：视觉对齐 Figma 稿的消息气泡、工具指示器样式
- 数据：`/api/v1/chat/sessions/*` 已完整对接

**3.14 Workflow Builder** (`views/project/build/BuildView.tsx`) — [改视觉]
- 现状：完整实现 CRUD + 节点画布（原生 HTML5 DnD）
- 改造：视觉对齐 Figma 稿的左侧表单 + 右侧节点图布局，节点拖拽逻辑不动
- 数据：`/api/v1/workflows/*` 已完整对接

**3.15 Strategy Planner** (`views/project/build/StrategyPlannerView.tsx`) — [补功能]
- 现状：仅占位
- 改造：补全为 Figma 稿的风险评分公式展示 + 模块选择
- 数据：未在后端调研中发现专用接口，需要进一步核实（本次先按 Mock 处理，标注 TODO）

### Phase 5 — 监控与全局

**3.16 Observability** (`views/cross-cutting/ObservabilityView.tsx`) — [改视觉]
- 现状：228 行完整实现，4 Tab + 10s 轮询
- 改造：仅视觉微调对齐 Figma 稿的进度条、GC 分代展示
- 数据：`/api/v1/observability/*` 已完整对接

**3.17 Run History** (`views/global/GlobalRunsView.tsx`) — [改视觉]
- 现状：shadcn Card + Tailwind，已对接 `/api/runs/list`
- 改造：仅视觉微调对齐 Figma 稿的表格行样式、状态徽章配色

**3.18 Settings** (`views/global/SettingsView.tsx`) — [改视觉]
- 现状：完整实现，Zustand settings store
- 改造：视觉对齐 Figma 稿的主题选择卡片（Alice/Aoko/Soujuurou 三态切换器）+ Provider 选择卡片布局
- 数据：Provider/Environment/Secret 已有 CRUD，主题/语言走本地存储，不需要后端改动

---

## 4. 共享组件改造清单

| 组件 | 现状 | 改造 |
|---|---|---|
| `StatCard`（需新建或从 Figma 稿迁移） | Dashboard 里直接手写 | 抽成独立共享组件，供 Dashboard/Reports/RunInspector 复用 |
| `AgentCard`（同上） | Dashboard 里直接手写 | 抽成独立共享组件 |
| `StatusBadge`（同上） | 各页面各自实现状态徽章 | 统一抽成共享组件，替换所有页面里重复的状态色映射逻辑 |
| `KanbanBoard.tsx` | 已存在，Tailwind 实现 | 仅视觉微调，不改交互 |
| `LiveAgentGraph.tsx` | 内联 `<style>` + SVG | 改为 Tailwind class，配色对齐 Figma 稿 WorkflowGraph |
| `TerminalPanel.tsx` | xterm.js 集成 | 仅调整 xterm 主题配色对齐 Figma 稿终端配色 |
| `SwimlaneTimeline.tsx` | 280 行完整实现 | 仅视觉微调 |
| `ChatSidebar.tsx` | 已存在 | 视觉对齐 Figma 稿会话列表样式 |
| `ModuleDetailSheet.tsx` | 已存在 | 视觉对齐 |

---

## 5. 实施顺序建议

1. **主题系统统一**（第 1 节）— 所有页面视觉改造的前提，必须先做
2. **共享组件抽取**（第 4 节）— StatCard/AgentCard/StatusBadge，减少后续页面改造的重复工作
3. **侧边栏重构**（第 2 节）— 导航结构变化影响全局，需要与用户核实 Memory 路由缺失问题后再动手
4. **Phase 1-5 页面改造**（第 3 节）— 按用户指定顺序或本方案的 Phase 顺序推进
5. **每个页面改造后**：运行 `npm run typecheck`、`npm run build` 验证，涉及交互的页面手动 smoke test

---

## 6. 待用户二次确认的事项（本方案暂未擅自决定）

1. Memory Explorer 页面在现有代码库中是否真实不存在（需要 Glob 复核，若存在则改为"改视觉"而非"新建"）
2. Kanban 拖拽当前落库行为的真实情况（乐观更新 or 已落库），决定是否需要后端补充 API
3. Strategy Planner 是否有计划中但未被本次调研发现的后端接口
4. `themes/all.css` 与 `tokens.css` 的变量 diff 结果如有冲突，以哪个为准（默认建议以 Figma 稿颜色为准，但需确认）
