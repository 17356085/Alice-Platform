# AITest Platform — Product & UX Architecture Design

> 从 Engine 到 Platform 的分水岭  
> 借鉴 Aperant 产品思维，设计 Testing-native 平台体验  
> 日期：2026-06-23 | 版本：v1.0-draft

---

## 0. 设计原则

### 不是 Aperant for Testing

AITest 不是把 Aperant 的 UI 改成测试主题。产品形态由领域决定：

| Aperant | AITest |
|---------|--------|
| Task = 一个 Coding Feature | Task = 一个测试模块的 SOP 运行 |
| Workspace = Git 仓库 | Workspace = 测试项目 + .tlo/ |
| Artifact = spec.md + code + PR | Artifact = PAGE_CONTEXT + TEST_CASES + Evidence + Report |
| Timeline = 代码修改记录 | Timeline = 测试执行时间线 |
| Kanban = Task 状态 | Kanban = SOP Phase 状态 |
| Terminal = CLI | Terminal = Agent 日志 |

### 三条产品铁律

1. **Project 是第一公民，不是 Chat。** 用户打开平台，第一眼看到的应该是项目列表，不是聊天框。
2. **Artifact 是第一产出，不是对话。** 每个 SOP Phase 产出的文档、报告、证据是平台的持久资产。
3. **Timeline 是第一调试工具，不是日志。** 当 Agent 出问题，用户应该先看 Timeline，不是翻日志。

---

## 1. Information Architecture

```
AITest Platform
│
├── 🏠 Dashboard (项目总览)
│   ├── 项目列表 (卡片：名称/模块数/SOP进度/最后活动)
│   ├── 平台状态 (LLM/Circuit Breaker/Worker Pool/Tenants)
│   ├── 快速操作 (新建项目/运行SOP/查看报告)
│   └── 成本概览 (今日Token/本月费用)
│
├── 📁 Workspace (当前项目)
│   ├── 项目概览
│   │   ├── 模块列表 (grid：模块名/页面数/Phase/状态)
│   │   ├── SOP 进度 (环形图：completed/in_progress/pending/failed)
│   │   └── 最近活动 (Timeline 摘要)
│   │
│   ├── 🎯 Requirements (需求中心)
│   │   ├── 需求文档 (REQUIREMENT_ANALYSIS.md)
│   │   ├── 业务场景 (BUSINESS_SCENARIOS.md)
│   │   └── 测试目标 (Test Objectives)
│   │
│   ├── 🧭 Strategy (策略中心)
│   │   ├── 风险矩阵 (Risk Matrix)
│   │   ├── 覆盖分析 (Coverage Analysis)
│   │   └── 测试策略 (AUTO_STRATEGY.md)
│   │
│   ├── 🧪 Test Design (设计中心)
│   │   ├── 页面分析 (PAGE_CONTEXT.md per page)
│   │   ├── 测试用例 (TEST_CASES.md per page)
│   │   └── 数据设计 (Test Data)
│   │
│   ├── ⚡ Execution (执行中心)
│   │   ├── SOP 运行 (启动/监控/恢复)
│   │   ├── Agent 终端 (实时日志 per agent)
│   │   ├── 执行历史 (Execution History)
│   │   └── 证据查看 (Screenshots/Videos/HAR)
│   │
│   ├── 📊 Reports (报告中心)
│   │   ├── 测试报告 (Excel/JSON per module)
│   │   ├── KPI 趋势 (Success Rate, Coverage Trend)
│   │   └── 运营指标 (8 KPIs: Latency, Cost, Memory...)
│   │
│   ├── 🧠 Knowledge (知识中心)
│   │   ├── ChromaDB 状态 (collections/docs)
│   │   ├── 已知坑位 (Known Issues)
│   │   ├── 定位器历史 (Locator History)
│   │   └── Memory 命中率
│   │
│   └── ⏱️ Timeline (时间线)
│       ├── Agent 活动流
│       ├── Phase 转换记录
│       ├── Artifact 变更记录
│       └── 错误/警告标记
│
├── ⚙️ Settings (设置)
│   ├── 项目设置 (Provider/Model/Base URL)
│   ├── Agent 配置 (model_tier/capabilities)
│   ├── 平台设置 (theme/language/Audit interval)
│   └── 集成 (GitHub/GitLab)
│
└── 🚀 Onboarding (接入向导)
    ├── 选择来源 (URL / 本地 / API)
    ├── 自动扫描 (Menu Tree Discovery)
    ├── 确认页面结构
    └── 生成项目骨架
```

---

## 2. User Journeys

### Journey 1: 导入新项目到第一份报告

