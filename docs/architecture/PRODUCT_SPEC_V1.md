# Alice V1 — Product Specification

> 融合 Architecture Analysis + UX Analysis  
> 所有后续开发以此文档为唯一产品事实源  
> 版本：V1.0 | 日期：2026-06-23

---

## 1. Vision

**Alice 是一个企业级 AI 测试自动化平台。**

用户导入被测系统，平台自动完成需求分析 → 策略制定 → 测试设计 → 脚本生成 → 执行 → 失败分析 → 报告 → 知识沉淀的全流程。

核心差异化：
- **Testing-native Workspace**：以项目/模块/页面为组织单元，不是 Chat
- **Artifact-first Pipeline**：每个 SOP Phase 产出明确文档，平台是资产积累系统
- **Timeline as primary debugger**：Agent 出问题先看 Timeline，不是翻日志
- **Observable Agents**：实时看见 Agent 在做什么、花了多少 Token、命中了什么 Memory

---

## 2. Users

| 角色 | 需求 | 核心场景 |
|------|------|----------|
| **测试工程师** | 导入项目，运行 SOP，查看报告 | 日常测试自动化 |
| **测试架构师** | 制定策略，管理 Knowledge，Review 质量 | 测试治理 |
| **QA Manager** | 查看进度，成本，成功率 | 团队管理 |
| **平台管理员** | 配置 Provider，管理租户，监控健康 | 平台运维 |

---

## 3. Information Architecture

```
Alice
│
├── 🏠 Dashboard
│   ├── 平台状态 (LLM / Worker Pool / Tenants)
│   ├── 项目卡片 (进度条 / 模块数 / 最近活动)
│   ├── 今日活动 (Timeline 摘要)
│   └── 快速操作
│
├── 📁 Project Workspace  (/projects/:id)
│   ├── Overview       — 模块列表 + SOP 进度 + 最近活动
│   ├── Requirements   — 需求文档 + 业务场景
│   ├── Strategy       — 风险矩阵 + 覆盖分析
│   ├── Test Design    — 页面分析 + 测试用例
│   ├── Execution      — 运行 / 暂停 / 恢复 SOP
│   │   ├── SOP Progress   — 进度条 + Phase 状态
│   │   ├── Agent Terminal — 实时日志 + 指标
│   │   └── Live Graph     — Agent 执行图 (核心差异化)
│   ├── Observability  — Timeline / Logs / Metrics / Cost
│   │   ├── Timeline       — Agent 活动时间线
│   │   ├── Metrics        — 8 KPIs 趋势图
│   │   └── Cost           — Token 消耗 + 费用
│   ├── Artifacts      — 文件浏览器 + 预览
│   ├── Knowledge      — ChromaDB / Known Issues / Memory 命中率
│   ├── Reports        — 测试报告 + KPI 趋势
│   └── Settings       — 项目配置
│
├── 🚀 Onboarding      — 导入向导
└── ⚙️ Settings         — 平台设置
```

### Progressive Disclosure

首次进入只有 Dashboard + 项目列表。创建/打开项目后，Workspace 逐步展开：

```
Level 1 (始终可见): Dashboard, Project List
Level 2 (项目打开后): Overview, Execution, Artifacts
Level 3 (SOP 运行后): Timeline, Reports, Knowledge
Level 4 (深度使用): Strategy, Requirements, Metrics
```

---

## 4. Core Pages (10 pages)

### 4.1 Dashboard (`/`)

```
┌─ 平台状态栏 ──────────────────────────────────────────┐
│ 🟢 Healthy  LLM:claude  Workers:2/4  Projects:3      │
├─ 项目卡片 ───────────────────── [+ Import] ──────────┤
│ ┌─ web-automation ─┐ ┌─ blue-album ─┐ ┌─ miniapp ─┐ │
│ │ ████████░░ 78%   │ │ ████░░░░ 35% │ │ ██░░░ 18% │ │
│ │ 12 modules       │ │ 4 modules    │ │ 3 modules  │ │
│ │ [Open]           │ │ [Open]       │ │ [Open]     │ │
│ └──────────────────┘ └──────────────┘ └────────────┘ │
├─ 今日活动 (Timeline 摘要, 最近5条) ──────────────────┤
│ 09:42 ✅ automation-agent  equipment/alarm-config    │
│ 09:35 ✅ test-design-agent  equipment/alarm-config   │
└──────────────────────────────────────────────────────┘
```

### 4.2 Project Overview (`/projects/:id`)

模块网格 + SOP 环形进度 + 最近 Timeline。项目级操作入口。

### 4.3 Execution (`/projects/:id/execution`)

```
┌─ Execution ───────────────────────────────────────────┐
│ Module: [equipment ▾]  Page: [alarm-config ▾]        │
│                                                        │
│ ┌─ SOP Progress ────────────────────────────────────┐ │
│ │ Phase 0 ✅ → 1 ✅ → 2 ✅ → 3 ⏳ → 4 ⬜ → ... → 8   │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ ┌─ Live Graph ────────────┐ ┌─ Agent Terminal ──────┐ │
│ │   [entry]               │ │ [project] [req] [des]  │ │
│ │     ↓                   │ │ [auto] [exec] [bug]    │ │
│ │  [preflight]            │ │                        │ │
│ │     ↓                   │ │ 🟢 automation-agent    │ │
│ │  ┌─cond_route─┐        │ │ Step 3/6  Skill:codegen│ │
│ │  ↓   ↓   ↓   ↓        │ │ Tokens:1,240/890 $0.02 │ │
│ │  P0  P1  P2  P4...    │ │                        │ │
│ │       ↓                │ │ [09:38] 📄 TECH_ANALYSIS│ │
│ │  [automation-agent]🟢  │ │ [09:39] ▶️ page-object │ │
│ └────────────────────────┘ └────────────────────────┘ │
│                                                        │
│ [▶ Run SOP]  [⏸ Pause]  [↻ Resume]  [■ Cancel]      │
└──────────────────────────────────────────────────────┘
```

