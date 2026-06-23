# 测试生命周期管理器 (TLO) — 开发计划书

> **版本**: v1.0 | **日期**: 2026-06-23 | **状态**: 待评审
>
> 基于 AITest Platform v0.5 + Aperant 架构评审 + ChatGPT 产品定位建议 → 综合输出

---

## 一、产品定位

### 1.1 不是什么

| 不是 | 原因 |
|------|------|
| 另一个 Aperant | Aperant 解决软件开发编排，TLO 解决测试生命周期编排 |
| 另一个 AI 编程工具 | 产物是测试结果/报告，不是代码 |
| 泛化 Agent 平台 | 聚焦测试领域，不做通用 Agent 市场 |

### 1.2 是什么

> **AI TestOps 平台 — 测试生命周期管理器 (Testing Lifecycle Orchestrator)**

核心差异:

- Aperant: 需求 → Code (产物: 代码)
- TLO: 需求 → Test Execution (产物: 测试结果/截图/日志/缺陷分析/报告)

### 1.3 与 Aperant 的流水线对照

| Aperant | TLO | 差异 |
|---------|-----|------|
| Spec | Test Requirement | TLO 识别测试对象 + 测试目标 |
| Planner | Test Strategy | TLO 产出 Smoke/Regression/Boundary/Negative/Security 策略 |
| Coder | Test Executor | TLO 操控 Browser/API/Selenium，不写业务代码 |
| QA (Pass/Fail) | Failure Analysis | TLO 更深入: 截图→DOM→Console→Network→LLM→根因 |
| Merge | Report | TLO 产出 Markdown/HTML/Allure，不合并代码 |

### 1.4 差异化优势

1. **测试生命周期管理** — 目前开源项目(含 Aperant)聚焦执行单项任务，TLO 覆盖完整生命周期
2. **失败深度分析** — Aperant QA 只判断 Pass/Fail，TLO 走截图→DOM→Network→LLM 全链路根因
3. **治理闭环** — 7 审计器 + EventBus + KPI，Aperant 无此层
4. **企业测试团队适配** — 贴合部门业务场景(鞍集涂源管理系统)

---

## 二、当前基线评估

### 2.1 资产盘点 (2026-06-23 核实)

| 资产 | 数量 | 状态 |
|------|------|------|
| 测试文件/函数 | 129 files / 1,082 tests | ✅ 12 模块全覆盖 |
| Python 模块 | ~95 files | ✅ 全量 import 通过 |
| CLI 命令 | 22 个 | ✅ sop/dev-sop/trace/kpi 等 |
| API 端点 | 30+ | ✅ `/health` `/api/audit/*` `/api/trace/*` `/api/kpi/*` |
| Web 页面 | 4 个 | ✅ dashboard/chat/trace/governance |
| RAG 知识库 | 5 collections / 1,115 docs | ✅ ChromaDB |
| 审计器 | 7 个 | ✅ state/SOP/cost/safety/KPI/online/scheduled |
| Agent 定义 | 21 个 | ✅ 8 测试 + 9 开发 + 4 通用 |
| Skill | 56 个 | ✅ 24 测试 + 32 开发 |
| 治理事件 | 6,301 条 | ✅ EventBus 30天 |

### 2.2 当前架构简图

```
CLI / Web UI
    ↓
LangGraph StateGraph (checkpoint + HITL)
    ↓
AgentLoop → LLM Provider (Anthropic/DeepSeek/Google)
    ↓
Skill Executor → RAG (ChromaDB 5 collections)
    ↓
Trace (JSONL) → Cost Auditor
    ↓
EventBus → 7 Auditors → KPI → Governance Dashboard
```

### 2.3 已知短板

| 问题 | 严重度 | 状态 |
|------|--------|------|
| SOP_STATUS 数据断连 (12 文件全空) | P0 | 需修复 |
| Trace 100% 合成数据 (19 entries, $0 cost) | P0 | 需真实运行 |
| KPI 趋势全红 (drift ↑366%) | P1 | 需排查根因 |
| 55 未跟踪审计文件 | P1 | 需 gitignore |
| Page Object 缺失 (0 个 page_*.py) | P2 | 长期重构 |
| 不可视化测试生命周期流转 | — | TLO 核心建设项 |

---

## 三、目标架构

### 3.1 分层架构