```
Step 1: 用户在 Dashboard 点击「+ 新建项目」
   ↓
Step 2: Onboarding Wizard
   - 输入被测系统 URL
   - 平台自动扫描页面结构 (BrowserUse Discovery)
   - 用户确认/编辑 Menu Tree
   ↓
Step 3: 平台生成项目骨架
   - .tlo/project.yaml
   - knowledge/modules/<module>/pages/<page>/
   - 每个 page 创建 PAGE_CONTEXT.md 模板
   ↓
Step 4: 用户进入 Workspace → 点击模块
   ↓
Step 5: 用户点击「运行 SOP」
   - 平台弹出 SOP 配置对话框 (mode/pages/provider)
   - 用户确认 → SOP Graph 启动
   ↓
Step 6: 用户在 Execution Center 看到实时进度
   - SOP 进度条 (Phase 0→1→2→...)
   - Agent 终端实时日志
   - Timeline 记录每次 Phase 转换
   ↓
Step 7: SOP 完成 → Report Center 出现报告
   - 用户点击下载/预览
   ↓
Step 8: Knowledge Center 自动更新
   - 新的定位器模式
   - 新的已知坑位
   - Memory 命中率变化
```

### Journey 2: 调试失败的 SOP

```
Step 1: Dashboard 或 Workspace 显示红色状态标记
   ↓
Step 2: 用户点击失败的 SOP → 进入 Execution Center
   ↓
Step 3: 用户首先看到 Timeline
   - 09:31 Requirement Agent ✅
   - 09:32 Strategy Agent ✅  
   - 09:34 Design Agent ✅
   - 09:38 Execution Agent ❌ (3 retries)
   - 09:42 Bug Analysis Agent 🟡 analyzing
   ↓
Step 4: 用户点击 Execution Agent 失败节点
   → 展开详细错误信息 + Agent 终端日志
   ↓
Step 5: 用户查看 Evidence (截图/页面结构)
   → 确认是定位器过期还是环境问题
   ↓
Step 6: 用户点击「恢复 SOP」→ 从 checkpoint 继续
```

### Journey 3: 查看平台运营状况

```
Step 1: Dashboard → 平台状态面板
   - LLM: claude-sonnet-4-6 (healthy, 0 circuit breakers open)
   - Worker Pool: 2/4 active, 12 completed, 0 failed
   - 项目数: 3
   ↓
Step 2: 点击「运营指标」→ 进入 Report Center / KPI 面板
   - Agent Latency p95: 12.3s (automation-agent)
   - Token Cost today: $3.42
   - Workflow Success Rate: 94.7%
   - Plugin Failure Rate: 0.3%
   ↓
Step 3: 发现 automation-agent latency 偏高
   → 点击展开 Phase Distribution
   → Planning 18% | Reasoning 46% | Tool Calling 21% | Memory 8%
   → Tool Calling 占比高 → 可能是 Browser 调用慢
   ↓
Step 4: 查看 Cost per Capability
   → Browser: avg 2,340 tokens, 8.2s, 96% success
   → Codegen: avg 1,200 tokens, 3.1s, 99% success  
   → RAG: avg 340 tokens, 0.4s, 100% success
   ↓
Step 5: 结论：Browser 能力是瓶颈，考虑升级 BrowserUse provider 或换 Playwright 直连
```

---

## 3. Testing Workspace — 超越 Aperant 的设计

Aperant 的 Workspace 以 Git 仓库为组织单元。AITest 的 Workspace 以**测试项目 → 模块 → 页面**为组织单元。这是 AITest 可以超越 Aperant 的地方。

### 3.1 Workspace 信息层级

```
Project: web-automation
│
├── Module: equipment (设备管理)
│   ├── Page: alarm-config (告警配置)
│   │   ├── 📄 PAGE_CONTEXT.md       ← 页面分析产出
│   │   ├── 📄 RISK_MODEL.md         ← 风险建模产出
│   │   ├── 📄 TEST_CASES.md         ← 测试用例 (68 cases)
│   │   ├── 📄 TECH_ANALYSIS.md      ← 技术分析产出
│   │   ├── 📄 AUTO_STRATEGY.md      ← 自动化策略
│   │   ├── 📜 AlarmConfigPage.py    ← Page Object
│   │   ├── 🧪 test_alarm_config.py  ← 测试脚本
│   │   ├── 📸 evidence/             ← 执行证据
│   │   │   ├── screenshot_001.png
│   │   │   └── page_structure.json
│   │   └── 📊 report/               ← 报告
│   │       └── alarm-config-test-report.xlsx
│   │
│   ├── Page: camera (摄像头管理)
│   └── Page: key-param (关键参数)
│
├── Module: personnel (人员管理)
├── Module: system-management (系统管理)
└── ...
```

