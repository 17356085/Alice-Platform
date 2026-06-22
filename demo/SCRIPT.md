# AITest Platform 演示脚本

> v0.5 Demo · 15 分钟 · 技术评委受众 · Live demo

---

## 时间线总览

| 段 | 时长 | Track | 内容 |
|----|------|-------|------|
| 开场 | 1min | — | 平台概述、架构定位 |
| 1 | 5min | A (CLI) | `dashboard` → `sop gate` → `sop run` → `trace stats` → `kpi summary` |
| 2 | 3min | B (Web) | Dashboard → Chat 工作台 → Trace 回放 |
| 3 | 3min | C (Dev) | `sop-dev run` — 9 Agent 开发流水线 |
| 收尾 | 3min | 治理 | 治理面板 → Safety Audit → KPI → Q&A |

---

## 准备清单

```bash
# 终端 1: 启动服务
aitest server start

# 终端 2: 预打开页面
# http://localhost:8000/          (Dashboard)
# http://localhost:8000/chat       (Chat)
# http://localhost:8000/trace      (Trace)
# http://localhost:8000/docs       (API)

# 终端 3: CLI 演示用
cd d:/Desktop/WorkStudy
```

---

## 开场 (1 min)

**[屏幕展示 Dashboard 页面]**

> "鞍集涂源管理系统 AI 测试平台 v0.5。12 个业务模块、828 个自动化测试用例，由 8 个 AI Agent 协作驱动。
>
> 核心架构分两层：
> - **治理层**：Prompt 工程 → Workflow 工程 → Skill 工程 → Agent 工程 → MCP 工程 → RAG 工程，六层全闭环
> - **执行层**：LangGraph 有状态编排引擎，支持 HITL 人机协同中断、断点续跑、质量门禁
>
> 今天演示三条线：CLI 测试流水线、Web 工作台、Dev Agent 开发流水线。"

**架构解说要点**（技术评委）:
- LangGraph StateGraph + checkpoint 持久化 → 任意节点中断恢复
- 6 层治理全闭环 (Prompt → Workflow → Skill → Agent → MCP → RAG)
- Event Bus 驱动 Knowledge Agent 自动学习

---

## Track A: CLI 能力展示 (5 min)

### A1. 平台总览 — `aitest dashboard` (30s)

```bash
aitest dashboard
```

**展示点**:
- 12 模块 SOP 状态矩阵（completed/partial/pending）
- 任务队列统计
- RAG 知识库 (5 集合, 235 文档)
- Event Bus 待处理事件
- Bug 历史
- Skill 能力分布 + LLM Provider

**解说**: "一个命令看到整个平台的全貌。每个模块的 SOP Phase、RAG 文档数、Event Bus 事件队列、Bug 历史——全部实时聚合。"

### A2. 门禁检查 — `check_sop_gate.py` (45s)

```bash
python ZJSN_Test-master526/tools/check_sop_gate.py \
  --module equipment --agent automation-agent --json
```

**展示点**:
- 前置条件检查（PROJECT_CONTEXT.md 是否存在、PageObject 是否编写）
- W04 BrowserUse 维度、P3 Prompt Engineering 维度
- `blocked: true/false` 判定

**解说**: "这是 SOP 门禁——每个 Agent 启动前强制验证前置条件是否满足。不满足时直接 block，给出缺失项和修复建议。等同于 CI/CD 的 pre-commit hook，但在 AI 编排层。"

### A3. SOP 流水线 — `aitest sop run` (2min)

```bash
aitest sop run --module=equipment --mode=full --non-interactive
```

**展示点**:
- Preflight 自动检测已有 artifacts，推荐最优 mode
- LangGraph 节点流转：entry → preflight → project_agent → ... → exit
- HITL 中断（如果触发）：展示 `[HITL] Approval Required` 和 auto-approve
- 最终 JSON 输出：completed_phases, status, pages_processed