```
┌──────────────────────────────────────────────────────┐
│              Web UI (Kanban + Dashboard + Trace)       │  🆕 可视化管理层
├──────────────────────────────────────────────────────┤
│           Lifecycle Orchestrator                       │  🆕 生命周期引擎
│  ┌──────────┬──────────┬──────────┬──────────────┐   │
│  │ Spec     │ QA Loop  │ Worktree │ Kanban       │   │
│  │ Pipeline │ (fix→    │ Manager  │ State Machine│   │
│  │ (4-stage)│  re-verify)│         │              │   │
│  └──────────┴──────────┴──────────┴──────────────┘   │
├──────────────────────────────────────────────────────┤
│           LangGraph StateGraph (已有)                  │
│    8 Agent SOP + 9 Agent Dev + HITL + Checkpoint       │
├──────────────────────────────────────────────────────┤
│           Governance Layer (已有，增强)                │
│    7 Auditors + EventBus + KPI Collector + Trace       │
├──────────────────────────────────────────────────────┤
│           Knowledge Layer (已有，扩展)                 │
│    ChromaDB RAG → + 语义图谱 (自动知识提取)           │
├──────────────────────────────────────────────────────┤
│           Infrastructure (已有)                        │
│    MCP Protocol │ Task Queue │ Agent Runner            │
└──────────────────────────────────────────────────────┘
```

### 3.2 测试生命周期 8 阶段

```
┌──────────────┐
│ 1. 需求分析   │  Requirement Analyst
│               │  理解需求 → 识别测试对象 → 生成测试目标
└──────┬───────┘
       ↓
┌──────────────┐
│ 2. 策略制定   │  Test Strategy Agent
│               │  Smoke / Regression / Boundary / Negative / Security
└──────┬───────┘
       ↓
┌──────────────┐
│ 3. 用例设计   │  Test Designer (🆕 4-stage Spec Pipeline)
│               │  Gatherer → Researcher → Writer → Critic
└──────┬───────┘
       ↓
┌──────────────┐
│ 4. 自动化开发 │  Automation Developer (🆕 Worktree 隔离)
│               │  脚本生成 → Worktree 验证 → 合并
└──────┬───────┘
       ↓
┌──────────────┐
│ 5. 环境准备   │  Environment Preparer (🆕)
│               │  数据准备 / 账号检查 / 浏览器就绪
└──────┬───────┘
       ↓
┌──────────────┐
│ 6. 测试执行   │  Execution Agent
│               │  Browser / API / Selenium / BrowserUse
└──────┬───────┘
       ↓
┌──────────────┐
│ 7. 失败分析   │  Failure Analyst (🆕 深度分析)
│               │  截图 → DOM → Console → Network → LLM → 根因
└──────┬───────┘
       ↓
┌──────────────┐
│ 8. 报告生成   │  Report Agent
│               │  Markdown / HTML / Allure / Excel (每页面)
└──────┬───────┘
       ↓
┌──────────────┐
│ 🔄 回归推荐   │  Regression Advisor (🆕)
│               │  基于代码变更 + 历史缺陷 → 推荐回归范围
└──────────────┘
```

### 3.3 Agent 重命名方案

| 旧名 (当前) | 新名 (TLO) | 职责聚焦 |
|------------|-----------|---------|
| requirement-agent | **Requirement Analyst** | 需求理解 + 测试对象识别 |
| test-design-agent | **Test Strategy Agent** | 测试策略生成 (5 类) |
| (🆕) | **Test Designer** | Spec Pipeline: Gather→Research→Write→Critic |
| automation-agent | **Automation Developer** | 脚本生成 + Worktree 验证 |
| (🆕) | **Environment Preparer** | 数据/账号/浏览器就绪 |
| execution-agent | **Execution Agent** | Browser/API/Selenium 执行 |
| bug-analysis-agent | **Failure Analyst** | 截图→DOM→Network→LLM 根因 |
| report-agent | **Report Agent** | 多格式报告输出 |
| (🆕) | **Regression Advisor** | 变更驱动的回归范围推荐 |

---

## 四、UI/UX 设计规范

> 借鉴 Aperant 设计系统，适配 TLO Web 平台定位。不做 Electron 桌面壳，但保留未来扩展可能。

### 4.1 设计原则

| 原则 | 说明 |
|------|------|
| **单页应用 (SPA)** | 一个 Shell 承载所有视图，无页面跳转感 |
| **Sidebar 导航** | 固定左侧导航栏，视图切换不刷新 |
| **卡片化信息** | 模块/任务/报告统一用卡片呈现 |
| **暗色/亮色主题** | CSS 变量驱动，一键切换 |
| **渐进增强** | Phase 1 纯 HTML/CSS/JS → Phase 2 Vue 3 SPA |

### 4.2 布局结构 (借鉴 Aperant App.tsx)