### 3.2 Workspace 右侧面板 (Contextual Panel)

当用户点击某个 Page 时，右侧出现上下文面板：

```
┌─ Page: alarm-config ──────────────────────────┐
│                                                │
│  SOP Phase: ████░░░░░░ 4/8 (automation)       │
│  Status: in_progress                           │
│                                                │
│  ── Artifacts ──                               │
│  ✅ PAGE_CONTEXT.md     2026-06-20             │
│  ✅ RISK_MODEL.md       2026-06-20             │
│  ✅ TEST_CASES.md       68 cases               │
│  ✅ TECH_ANALYSIS.md    2026-06-21             │
│  🔄 AUTO_STRATEGY.md    generating...          │
│  ⬜ AlarmConfigPage.py                         │
│  ⬜ test_alarm_config.py                       │
│                                                │
│  ── Recent Activity ──                         │
│  09:31  Design Agent completed                 │
│  09:32  Automation Agent started               │
│  09:35  TECH_ANALYSIS.md saved                 │
│                                                │
│  [Run SOP]  [View Report]  [Open in Terminal]  │
└────────────────────────────────────────────────┘
```

---

## 4. Timeline 设计

这是借鉴 Aperant 最多的产品设计。Timeline 是调试 Agent 的第一入口。

### 4.1 Timeline 条目类型

```
🟢 Phase Started    project-agent started Phase 0
📄 Artifact Created  PAGE_CONTEXT.md saved
🟡 Warning          Gate check: missing AUTO_STRATEGY.md
🔴 Error            automation-agent failed (retry 1/3)
🔄 Retry            automation-agent retrying...
✅ Phase Completed  test-design-agent completed (12.3s)
💾 Checkpoint       SOP state saved
🧠 Memory Hit       Known issue matched: el-dialog teleport
```

### 4.2 Timeline 视图

```
Project: web-automation  Module: equipment  Page: alarm-config
─────────────────────────────────────────────────────────────

Today, June 23

09:31  ✅ project-agent completed                Phase 0  [2.1s]
       → PROJECT_CONTEXT.md verified
       → MODULE_CONTEXT.md verified

09:31  🟢 requirement-agent started              Phase 1

09:32  📄 REQUIREMENT_ANALYSIS.md created
       → 3 business scenarios identified
       → 12 test targets defined

09:32  ✅ requirement-agent completed            Phase 1  [1.8s]

09:32  🟢 test-design-agent started              Phase 2

09:33  📄 PAGE_CONTEXT.md created
       → 24 elements found (8 inputs, 6 buttons, 3 tables, 7 labels)
       → Framework: Element Plus 2.x detected

09:34  🧠 Memory Hit
       → Known issue #42: el-dialog append-to-body
       → Known issue #17: el-cascader lazy load

09:34  📄 RISK_MODEL.md created
       → Risk score: Medium (12 factors, score 34/100)

09:35  📄 TEST_CASES.md created
       → 68 cases (P0: 12, P1: 28, P2: 28)
       → Type: Positive 40, Negative 18, Boundary 10

09:35  ✅ test-design-agent completed            Phase 2  [3.4s]

09:36  🟢 automation-agent started               Phase 4

09:38  📄 TECH_ANALYSIS.md created
       → 24 locators designed (A: 18, B: 5, C: 1)
       → Wait strategies: 8 visibility, 6 clickable, 2 custom

09:40  🔴 automation-agent failed                Phase 4  [4.2s]
       → Error: element not found: .el-table__body
       → Root cause: table lazy-renders after API response

09:41  🔄 automation-agent retrying (1/3)        Phase 4

09:42  📜 AlarmConfigPage.py created
       → 24 locators, 12 methods

09:42  ✅ automation-agent completed             Phase 4  [6.1s]

09:43  🟢 execution-agent started                Phase 6
       ████████░░░░░░░░░░ Running...
```

### 4.3 Timeline 的交互

- **点击条目** → 展开详情（完整日志、token 消耗、参数）
- **点击 Phase 节点** → 跳转到 Agent 终端该阶段的日志
- **点击 Artifact** → 在右侧面板打开预览
- **点击错误** → 展开错误堆栈 + 建议修复
- **时间轴缩放** → 按分钟/小时/天聚合

---

## 5. Dashboard 设计

### 5.1 首屏布局