**解说**: "完整 SOP 流水线——LangGraph 编译图、流式执行。每个节点是一个 Agent，每个 Agent 执行一组 Skill。HITL 中断在关键节点（如自动化策略审批）暂停等待人工确认。非交互模式下自动通过。"

**技术亮点**:
- checkpoint 持久化 (SQLite via langgraph-checkpoint-sqlite)
- 中断恢复机制
- 失败自动重试

### A4. 可观测性 — `aitest trace` (1min)

```bash
aitest trace list --run-id=sop-equipment-240620-001 --limit=5
aitest trace stats --run-id=sop-equipment-240620-001
```

**展示点**:
- 每次 LLM 调用、Skill 执行、Agent 决策全记录
- Token 成本精确到 $0.0001
- 按 Agent/Skill 聚合统计

**解说**: "全链路可观测——每个 LLM 调用、每个 Skill 执行、每个 Agent 决策都有完整 trace。Token 成本精确计算，支持按 run/agent/skill 多维度聚合。"

### A5. 治理 KPI — `aitest kpi summary` (45s)

```bash
aitest kpi summary --days=30 --json
```

**解说**: "L4 治理指标——State Audit（状态漂移）、SOP Audit（合规）、Cost Audit（成本）、Safety Audit（安全）四大审计器独立评分。安全指标不与其他指标混合，独立拉出。"

---

## Track B: Web 工作台 (3 min)

### B1. Dashboard 首页 (30s)