```
┌──────────┬──────────────────────────────────────────┐
│          │  Project Tab Bar (模块标签页，可拖拽排序)   │
│          ├──────────────────────────────────────────┤
│ Sidebar  │                                          │
│          │         主内容区域 (视图切换)               │
│  📋 看板  │   ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  ▶️ 执行  │   │  Card   │ │  Card   │ │  Card   │   │
│  📊 报告  │   │equipment│ │personnel│ │   lab   │   │
│  🔍 知识  │   └─────────┘ └─────────┘ └─────────┘   │
│  ⚙️ 设置  │                                          │
│          │                                          │
│  🌙 主题  │                                          │
└──────────┴──────────────────────────────────────────┘
```

### 4.3 视图定义

| 视图 | 图标 | 内容 | 来源 |
|------|------|------|------|
| **Kanban** | 📋 | 12 模块卡片按生命周期分列 (Pending→Planning→Executing→Analyzing→Completed) | 借鉴 Aperant KanbanBoard |
| **Execution** | ▶️ | 实时执行日志流 (SSE)，Agent 输出 + 截图 + 进度 | 借鉴 Aperant TerminalGrid (简化为日志面板) |
| **Reports** | 📊 | 测试报告列表 (Excel/Allure/HTML)，按模块 + 时间筛选 | 现有 report-agent 产出 + UI |
| **Knowledge** | 🔍 | RAG 知识库检索 + 语义搜索 + 已知问题浏览 | 现有 ChromaDB + 新搜索 UI |
| **Settings** | ⚙️ | Provider 配置 / 模块开关 / 审计阈值 / Agent 参数 | 现有 .env + UI |

### 4.4 设计令牌系统 (借鉴 Aperant globals.css)

完整迁移 Aperant 的 30+ CSS 变量体系，适配 TLO 品牌色。

```css
/* ═══════════════════════════════════════════════════════
   TLO Design Tokens — 借鉴 Aperant globals.css
   Phase 1: 单文件 tlo.html 内联
   Phase 2: 迁移到 Vue 3 SPA src/styles/tokens.css
   ═══════════════════════════════════════════════════════ */

:root {
  /* ── 基础表面 ── */
  --background: #f8f9fb;
  --foreground: #1a1a2e;
  --card: #ffffff;
  --card-foreground: #1a1a2e;
  --border: #e2e4e9;
  --input: #e2e4e9;
  --ring: #5b7fff;

  /* ── 品牌色 ── */
  --primary: #5b7fff;
  --primary-foreground: #ffffff;
  --secondary: #f0f1f5;
  --secondary-foreground: #1a1a2e;
  --muted: #f5f5f7;
  --muted-foreground: #6b7280;
  --accent: #eef0ff;
  --accent-foreground: #5b7fff;

  /* ── 语义色 ── */
  --success: #22c55e;
  --success-foreground: #ffffff;
  --success-light: #e6f9ed;
  --warning: #f59e0b;
  --warning-foreground: #1a1a2e;
  --warning-light: #fff8e6;
  --destructive: #ef4444;
  --destructive-foreground: #ffffff;
  --destructive-light: #fef0f0;
  --info: #3b82f6;
  --info-foreground: #ffffff;
  --info-light: #e8f2ff;

  /* ── Sidebar 专用 ── */
  --sidebar: #0f1420;
  --sidebar-foreground: #e2e4e9;
  --sidebar-active: #5b7fff;

  /* ── 圆角 (对齐 Aperant) ── */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* ── 阴影 (对齐 Aperant) ── */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.08);
  --shadow-focus: 0 0 0 3px rgba(91, 127, 255, 0.2);

  /* ── 字体 ── */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
               'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;

  /* ── 动画 ── */
  --animate-fade-in: fade-in 0.25s ease-out;
  --animate-slide-up: slide-up 0.25s ease-out;
}

/* ── 暗色主题 ── */
.dark {
  --background: #0b0b0f;
  --foreground: #e6e6e6;
  --card: #121216;
  --card-foreground: #e6e6e6;
  --border: #23262b;
  --input: #23262b;
  --ring: #818cf8;

  --primary: #818cf8;
  --primary-foreground: #0b0b0f;
  --secondary: #1a1a1f;
  --secondary-foreground: #e6e6e6;
  --muted: #1a1a1f;
  --muted-foreground: #868f97;
  --accent: #1e2040;
  --accent-foreground: #818cf8;

  --success: #4ebe96;
  --success-light: #1a2924;
  --warning: #d2d714;
  --warning-light: #262618;
  --destructive: #ff5c5c;
  --destructive-light: #2a1a1a;
  --info: #479ffa;
  --info-light: #1a2230;

  --sidebar: #0a0a10;
  --sidebar-foreground: #868f97;
  --sidebar-active: #818cf8;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.5);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.6);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.7);
  --shadow-focus: 0 0 0 2px rgba(129, 140, 248, 0.2);
}

/* ── 关键帧 ── */
@keyframes fade-in  { from { opacity: 0; } to { opacity: 1; } }
@keyframes slide-up { from { transform: translateY(8px); opacity: 0; }
                      to   { transform: translateY(0); opacity: 1; } }
@keyframes pulse-subtle { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
```