```
┌──────────────────────────────────────────────────────────────┐
│  AITest Platform                              [Settings] [👤] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Platform Status ──────────────────────────────────────┐  │
│  │  🟢 Healthy  │  LLM: claude  │  Workers: 2/4  │  3 Projects │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Projects ──────────────────────── [+ New Project] ────┐  │
│  │                                                         │  │
│  │  ┌──────────────────┐  ┌──────────────────┐            │  │
│  │  │ web-automation   │  │ blue-album-v2    │            │  │
│  │  │ ████████░░ 78%   │  │ ████░░░░░░ 35%   │            │  │
│  │  │ 12 modules       │  │ 4 modules        │            │  │
│  │  │ 48 pages         │  │ 12 pages         │            │  │
│  │  │ Last: 09:42      │  │ Last: yesterday  │            │  │
│  │  │ [Open]           │  │ [Open]           │            │  │
│  │  └──────────────────┘  └──────────────────┘            │  │
│  │                                                         │  │
│  │  ┌──────────────────┐  ┌──────────────────┐            │  │
│  │  │ miniapp-weixin   │  │ + Import Project  │            │  │
│  │  │ ██░░░░░░░ 18%   │  │                   │            │  │
│  │  │ 3 modules        │  │                   │            │  │
│  │  │ Last: last week  │  │                   │            │  │
│  │  │ [Open]           │  │                   │            │  │
│  │  └──────────────────┘  └──────────────────┘            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Quick Actions ────────────────────────────────────────┐  │
│  │  [🔍 Discover]  [▶️ Run SOP]  [📊 Reports]  [⚙️ Settings] │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Today's Activity ─────────────────────────────────────┐  │
│  │  09:42  automation-agent ✅  equipment/alarm-config     │  │
│  │  09:35  test-design-agent ✅  equipment/alarm-config    │  │
│  │  09:32  requirement-agent ✅  equipment/alarm-config    │  │
│  │  09:31  project-agent ✅  equipment/alarm-config        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Project Card 设计

每个 Project Card 展示：
- **项目名** + 状态标记 (active/idle/error)
- **SOP 进度条** (所有模块的 Phase 完成率)
- **模块数 / 页面数**
- **最近活动时间**
- **快捷操作**: [Open Workspace] [Run SOP] [Latest Report]

---

## 6. Agent 终端 — 运行时可见性

### 6.1 多 Agent 标签页

```
┌─ Execution Center ──────────────────────────────────────────┐
│  [project-agent] [requirement] [test-design] [automation]   │
│  [execution] [bug-analysis] [report] [knowledge]            │
│                                                             │
│  ┌─ automation-agent ────────────────────────────────────┐  │
│  │  Status: Running  |  Step: 3/6  |  Skill: codegen     │  │
│  │  Tokens: 1,240 in / 890 out  |  Cost: $0.02           │  │
│  │  Circuit: ✅ closed                                    │  │
│  │                                                        │  │
│  │  ── Log ───────────────────────────────────────────── │  │
│  │  [09:36] 🤖 Agent: automation-agent | Provider: claude │  │
│  │  [09:36] 📋 Skill chain: tech-analysis → auto-strategy │  │
│  │           → page-object → test-script → consistency    │  │
│  │  [09:37] ▶️ Executing: tech-analysis                   │  │
│  │  [09:37] 🧠 Memory hit: el-dialog append-to-body        │  │
│  │  [09:38] 📄 TECH_ANALYSIS.md saved (24 locators)       │  │
│  │  [09:38] ✅ tech-analysis completed (2.1s)             │  │
│  │  [09:39] ▶️ Executing: page-object-generator           │  │
│  │  ...                                                    │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 终端增强

对比当前 `print()` 日志：

```
现在:
[AGENT] automation-agent | Provider: claude
[PLAN] Skill chain: tech-analysis → ...

未来:
🟢 automation-agent started  Phase 4  module=equipment  page=alarm-config
   tier=max  model=claude-opus-4-8  budget=30,000 tokens
📄 tech-analysis → 24 locators (18 A-grade, 5 B-grade, 1 C-grade)
   duration=2.1s  tokens_in=1,240  tokens_out=890  cost=$0.02
⚠️ 1 C-grade locator: .el-table__body (lazy-renders after API)
   → Suggested fix: add wait_for_selector('.el-table__body tr')
```

---

## 7. 前端页面结构 (当前 vs 目标)

### 7.1 当前路由表 (14 views)