**[浏览器切换到 http://localhost:8000/]**

**展示点**:
- Hero 区域：模块数/用例数/Agent数/Skill数
- 演示导航流程
- 模块 SOP 状态矩阵
- 快速入口卡片

### B2. Chat 工作台 (1min)

**[点击 "Chat 工作台" 或 http://localhost:8000/chat]**

**展示点**:
- 左侧 Sidebar：12 模块树 + 页面状态点 (绿/红/灰)
- 会话管理：新建/搜索/切换 session
- 治理面板 (🛡)：State/SOP/Cost 三合一审计面板
- 输入框：支持自然语言指令 + 快速操作按钮

**解说**: "Chat 工作台——左侧模块导航，右侧 AI 对话。每个模块展开显示页面列表和测试状态。治理面板一键拉取 State/SOP/Cost 三合一审计。"

### B3. Trace 回放 (1min)

**[点击导航栏 "Trace 回放" 或 http://localhost:8000/trace]**

**展示点**:
- Run 选择下拉：3 条预填充 run（equipment SOP / warehouse bug / dev SOP）
- 选择 `sop-equipment-240620-001` → 展示
- Summary 卡片：总步数、成功/失败/部分、总成本 $1.04、总延迟
- 时间线：每步显示 skill_id、status badge、model、token 数、成本、响应预览

**解说**: "Agent 运行时观测面板——选择一次运行，看到每一步的完整执行链路。绿色是成功、红色是失败、黄色是有安全标志。每个 step 显示使用的模型、token 消耗、成本和响应预览。选中第二条 run 有安全标志——发现了敏感信息泄露。"

**技术亮点**:
- JSONL 追加写入，零外部依赖
- 实时安全扫描 (safety_auditor.check_output_safety)
- 成本按模型定价表精确计算

### B4. API 文档 (30s)

**[http://localhost:8000/docs]**

**展示点**: Swagger UI，30+ 端点，分类：Chat / Agent / Workflow / Bug / Audit / KPI / Trace

---

## Track C: Dev Agent 开发流水线 (3 min)

### C1. Dev SOP CLI 运行 (2min)

```bash
aitest sop-dev run --module=tank-monitor --mode=full --non-interactive
```

**展示点**:
- 9 Agent 节点：pm → req → arch → design → frontend → backend → review → test → debug → build
- 10 Phase 流水线
- 与测试 SOP 共用 LangGraph checkpoint 机制

**解说**: "开发 SOP 流水线——9 个开发 Agent 协作完成一个完整功能模块。从 PM 立项、需求分析、架构设计，到前后端实现、Code Review、测试、调试、构建。每个 Agent 有明确的 Primary/Secondary Owner 关系绑定到 Skill。"

**技术亮点**:
- 复用同一套 LangGraph + checkpoint 基础设施
- 32 个 dev Skill，覆盖全开发流程
- 条件路由：review 发现问题自动触发 debug agent

### C2. 架构设计结果展示 (1min)

```bash
aitest trace list --run-id=dev-sop-tank-monitor-240622-003
```

**解说**: "这是前面演示中 dev SOP 的一次真实运行——PM Agent 完成项目初始化和计划审批，需求 Agent 分析了业务需求，架构 Agent 设计了完整的组件树和数据流。从 trace 回放可以看到每一步的输入输出。"

---

## 收尾: 治理全景 (3 min)

### 治理指标聚合 (1min)

```bash
aitest kpi audit-all --modules=equipment,warehouse,tank --json
```

**解说**: "一次性审计全部模块——State/SOP/Cost/Safety 四个维度独立评分。"

### Safety Auditor (1min)

```bash
python -c "
from aitest.governance.safety_auditor import SafetyAuditor
report = SafetyAuditor().audit('warehouse', days=7)
print(f'Safety Score: {report[\"safety_score\"]}/100')
print(f'Violations: {report[\"total_violations\"]} (critical: {report[\"critical_count\"]}, high: {report[\"high_count\"]})')
for v in report['violations']:
    print(f'  [{v[\"severity\"]}] {v[\"rule_id\"]}: {v[\"description\"]}')
"
```

**展示点**:
- 4 维安全检查：高风险确认 / 敏感泄露 / 权限绕过 / 审计完整性
- 独立评分（不与质量分混合——来自 Agent 评估方法论）
- 安全事件自动发射到 Event Bus

**解说**: "安全审计独立于质量审计——这是我们从 Agent 评估方法论中得出的核心原则：安全指标必须独立拉出，不可被平均分掩盖。4 个检查维度：高风险操作确认、敏感信息泄露、权限绕过、审计链路完整性。"

### 总结 (1min)

**回到 Dashboard 页面**

> "总结一下：AITest Platform v0.5 覆盖了 AI 测试的完整链路——
>
> - **CLI 侧**：一条命令跑通完整 SOP，门禁检查 → 流水线编排 → trace 观测 → KPI 报表
> - **Web 侧**：Chat 工作台 + Trace 回放 + 治理仪表板，浏览器完成全流程
> - **开发侧**：9 Agent 开发流水线已打通，从需求到构建全 AI 驱动
>
> 欢迎提问。"

---

## 故障预案

| 场景 | 方案 |
|------|------|
| LLM API 超时 | 切换到 trace 回放展示历史数据，强调平台即使 API 不可用也有完整可观测性 |
| 被测系统不可达 | SOP run 会卡在 preflight。展示 preflight 自动检测机制 + gate 检查，跳过实际执行 |
| Trace 数据不显示 | 重新运行 `python demo/seed_traces.py` 刷新数据 |
| 服务启动失败 | `pip install -r requirements.txt` 重装依赖，或用 Docker 启动 |
| Chat 页面空白 | 检查浏览器 console，回退到 Dashboard + CLI 纯展示 |

---

## 附录: 关键架构图 (口头解说时使用)

```
┌─────────────────────────────────────────────────────┐
│                   Governance Layer                    │
│  Prompt → Workflow → Skill → Agent → MCP → RAG       │
│  + State/SOP/Cost/Safety 4 Auditors                   │
│  + Event Bus (AgentCompleted, BugClosed, ...)         │
├─────────────────────────────────────────────────────┤
│                   Execution Layer                     │
│  LangGraph StateGraph + Checkpoint (SQLite)           │
│  AgentLoop → SkillExecutor → LLMProvider              │
│  HITL interrupts @ strategy_approval, testcase_gate   │
├─────────────────────────────────────────────────────┤
│                   Observation Layer                   │
│  Trace Logger (JSONL) + Trace Replay UI               │
│  Cost Advisor + Failure Attributor                    │
└─────────────────────────────────────────────────────┘
```