### 4.5 组件样式规范

**卡片 (Card)** — 所有信息容器统一使用:

```css
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.15s ease;
}
.card:hover { box-shadow: var(--shadow-md); }
```

**状态徽章 (Badge)** — 对齐 Aperant 的语义色体系:

| 状态 | 类名 | 背景 | 文字 |
|------|------|------|------|
| 成功/通过 | `.badge-ok` | `var(--success-light)` | `var(--success)` |
| 警告 | `.badge-warn` | `var(--warning-light)` | `var(--warning)` |
| 失败/错误 | `.badge-err` | `var(--destructive-light)` | `var(--destructive)` |
| 信息/运行中 | `.badge-info` | `var(--info-light)` | `var(--info)` |

**进度指示器 (PhaseProgressIndicator)** — 借鉴 Aperant:

```
┌──────────────────────────────────────────┐
│ equipment  ●━━━━●━━━━●━━━━○━━━━○  3/5    │
│            Plan  Design  Exec  Analyze  Done │
└──────────────────────────────────────────┘
```

### 4.6 Kanban 列定义 (TLO 测试生命周期)

| 列 | 含义 | 卡片状态 | 触发条件 |
|----|------|---------|---------|
| **Pending** | 待测试 | 未启动 | 模块初始状态 |
| **Planning** | 策略制定中 | Spec Pipeline 运行中 | Requirement Analyst 接管 |
| **Executing** | 测试执行中 | 实时进度 + Agent 日志 | Execution Agent 运行中 |
| **Analyzing** | 失败分析/QA Loop | 红灯/黄灯闪烁 | 测试失败触发 |
| **Completed** | 报告已生成 | 绿灯 | 全部通过 + Report 输出 |

卡片内容：模块名 + 页面数/用例数 + PhaseProgressIndicator + 最近执行时间 + 操作按钮。

### 4.7 响应式策略

| 断点 | Sidebar | 内容区 | Kanban 列 |
|------|---------|--------|-----------|
| ≥1280px | 固定 220px | 自适应 | 5 列 |
| 1024-1279px | 折叠为图标 | 自适应 | 3 列 + 横向滚动 |
| <1024px | 隐藏 (汉堡菜单) | 全宽 | 单列 + 下拉筛选 |

### 4.8 技术实现路线

| 阶段 | 技术栈 | 产出 |
|------|--------|------|
| **Phase 1** | 纯 HTML + CSS 变量 + vanilla JS | `aitest/server/static/tlo.html` (单文件 SPA) |
| **Phase 2** | Vue 3 + Vite + shadcn-vue + Radix Vue + Tailwind CSS v4 + Zustand | `aitest/web/` (独立前端工程) |
| **Phase 3 (可选)** | Electron 壳 + WebView | 桌面应用分发包 (Windows/macOS/Linux) |

> **Electron 暂缓原则**: 先完成 Web 版前后端全部能力并稳定运行，再评估是否需要 Electron 桌面壳。Phase 3 的触发条件：(1) 用户强需求离线使用，(2) 需要 OS 级文件系统访问，(3) 需要系统托盘/通知。在此之前不做 Electron。

### 4.9 与 Aperant UI 的差异清单

| Aperant 特性 | TLO 做法 | 原因 |
|-------------|---------|------|
| 11 个视图 (Kanban/Terminals/Roadmap/Ideation/Insights/GitHub Issues/...) | 5 个视图 (Kanban/Execution/Reports/Knowledge/Settings) | 聚焦测试场景 |
| xterm.js PTY 终端 | SSE 日志面板 + 代码高亮 | 不需要完整终端模拟 |
| Electron 壳 | 浏览器 Web 应用 | QA 工程师用浏览器 |
| 8 个主题 × 2 模式 | 2 个主题 (Light/Dark) | 演示足够，之后可扩展 |
| React + dnd-kit 拖拽 | Phase 1 原生 drag & drop API, Phase 2 VueUse | 技术栈对齐 |
| Tailwind CSS v4 + Radix UI | Phase 1 CSS 变量, Phase 2 Tailwind + shadcn-vue (Radix Vue 封装) | shadcn 是 Radix 的上层封装，Aperant 原生 Radix → TLO 用 shadcn-vue |