```
/dashboard          DashboardView           ← 基础统计卡片
/workspace/kanban   KanbanView             ← SOP Phase 看板
/workspace/gaps     GapDiscoveryView       ← 测试缺口扫描
/workspace/chat     IntelligenceChatView    ← AI 聊天
/workspace/execution ExecutionView          ← 终端面板
/workspace/terminal AgentTerminalView       ← Per-agent 日志
/workspace/reports  ReportsView            ← KPI 摘要
/workspace/knowledge KnowledgeView          ← RAG 状态
/workspace/ideation IdeationView            ← 改进建议
/workspace/integrations IntegrationView     ← GitHub/GitLab
/workspace/settings ProjectSettingsView     ← 项目设置
/settings           SettingsView            ← 平台设置
/onboarding         OnboardingWizardView    ← 接入向导
/strategy           StrategyPlannerView     ← 风险矩阵
```

### 7.2 目标路由表 (重组后)

```
/dashboard              ← 增强：项目卡片 + 平台状态 + Activity Feed
/projects/:id           ← 新增：项目 Workspace 主页
/projects/:id/requirements  ← 重组：需求中心
/projects/:id/strategy  ← 重组：策略中心 (原 /strategy 移入)
/projects/:id/design    ← 新增：测试设计中心 (原 gaps 一部分)
/projects/:id/execution ← 增强：执行中心 + Agent 终端 (原 terminal 合并)
/projects/:id/timeline  ← 新增：时间线 (核心新功能)
/projects/:id/reports   ← 增强：报告中心 + 运营指标
/projects/:id/knowledge ← 增强：知识中心 + Memory 命中率
/projects/:id/artifacts ← 新增：Artifact 浏览器 (文件树 + 预览)
/projects/:id/settings  ← 保持
/settings               ← 保持
/onboarding             ← 保持
```

**核心变化：**
- `/workspace/*` → `/projects/:id/*` — Project 成为 URL 第一公民
- 新增 Timeline、Artifacts、Design Center
- Chat 降级为 Agent 终端的一个视图模式，不再独立路由
- Kanban 融入 Execution Center（SOP 进度看板）

---

## 8. 借鉴 Aperant vs Testing-native 设计决策

| 设计元素 | Aperant 做法 | AITest 做法 | 理由 |
|----------|-------------|------------|------|
| **Workspace 组织** | Git 仓库 + Spec 目录 | 测试项目 + .tlo/ + Module/Page 层级 | Testing-native。测试不围绕 Git |
| **Task 单元** | 一个 Coding Feature | 一个模块的 SOP 运行 | 领域差异 |
| **Timeline** | 代码修改记录 + Agent 事件 | 测试执行时间线 + Phase 转换 + Artifact 变更 | 借鉴思想，测试化 |
| **Kanban** | Task 状态 (Todo→Done) | SOP Phase 状态 (0→8) | 已有，增强交互 |
| **Terminal** | xterm.js PTY | Agent 结构化日志 + 实时指标 | 更结构化。测试 Agent 日志比 PTY 有用 |
| **Insights** | 代码库探索 + 问答 | 测试缺口扫描 + 改进建议 | 已类似，继续增强 |
| **Artifact 面板** | 文件树 (spec dir) | Page 级 Artifact 列表 + 内容预览 | 更聚焦。测试 artifact 是文档 |
| **Memory UI** | 无前端展示 | ChromaDB 状态 + 命中率 + 最近匹配 | 测试需要可观测的 Memory |
| **Roadmap** | Feature → Task | Requirement → Test Cycle | 保留概念，测试化 |
| **Git Worktree UI** | Worktree 状态面板 | Execution Workspace (非 Git) | 测试不需要 Git 隔离 |
| **PR Review UI** | Diff + Comment | 不需要 | 测试无 PR 场景 |
| **Merge UI** | 冲突解决面板 | 不需要 | 测试无合并场景 |

---

## 9. 实施优先级

### P0 — v1.1 必须

1. **Dashboard 增强** — 项目卡片 + 平台状态 + Activity Feed
2. **Timeline 页面** — `/projects/:id/timeline` (核心差异化功能)
3. **Workspace 重组** — `/workspace/*` → `/projects/:id/*`

### P1 — v1.2

4. **Artifact 浏览器** — 右侧上下文面板，Page 级文件树 + 预览
5. **Agent 终端增强** — 结构化日志 + 实时指标 (tokens/cost/duration)
6. **执行中心增强** — SOP 进度条 + Phase 状态可视化

### P2 — v1.3

7. **需求中心 / 策略中心 / 设计中心** — 从 Chat 分离为独立视图
8. **运营指标 Dashboard** — 8 KPIs 可视化趋势图
9. **Memory 面板** — ChromaDB 状态 + 命中率 + 匹配历史

---

## 10. 一句话

**引擎已经就绪。现在让用户看见平台。**