### 4.4 Observability — Timeline (`/projects/:id/observability`)

Agent 活动时间线（参见 UX Architecture §4）。核心调试入口。

### 4.5 Artifacts (`/projects/:id/artifacts`)

```
┌─ Artifacts ───────────────────────────────────────────┐
│ Module: equipment  Page: alarm-config                 │
│                                                        │
│ 📁 alarm-config/                                       │
│   ├── ✅ PAGE_CONTEXT.md       2026-06-20  [预览]     │
│   ├── ✅ RISK_MODEL.md         2026-06-20  [预览]     │
│   ├── ✅ TEST_CASES.md         68 cases    [预览]     │
│   ├── ✅ TECH_ANALYSIS.md      2026-06-21  [预览]     │
│   ├── 🔄 AUTO_STRATEGY.md     generating...           │
│   ├── ⬜ AlarmConfigPage.py                            │
│   └── ⬜ test_alarm_config.py                          │
│                                                        │
│ ┌─ Preview: PAGE_CONTEXT.md ─────────────────────────┐ │
│ │ # Page Context: 告警配置                            │ │
│ │ ## Elements (24)                                    │ │
│ │ | Name | Type | Locator | Grade |                   │ │
│ │ |------|------|---------|-------|                   │ │
│ │ | ...                                              │ │
│ └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 4.6 Knowledge (`/projects/:id/knowledge`)

ChromaDB 状态、Known Issues 列表、Memory 命中率、最近匹配。

### 4.7 Reports (`/projects/:id/reports`)

测试报告列表 + KPI 趋势 (8 运营指标) + Token 成本趋势。

### 4.8 Onboarding (`/onboarding`)

4-step wizard: URL输入 → 扫描 → 确认Menu → 完成。

### 4.9 Settings (`/settings`)

平台设置: Provider / Model / Theme / Language / Audit Interval / API Key。

### 4.10 Project Settings (`/projects/:id/settings`)

项目配置: Base URL / Test Project Path / Model Tier overrides。

---

## 5. Agent Workflow (用户视角)

```
用户在 Execution 页面:
  1. 选择 Module + Page (或全模块)
  2. 选择 Mode (full / from-automation / resume)
  3. 点击 [▶ Run SOP]
  
  → Live Graph 展示 SOP 图，当前节点高亮
  → Agent Terminal 实时日志 + tokens/cost/duration
  → Timeline 新增 Phase 事件
  
  SOP 完成:
  → Artifacts 页面自动出现新文件
  → Reports 页面出现新报告
  → Knowledge 页面更新 Memory
```

---

## 6. Context Model

```
User ←→ Platform
         │
         ├── Project (.tlo/project.yaml)
         │     ├── knowledge/modules/<module>/
         │     │     ├── MODULE_CONTEXT.md
         │     │     └── pages/<page>/
         │     │           ├── PAGE_CONTEXT.md
         │     │           ├── RISK_MODEL.md
         │     │           ├── TEST_CASES.md
         │     │           ├── TECH_ANALYSIS.md
         │     │           └── AUTO_STRATEGY.md
         │     ├── runtime/sop-status/
         │     └── artifacts/
         │
         ├── Agent ←→ LLM Provider
         │     ├── Skill (.md prompt)
         │     ├── Capability (Browser / RAG / Codegen / Execute)
         │     └── Memory (ChromaDB → TestingMemory)
         │
         └── Observability
               ├── Timeline (Agent events)
               ├── Metrics (8 KPIs)
               ├── Trace (OTel spans)
               └── Logs (JSONL)
```

---

## 7. Artifact Model

```
每个 Page 的 SOP 运行产生:

Phase 0: PROJECT_CONTEXT.md (项目级)
Phase 1: REQUIREMENT_ANALYSIS.md
Phase 2: PAGE_CONTEXT.md, RISK_MODEL.md, TEST_CASES.md
Phase 4: TECH_ANALYSIS.md, AUTO_STRATEGY.md, PageObject.py, test_*.py
Phase 6: evidence/ (screenshots, HAR, page_structure.json)
Phase 7: BUG_ANALYSIS.md (如果失败)
Phase 8: report/ (Excel, JSON)
Transverse: Knowledge updates (ChromaDB)
```

---

## 8. Timeline Model

```json
{
  "ts": "2026-06-23T09:42:00Z",
  "project": "web-automation",
  "module": "equipment",
  "page": "alarm-config",
  "type": "phase_completed",
  "agent": "automation-agent",
  "phase": 4,
  "duration_s": 6.1,
  "tokens_in": 1240,
  "tokens_out": 890,
  "success": true,
  "artifacts": ["AlarmConfigPage.py", "test_alarm_config.py"]
}
```

---

## 9. Future Roadmap

| 版本 | 内容 |
|------|------|
| **V1.0** ✅ | Architecture frozen, Constitution, 92 tests, CI/Docker, Operational KPIs |
| **V1.1** | Dashboard增强 + Timeline + Workspace重组 (`/projects/:id`) |
| **V1.2** | Artifact浏览器 + Live Graph + Agent终端增强 |
| **V1.3** | Knowledge面板 + Metrics趋势 + Progressive Disclosure |
| **V2.0** | Memory Observer, Process隔离, 多节点, E2E Benchmark |

---

> **本 Spec 是 Alice V1 的唯一产品事实源。所有 PR、设计、开发均对照本文。**