### 4.10 shadcn-vue 组件映射

> 选 shadcn-vue 理由: Aperant 底层用 **Radix UI**（无障碍原语）；shadcn = Radix 社区标准封装（copy-paste 模式，无 npm 黑盒）。React 版 shadcn/ui → Vue 3 版 shadcn-vue，同体系不同框架。

**TLO 核心 UI → shadcn-vue 组件对照:**

| TLO 区域 | shadcn-vue 组件 | Radix Vue 原语 |
|---------|----------------|---------------|
| Sidebar 导航 | `Sidebar` / `NavigationMenu` | `NavigationMenu` |
| Kanban 列 + 卡片 | `Card` (`CardHeader`/`CardContent`/`CardFooter`) + `ScrollArea` | — |
| 拖拽排序 | VueUse `useSortable` + `Sortable` | — |
| 任务详情弹窗 | `Dialog` / `Sheet` | `Dialog` |
| 状态徽章 | `Badge` (variant: success/warning/destructive/info) | — |
| 进度指示器 | `Progress` + 自定义 Step Indicator | `Progress` |
| 执行日志面板 | `Collapsible` + `ScrollArea` + `<pre>` | `Collapsible` |
| 主题切换 | `DropdownMenu` + `Switch` | `DropdownMenu` / `Switch` |
| 设置表单 | `Form` (vee-validate) + `Select` + `Input` + `Switch` | `Select` / `Switch` |
| Toast 通知 | `Toast` / `Sonner` | `Toast` |
| 数据表格 | `Table` + 自定义虚拟滚动 | — |
| 命令面板 Ctrl+K | `Command` (cmdk-vue) | — |
| 悬浮提示 | `Tooltip` / `HoverCard` | `Tooltip` / `HoverCard` |
| 模块标签页 | `Tabs` | `Tabs` |

**与 Aperant 技术栈对比:**

| 层 | Aperant | TLO Phase 2 |
|----|---------|-------------|
| 框架 | React 19 | Vue 3 (Composition API) |
| UI 原语 | Radix UI (React) | Radix Vue |
| 组件封装 | 自建 | shadcn-vue (社区标准化) |
| 样式 | Tailwind CSS v4 | Tailwind CSS v4 |
| 状态管理 | Zustand 5 | Pinia (Vue 生态标准) |
| 拖拽 | dnd-kit | VueUse `useSortable` |
| 终端 | xterm.js PTY | SSE + `<pre>` 高亮 |
| 主题 | 8×2=16 套 | 2 套 (Light/Dark)，token 可直接扩展 |

> **核心差异**: Aperant 在 Radix 之上自建组件层。TLO 用 shadcn-vue——同样的 Radix 底层，组件由社区维护、文档完善、主题系统开箱即用。TLO 的组件层比 Aperant 更标准化。

---

## 五、核心能力设计

### 5.1 Spec Pipeline (4 阶段测试设计)

借鉴 Aperant 的 `spec_gatherer → researcher → writer → critic`，适配测试领域:

```
Test Designer 内部流水线:

Gatherer        →  收集需求文档 + 页面截图 + API Schema + 历史缺陷
Researcher      →  风险分析: 识别高风险区域 + 边界条件 + 安全漏洞面
Writer          →  产出测试用例: 步骤 + 预期 + 优先级 + 数据 + 标签
Critic          →  用例评审: 重复检测 + 覆盖率缺口 + 可执行性验证
```

**实现**: 4 个 Skill (非 4 个 Agent)，由 `test-designer` Agent 串行调用。复用现有 `skill_executor.py`。

### 5.2 QA Loop (失败→修复→重验证)

借鉴 Aperant 的 `qa/reviewer.py → qa/fixer.py → qa/loop.py`:

```
测试失败
    ↓
Failure Analyst: 截图 + DOM diff + Console error + Network trace → 根因报告
    ↓
Automation Developer: 根据根因修复定位器/等待策略/测试数据
    ↓  (在 Worktree 中执行)
Execution Agent: 重跑失败用例
    ↓
    ├── 通过 → 合并修复回 script/ + 更新 RAG 知识库
    └── 失败 → 升级人工 + 创建 Bug Ticket
```

**实现**: `aitest/governance/qa_loop.py` — 新文件，编排失败→修复→重验证循环。集成现有 `bug-analysis-agent` + `automation-agent` + `execution-agent`。

### 5.3 Worktree 隔离

借鉴 Aperant 的 `core/worktree.py`:

```
Automation Developer 执行时:
  1. git worktree add .claude/worktrees/auto-<timestamp> (从当前分支)
  2. Agent 在工作树中生成/修改测试脚本
  3. Execution Agent 在工作树中运行验证
  4. 通过 → git merge 回原分支 + 删除工作树
  5. 失败 → 保留工作树供人工检查 + 记录日志
```

**实现**: `aitest/infra/worktree_manager.py` — 新文件，封装 git worktree 操作。集成到 `AgentLoop` 的 pre/post hooks。

### 5.4 失败深度分析

比 Aperant QA (仅 Pass/Fail) 更深入:

```
失败信号
    ↓
┌──────────────────────────────┐
│ 多维证据采集                   │
│  📸 截图 (全页 + 失败区域)     │
│  🌳 DOM snapshot (失败时刻)    │
│  📡 Console logs (JS errors)  │
│  🌐 Network trace (API 错误)  │
│  ⏱  Timeline (加载/渲染耗时)  │
└──────────┬───────────────────┘
           ↓
┌──────────────────────────────┐
│ LLM 根因分析                   │
│  • 定位器失效? (DOM changed)  │
│  • 时序问题? (race condition) │
│  • 数据问题? (test data stale)│
│  • 环境问题? (service down)   │
│  • 被测 Bug? (real defect)    │
└──────────┬───────────────────┘
           ↓
┌──────────────────────────────┐
│ 分类 + 建议                    │
│  🟢 自动化可修复 → QA Loop    │
│  🟡 需人工确认 → Ticket       │
│  🔴 被测缺陷   → Bug Report   │
└──────────────────────────────┘
```

**实现**: 增强 `bug-analysis-agent` 的 Skill，新增 `failure-evidence-collector` + `root-cause-analyzer` Skill。

### 5.5 Kanban 可视化管理

借鉴 Aperant 的 Kanban Board:

```
模块看板 (每个模块一张卡片):

┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Pending  │  │Planning │  │Executing  │  │Analyzing │  │Completed │
├─────────┤  ├─────────┤  ├──────────┤  ├──────────┤  ├──────────┤
│ workflow │  │  dcs    │  │equipment │  │personnel │  │  system  │
│          │  │  tank   │  │   lab    │  │  sales   │  │warehouse │
│          │  │         │  │production│  │          │  │          │
└─────────┘  └─────────┘  └──────────┘  └──────────┘  └──────────┘

点击卡片 → Task Detail:
  • Prompt (当前任务描述)
  • Timeline (执行时间线)
  • 截图/日志 (最新执行结果)
  • Agent 状态 (当前阶段 + 进度)
  • 操作按钮 (Run / Pause / Resume / Report)
```

**实现**: 
- Phase 1: 纯前端升级 — 在 `/governance` 页面加 Kanban 视图 (HTML/CSS/JS)
- Phase 2: 后端支持 — WebSocket 推送状态变更 + Zustand 状态管理 (如引入 Vue 3)

### 5.6 知识语义图谱

在 ChromaDB 基础上增加主动知识提取:

```
每次测试执行后:
  1. 提取新的定位策略 → "equipment 模块 dialog 用 el-dialog__wrapper 定位"
  2. 提取失败模式 → "Element Plus cascader panel 需要等待动画结束"
  3. 提取修复策略 → "menu-management 等待时间从 1s 改为 2s"
  4. 跨模块关联 → "此修复同样适用于 tank/alarm-config 的同模式问题"

存入 ChromaDB + 元数据关联图谱
  page_objects: {pattern, module, page, element_type, success_rate}
  known_issues: {pattern, modules_affected, fix_strategy, occurrence_count}
```

**实现**: Phase 2。新增 `aitest/knowledge/knowledge_extractor.py`，集成到 `AgentLoop` post-execution hook。

---

## 六、实施路线图

### Phase 1: 生命周期骨架 (Weeks 1-4)

**目标**: TLO 最小闭环可演示

| # | 任务 | 文件 | 估时 |
|---|------|------|------|
| 1.1 | **Agent 重命名 + 8 阶段定义** | `governance/agents/agent-definitions.yaml` 更新 | 4h |
| 1.2 | **Spec Pipeline (4-stage)** | `governance/skills/test-design/` 新增 gatherer/researcher/writer/critic | 12h |
| 1.3 | **QA Loop 编排器** | `aitest/governance/qa_loop.py` (新) | 16h |
| 1.4 | **Kanban UI (Phase 1: 静态)** | `aitest/server/static/governance.html` 扩展 | 12h |
| 1.5 | **Lifecycle State Machine** | `aitest/graphs/lifecycle_state.py` (新) | 8h |
| 1.6 | **P0 修复: SOP_STATUS 同步 + 真实 trace** | 回填数据 + 真实运行 3 条 SOP | 4h |

**产出**: 
- 8 阶段 Agent 定义就绪
- Test Designer 4 阶段流水线可用
- QA Loop 基本闭环 (失败→分析→修复→重跑)
- Kanban 页面显示模块生命周期状态
- SOP_STATUS 数据真实

### Phase 2: 隔离与知识 (Weeks 5-8)

| # | 任务 | 文件 | 估时 |
|---|------|------|------|
| 2.1 | **Worktree Manager** | `aitest/infra/worktree_manager.py` (新) | 12h |
| 2.2 | **Worktree 集成 AgentLoop** | `aitest/agent_runner.py` 增加 pre/post hooks | 8h |
| 2.3 | **失败深度分析增强** | governance/skills/diagnosis/ 新增 evidence-collector + root-cause | 16h |
| 2.4 | **知识自动提取器** | `aitest/knowledge/knowledge_extractor.py` (新) | 12h |
| 2.5 | **shadcn-vue UI 组件集成** | `aitest/web/` 初始化 + 按需添加 12+ 组件 | 16h |
| 2.6 | **Kanban UI (Phase 2: 交互)** | WebSocket 推送 + VueUse 拖拽流转 + shadcn Card/Badge/Dialog | 16h |
| 2.7 | **Regression Advisor Agent** | `governance/agents/` + `aitest/agents/regression_advisor.py` | 12h |

**产出**:
- Agent 在 Worktree 中安全修改测试脚本
- 失败分析输出多维证据 + 根因分类
- 每次执行自动提取知识到 ChromaDB
- Kanban 支持拖拽 + 实时刷新 (shadcn-vue Card + VueUse useSortable)
- 代码变更 → 回归范围推荐
- shadcn-vue 组件库集成 (12+ 组件), 设计令牌与 Tailwind CSS v4 完全对齐

### Phase 3: 协作与集成 (Weeks 9-12)

| # | 任务 | 估时 |
|---|------|------|
| 3.1 | **GitHub/GitLab Issue → 测试用例** | 16h |
| 3.2 | **PR → 自动触发关联模块回归** | 12h |
| 3.3 | **CI/CD 原生集成 (Jenkins/GitHub Actions)** | 12h |
| 3.4 | **Environment Preparer Agent** | 8h |
| 3.5 | **多模块并行执行** | 12h |
| 3.6 | **性能/压力测试集成 (可选)** | 16h |

---

## 七、关键决策记录

| # | 决策 | 选项 A | 选项 B | 选择 | 理由 |
|---|------|--------|--------|------|------|
| 1 | 知识图谱引擎 | Graphiti (Aperant 同款) | ChromaDB 扩展 | **ChromaDB** | 已有 1115 docs，迁移成本高 |
| 2 | Worktree 实现 | 复用 Aperant AGPL 代码 | 自建 | **自建** | AGPL 许可证冲突 |
| 3 | 前端框架 | 纯 HTML (当前) | Vue 3 SPA | **Phase 1 HTML → Phase 2 Vue 3** | 渐进增强，Phase 1 零构建部署，Phase 2 完整 SPA |
| 4 | QA Loop 编排 | LangGraph 子图 | 独立 Python 循环 | **LangGraph 子图** | 复用 checkpoint/HITL |
| 5 | Spec Pipeline | 4 个独立 Agent | 4 个 Skill | **4 Skill** | 同一 Agent 不同阶段，省 token |
| 6 | Electron 桌面应用 | 现在做 | 暂缓 (Phase 3 可选) | **暂缓** | 先完成 Web 版全能力，有离线/OS 级需求时再评估 |
| 7 | 产品名称 | AI TestOps Platform | Testing Lifecycle Orchestrator | **TLO** | 后者更精准描述差异化定位 |
| 8 | UI 组件库 | 自建 (纯 CSS) | shadcn-vue (Radix Vue + Tailwind) | **shadcn-vue** | Aperant 底层即 Radix UI；shadcn 是 Radix 的最佳封装，copy-paste 模式无依赖锁定；Vue 3 社区生态最活跃的 headless UI 方案 |

---

## 八、不对齐 Aperant 的设计决策

| Aperant 做 | TLO 不做/不同 | 原因 |
|-----------|-------------|------|
| Electron 桌面应用 | Web 优先，Electron 暂缓 (Phase 3 可选) | QA 工程师用浏览器；完成 Web 全能力后再评估离线/OS 需求 |
| Claude-exclusive 后端 | 多 Provider (已有) | 已有 Anthropic + DeepSeek + Google |
| AGPL-3.0 许可 | 企业友好许可 | 企业环境部署考量 |
| Claude Agent SDK 强依赖 | LangGraph + AgentLoop | 已有成熟骨架，迁移成本高 |
| 开发流程编排 (Coder→Merge) | 测试流程编排 (Execute→Analyze→Report) | 产物不同 |
| QA Pass/Fail | 失败深度分析 | TLO 核心差异化 |
| CodeRabbit 代码审查 | — | 测试脚本不需要 AI 代码审查 |
| 线性/PR Review 集成 | GitHub Issue → 测试 + PR → 回归 | 测试场景的集成需求不同 |

---

## 九、成功指标

| 指标 | 当前基线 | Phase 1 目标 | Phase 2 目标 |
|------|---------|-------------|-------------|
| 生命周期阶段覆盖 | 3/8 (执行/分析/报告) | 6/8 | 8/8 |
| QA Loop 自动修复率 | 0% | 30% | 60% |
| Worktree 隔离 | 无 | — | 100% Agent 写操作 |
| Kanban 模块管理 | 静态表格 | 状态卡片 (只读) | 拖拽流转 (可交互) |
| 失败分析深度 | Error message only | + 截图 + Console | + DOM + Network |
| 知识自动提取 | 无 | — | 每次执行 → 1-3 条新知识 |
| 回归推荐准确性 | 无 | — | ≥70% |

---

## 十、参考资源

| 资源 | 用途 |
|------|------|
| [Aperant GitHub](https://github.com/AndyMik90/Aperant) | Spec Pipeline / QA Loop / Worktree / Kanban 设计参考 |
| [Aperant CLAUDE.md](https://raw.githubusercontent.com/AndyMik90/Aperant/main/CLAUDE.md) | Agent 编排规范 + 项目结构 |
| `aitest/governance/safety_auditor.py` | 4 维度独立评分方法论 (可复用到 Failure Analyst) |
| `aitest/graphs/sop_graph.py` | LangGraph 编排参考 (QA Loop 可复用模式) |
| `governance/context/shared-language.md` | 平台术语一致性 |

---

## 附录 A: AITest Platform → TLO 迁移对照

| 旧组件 | 新组件 | 迁移方式 |
|--------|--------|---------|
| `test-design-agent` (1 Skill) | Test Designer (4 Skill Spec Pipeline) | 扩展 |
| `bug-analysis-agent` | Failure Analyst (+ 证据收集 + 根因分类) | 增强 |
| `automation-agent` | Automation Developer (+ Worktree 隔离) | 增强 |
| — | QA Loop (`qa_loop.py`) | 新建 |
| — | Worktree Manager (`worktree_manager.py`) | 新建 |
| — | Regression Advisor Agent | 新建 |
| — | Knowledge Extractor | 新建 |
| — | Environment Preparer Agent | 新建 |
| `/governance` (静态表格) | `/governance` (Kanban 看板) | UI 重写 |
| `agent-definitions.yaml` | 更新为新 Agent 名称 | 修改 |
| `skill-registry.yaml` | 新增 test-designer 4 skills | 扩展 |
| ChromaDB RAG | ChromaDB + 语义关联元数据 | 增强 |

---

## 附录 B: ChatGPT 建议评审纪要

| ChatGPT 建议 | 评审结果 | 采纳 |
|-------------|---------|------|
| Agent 改测试领域名 (Requirement Analyst / Test Strategy / Failure Analyst) | ✅ 精确定位，采纳 | 是 |
| Pipeline 命名: Test Strategy → Planner → Executor → Analyzer → Reporter | ✅ 比泛化名称更好，采纳 | 是 |
| 产品定位 "AI TestOps" / "Agentic Test Platform" | ✅ 定位清晰，采纳 TLO | 是 |
| 失败分析比 Aperant QA 更深 | ✅ 核心差异化，采纳 | 是 |
| Kanban 卡片化 | ✅ 已独立识别，双重确认 | 是 |
| 明确 "不做成 Aperant" | ✅ 方向一致 | 是 |
| Agent 数量保留 ~8 个 | ⚠️ 建议合并为 5 个，我们保留 8+2 新 | 部分 |
| Electron 桌面应用 | ❌ 未提及，我们明确不做 | — |
| Spec Pipeline 4 阶段 | ❌ 未提及，从 Aperant 独立识别 | — |
| Worktree 隔离 | ❌ 未提及，从 Aperant 独立识别 | — |
