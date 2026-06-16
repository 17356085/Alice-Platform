# LangGraph 逆向拆解：把鞍集涂源管理系统的图引擎映射到 LangGraph 理论体系

> **写作目的**: 教学文档。以本项目为真实案例，从 0 开始逆向拆解其 LangGraph 设计，帮助理解 LangGraph 的每个核心概念在实际工程中如何落地。
> **读者假设**: 已了解 LangGraph 的基本概念（StateGraph、Node、Edge），希望看到一个生产级的完整案例。
> **配套阅读**: 建议同时打开 `aitest/graphs/` 目录对照代码。

---

## 0. 先决知识：LangGraph 解决什么问题

在 Agent 工程中，你会遇到以下需求：

```
需求                              LangGraph 提供的概念
─────────────────────────────────────────────────────
多个步骤按顺序执行                Node + Edge
每一步后有分支决策                Conditional Edge  
执行中保存进度，中断后恢复        Checkpoint (SqliteSaver)
循环执行直到某个条件满足          Conditional Edge 指向上游节点
需要人审批后才能继续              interrupt() + Human-in-the-loop
大图嵌套小图                      SubGraph (compiled graph as node)
跨步骤共享状态                    State (TypedDict)
多个节点向同一字段追加            Annotated[list, operator.add]
```

本项目的 `aitest/graphs/` 恰好覆盖了所有这些概念。下面逐一映射。

---

## 1. 全景：这套系统有多少个 Graph？

在开始分析节点之前，先建立全局视图。本项目 LangGraph 体系包含 **1 个顶层图 + 4 个活跃 SubGraph + 2 个已归档 SubGraph**：

```
sop_graph.py (顶层 StateGraph)
├── entry                          ← 入口节点
├── preflight                      ← 起飞前检查
├── project_agent                  ← AgentLoop (P0-1 统一: 不再有独立 SubGraph)
├── requirement_agent              ← AgentLoop
├── test_design_agent              ← AgentLoop
├── automation_agent               ← AgentLoop
├── execution_agent ──→ execution_graph.py (SubGraph)
│                         ├── entry → act → gate → exit
├── bug_analysis_agent ─→ bug_analysis_graph.py (SubGraph)
│                         ├── entry → analyze_fail → auto_fix
│                         │     → request_approval → verify
│                         │     → report → exit
│                         └── 条件路由: verify → analyze_fail (loop)
├── report_agent ──────→ execution_graph.py (SubGraph)
│                         ├── entry → act → exit
├── knowledge_agent ───→ execution_graph.py (SubGraph)
│                         ├── entry → act → exit (+ EventBus + RAG)
└── exit                          ← 出口节点

_archived/ (P0-1 归档 — 设计演化史):
├── project_graph.py              ← 8 节点 AgentLoop SubGraph (已被 AgentLoop 替代)
├── requirement_graph.py          ← 8 节点 AgentLoop SubGraph (已被 AgentLoop 替代)
├── test_design_graph.py          ← 同模式 (已被 AgentLoop 替代)
└── automation_graph.py           ← 同模式 (已被 AgentLoop 替代)
```

**关键设计决策（为什么有 SubGraph vs AgentLoop 之分）**：

```
Agent 类型                      LangGraph 实现              原因
────────────────────────────────────────────────────────────────────
project-agent                  make_agent_loop_node()      简单 Skill 链，不需要图
requirement-agent              make_agent_loop_node()      简单 Skill 链，不需要图
test-design-agent              make_agent_loop_node()      简单 Skill 链，不需要图
automation-agent               make_agent_loop_node()      简单 Skill 链，不需要图
execution-agent                build_execution_subgraph()  需要 execution_failed 标志影响顶层路由
bug-analysis-agent             build_bug_analysis_compiled() 需要循环 + HITL interrupt
report-agent                   build_report_subgraph()     需要多 Skill 节点
knowledge-agent                build_knowledge_subgraph()  需要 EventBus + RAG 索引
```

---

## 2. LangGraph 概念 #1: State（状态）

> **LangGraph 理论**: State 是流经所有节点的共享字典。每个节点读取 State，返回 State 的部分更新。LangGraph 自动合并更新。

### 本项目的 State 定义

文件: [aitest/graphs/state.py:194-249](aitest/graphs/state.py#L194)

```python
class SOPState(TypedDict):
    # ── 运行时标识 (一次性写入，流转不变) ──
    module: str                              # "equipment"
    pages: List[str]                         # ["alarm-config", "unit-management"]
    mode: SOPMode                            # "full" | "resume" | "from-automation" | ...
    provider: str                            # "claude" | "openai" | "ollama"
    run_id: str                              # "sop-equipment-1718300000"

    # ── Phase 状态机 (随节点流转而更新) ──
    current_phase: PhaseName                 # "Preflight" → "Project Init" → ...
    completed_phases: Annotated[List, operator.add]    # ★ 自动累积
    failed_phases: Annotated[List, operator.add]       # ★ 自动累积
    skip_phases: List[PhaseName]             # mode 决定的跳过列表

    # ── Per-page 迭代 ──
    current_page_index: int                  # 0-based，驱动页面循环
    per_page_results: Annotated[List, operator.add]    # ★ 自动累积

    # ── Agent 输出 (编排↔Agent 接口) ──
    agent_outputs: Dict[str, Any]            # agent_name → AgentResult
    artifact_map: Dict[str, List[str]]       # phase → 产物文件路径
    skill_observations: Annotated[List, operator.add]  # ★ 自动累积

    # ── Bug-analysis 自动循环 ──
    bug_cycle_count: int                     # 当前循环次数
    bug_cycle_max: int                       # 最大循环次数 (默认 3)
    fix_approved: Optional[bool]             # None=等待中, True=批准, False=拒绝

    # ── Human-in-the-loop ──
    interrupt_requested: bool
    human_input: Optional[str]

    # ── 门禁 ──
    gate_results: Annotated[List, operator.add]   # ★ 自动累积

    # ── 错误 ──
    fatal_error: Optional[str]               # 非 None → 立即终止
    status: str                              # "running" | "completed" | "failed"
```

### 为什么这样设计 State？

**① 混合合并策略**

State 中同时使用了两种合并策略：

| 字段 | 合并策略 | 原因 |
|------|---------|------|
| `module`, `mode`, `status` | **覆盖** (默认) | 单一事实，后来的值覆盖先前的 |
| `completed_phases` | **追加** (`operator.add`) | 每个 Agent 往列表里追加它完成的 Phase |
| `failed_phases` | **追加** (`operator.add`) | 同上 |
| `gate_results` | **追加** (`operator.add`) | 每个门禁节点追加检查结果 |
| `skill_observations` | **追加** (`operator.add`) | 每个 Skill 执行后追加观察 |
| `agent_outputs` | **覆盖** (`operator.add` 不适用) | 需要整体替换，不是追加（用 `{**prev, new_key: val}` 模式） |

这是 LangGraph 的**核心能力**：不同的字段可以有不同的 reducer。

**② AgentResult 封装 — P2-4 分层**

```python
@dataclass
class AgentResult:
    """单个 Agent 的执行结果，存储在 agent_outputs[agent_name] 中。"""
    agent_name: str
    success: bool
    completed_skills: List[str]
    failed_skills: Dict[str, str]
    retry_counts: Dict[str, int]
    execution_failed: bool          # execution-agent 特有
```

**设计思想**: Agent 内部状态（skills/retries/observations）封装在 `AgentResult` 中，不污染顶层 State。顶层 State 只有编排级字段（Phase/Page/错误状态）。

这是**关注点分离**在 State 设计中的体现：编排器不需要知道 Agent 内部重试了多少次，只需要知道 Agent 成功还是失败。

### 与 LangGraph 理论的映射

| LangGraph 概念 | 本项目对应 |
|---------------|-----------|
| `TypedDict` State | `SOPState` |
| Reducer (合并策略) | `Annotated[List[PhaseName], operator.add]` |
| Default reducer (覆盖) | `module: str`, `status: str` 等 |
| Nested state | `agent_outputs: Dict[str, AgentResult]` |
| State factory | `create_initial_state(module, pages, mode)` |

---

## 3. LangGraph 概念 #2: Node（节点）

> **LangGraph 理论**: Node 是一个 Python 函数，签名为 `(state: State) -> dict`。它读取当前状态，返回一个部分状态更新字典。LangGraph 自动将返回的 dict 合并到当前 State。

### 本项目的所有节点（20+ 个）

我按功能将它们分为 6 类：

#### 类型 A: 编排节点（顶层图）

```python
# ① entry_node — 入口初始化
def entry_node(state: SOPState) -> dict:
    mode = state.get("mode", "full")
    skip_phases = list(MODE_SKIP_MAP.get(mode, []))
    return {
        "skip_phases": skip_phases,
        "current_phase": "Preflight",
        "status": "running",
    }
```

**职责**: 根据 mode 决定跳过哪些 Phase。`from-automation` 模式跳过 Project Init / Requirement / Test Design 三个 Phase。

**输入**: 初始状态（module, pages, mode, provider）
**输出**: `skip_phases` 列表 + `status="running"`
**状态流转**: `status: None → "running"`, `skip_phases: [] → ["Project Init", "Requirement", "Test Design"]`（取决于 mode）

**为什么需要**: 如果 State 的初始值就能覆盖所有字段，为什么还需要 entry_node？因为有些状态需要**基于其他状态计算**。`skip_phases` 是根据 `mode` 推导出来的——它不是用户输入，而是编排逻辑。

---

```python
# ② preflight_node — 起飞前检查
def preflight_node(state: SOPState) -> dict:
    # 检查 PROJECT_CONTEXT.md 是否存在
    # 检查 MODULE_CONTEXT.md 是否存在
    # 自动发现模块下的所有页面
    # 检查每个页面的产物 (PAGE_CONTEXT, TEST_CASES, TECH_ANALYSIS, ...)
    # 自动检测推荐 mode（如果用户选了 full 但其实可以从 from-automation 开始）
    # 返回 artifact_map, per_page_results, completed_phases (resume 模式)
    return {
        "pages": pages,                     # 自动发现的页面列表
        "per_page_results": [...],          # 每个页面的产物检查结果
        "artifact_map": {...},              # phase → 文件路径
        "completed_phases": [...],          # resume 模式从 SOP_STATUS 恢复
        "agent_outputs": {
            "preflight_auto_detect": {...}, # 推荐 mode + 理由
        },
    }
```

**职责**: 扫描文件系统，确定 "已经做了什么" 和 "还需要做什么"。

**输入**: `module`, `mode`, `pages`（可能为空）
**输出**: `pages`（自动发现）, `per_page_results`, `artifact_map`, `agent_outputs.preflight_auto_detect`
**状态流转**: `pages: [] → ["alarm-config", "unit-management"]`, 填充 `artifact_map`

**为什么需要**: 这是 LangGraph 的 **动态路由前提**。没有 preflight 节点，`route_next_phase` 就无从判断哪些 Phase 已完成。preflight 是**数据驱动路由的感知层**。

---

```python
# ③ exit_node — 出口
def exit_node(state: SOPState) -> dict:
    # 确定最终状态 (completed / completed_with_issues / failed)
    # 写入 SOP_STATUS_<module>.json
    # 发射 CycleEnd 事件到 EventBus
    return {
        "status": final_status,          # "completed" | "failed" | "completed_with_issues"
        "current_phase": "Complete",
    }
```

**职责**: 持久化最终状态，发射事件通知 Knowledge Agent。

**输入**: `module`, `completed_phases`, `failed_phases`, `fatal_error`, `pages`, `run_id`
**输出**: `status`, 文件系统副作用（JSON 文件 + EventBus 事件）
**状态流转**: 标记流水线终结状态

**为什么需要**: LangGraph 图中需要一个明确的 **END 节点**。没有它，图执行完成但没有持久化记录——你无法回答 "上次做到哪了"。

#### 类型 B: Agent 节点（顶层图，4 个统一为 AgentLoop）

```python
# ④~⑦ project_agent, requirement_agent, test_design_agent, automation_agent
builder.add_node("project_agent", make_agent_loop_node("project-agent"))
builder.add_node("requirement_agent", make_agent_loop_node("requirement-agent"))
builder.add_node("test_design_agent", make_agent_loop_node("test-design-agent"))
builder.add_node("automation_agent", make_agent_loop_node("automation-agent"))
```

**职责**: 每个节点内部调用 `AgentLoop(agent_name).run()`，执行 Agent 的 Skill 链，返回 AgentResult。

**输入**: 当前 State（特别是 `module`, `page`, `provider`）
**输出**: `agent_outputs[agent_name] = AgentResult(...)`, `completed_phases: [phase]` 或 `failed_phases: [phase]`
**状态流转**: Agent 内部状态封装在 AgentResult 中，顶层只更新 Phase 完成/失败状态

**为什么设计成 AgentLoop 包装节点**: 这是 P0-1 架构统一的核心。在此之前，每个 Agent 有自己独立的 SubGraph（8 节点循环）——这造成了：
- 4 个 SubGraph 几乎完全相同，只有 Skill 列表不同
- AgentLoop 和 SubGraph 双重实现，修改要改两处
- SubGraph 的 8 节点粒度对简单的 Skill 链来说过度设计

统一后：简单的 Skill 链 Agent → `make_agent_loop_node()`；需要循环/HITL 的 Agent → 保留 SubGraph。

#### 类型 C: SubGraph 节点（顶层图，3 个保留 SubGraph）

```python
# ⑧ execution_agent → execution_graph.py SubGraph
builder.add_node("execution_agent", build_execution_subgraph().compile())

# ⑨ bug_analysis_agent → bug_analysis_graph.py SubGraph (最复杂)
builder.add_node("bug_analysis_agent", build_bug_analysis_compiled())

# ⑩ report_agent → execution_graph.py SubGraph
builder.add_node("report_agent", build_report_subgraph().compile())

# ⑪ knowledge_agent → execution_graph.py SubGraph
builder.add_node("knowledge_agent", build_knowledge_subgraph().compile())
```

这些节点的内部结构在后面详细展开。

#### 类型 D: Bug Analysis SubGraph 内部节点（6 个）

这是整个系统最复杂的 SubGraph，独立分析：

```python
# bug_entry — 初始化循环计数器
def bug_entry(state) -> dict:
    return {
        "current_phase": "Bug Analysis",
        "bug_cycle_count": 0,
        "fix_approved": None,
    }

# analyze_fail_node — RAG + LLM 根因分析
def analyze_fail_node(state) -> dict:
    # 1. RAG 搜索已知问题 (search_known_issues)
    # 2. 跨模块搜索技术分析 (search_context, collection="tech_analysis")
    # 3. 跨模块搜索页面模式 (search_context, collection="page_context")
    # 4. LLM 深度分析 (run_skill "diagnosis/bug-analysis")
    return {"agent_outputs": {"bug_analysis": {...}}}

# auto_fix_node — 自动生成修复代码
def auto_fix_node(state) -> dict:
    # 调用 run_skill("automation/page-object-generator", mode="fix")
    return {"agent_outputs": {"bug_fix": {...}}}

# request_approval_node — ★ Human-in-the-loop
def request_approval_node(state) -> dict:
    approval = interrupt({                      # ← LangGraph interrupt()
        "type": "bug_fix_approval",
        "cycle": f"{cycle + 1}/3",
        "analysis_summary": "...",
        "fix_summary": "...",
        "options": ["approve", "reject", "skip"],
    })
    return {"fix_approved": approval == "approve"}

# verify_node — 重新运行测试验证修复
def verify_node(state) -> dict:
    # subprocess.run(["pytest", test_file, "-v", "--tb=short"])
    return {"bug_cycle_count": cycle + 1, "agent_outputs": {"bug_verify": {...}}}

# generate_report_node — 生成 Bug 分析报告
def generate_report_node(state) -> dict:
    # 确定最终 resolution: fixed | rejected_by_human | max_cycles_exceeded
    return {"agent_outputs": {"bug_report": {...}}}

# bug_exit — 标记 Phase 完成
def bug_exit(state) -> dict:
    return {"completed_phases": ["Bug Analysis"]}
```

**状态流转（Bug Analysis 的完整生命周期）**:

```
bug_cycle_count: 0 ──→ 1 ──→ 2 ──→ 3 (max)
fix_approved: None ──→ True ──→ None (reset) ──→ ...
bug_analysis 数据: {} ──→ {rag_matches, deep_analysis}
bug_fix 数据:     {} ──→ {cycle, fix_content}
bug_verify 数据:  {} ──→ {cycle, passed: False} ──→ {cycle, passed: True}
```

#### 类型 E: Execution/Report/Knowledge SubGraph 内部节点（轻量）

```python
# execution_graph.py 中的节点

# exec_entry — 设置当前 Phase
def exec_entry(state) -> dict:
    return {"current_phase": "Execute & Debug"}

# exec_act — 运行 pytest（内部调 AgentLoop）
def exec_act(state) -> dict:
    agent = AgentLoop("execution-agent", ...)
    result = agent.run()
    exec_failed = bool(result.failed_skills and len(result.failed_skills) > 0)
    return {
        "agent_outputs": {
            "execution-agent": result.to_dict(),
            "execution_failed": exec_failed,  # ← 顶层路由依赖这个标志
        },
    }

# exec_gate — 检查 allure-results 目录
def exec_gate(state) -> dict:
    allure_dir = ZJSN_TEST / "allure-results"
    ok = allure_dir.exists() and any(allure_dir.iterdir())
    return {"gate_results": [GateResult(...).to_dict()]}

# exec_exit — 标记 Phase 完成
def exec_exit(state) -> dict:
    return {"completed_phases": ["Execute & Debug"]}

# report_entry / report_act / report_exit — Report Agent 的 3 节点线性流程
# knowledge_entry / knowledge_act / knowledge_exit — Knowledge Agent 的 3 节点
# knowledge_act 额外处理: EventBus process_pending() + RAG index_* calls
```

#### 类型 F: 已归档的 Perceive→Plan→Act→Observe→Update 节点（_archived/）

```python
# project_graph.py — 已被 AgentLoop 替代，但作为设计演化史料保留

# proj_entry    → 初始化
# proj_perceive → 检查现有产物
# proj_plan     → 决定下一个 Skill
# proj_act      → 调用 LLM 执行 Skill
# proj_observe  → 验证产出（文件存在性检查）
# proj_update   → 更新完成/失败/重试计数
# proj_gate     → Phase 门禁检查
# proj_exit     → 标记 Phase 完成
```

这些节点精确对应了 AgentLoop 的 Perceive→Plan→Act→Observe→Update 循环，但每个步骤都是独立的 LangGraph 节点。在 P0-1 统一后，这个循环被压缩为一个 `AgentLoop.run()` 调用。

---

## 4. LangGraph 概念 #3: Edge（普通边）

> **LangGraph 理论**: `add_edge(from, to)` 创建一条从 `from` 到 `to` 的固定边。执行完 `from` 节点后，**无条件**转入 `to` 节点。

### 本项目中的普通边

```python
# 顶层图 — 固定流程
builder.add_edge("entry", "preflight")     # 入口 → 检查
builder.add_edge("exit", END)              # 出口 → 结束

# Bug Analysis SubGraph — 内部固定流程
builder.add_edge("entry", "analyze_fail")          # 入口 → 分析
builder.add_edge("analyze_fail", "auto_fix")       # 分析 → 修复
builder.add_edge("auto_fix", "request_approval")   # 修复 → 审批
builder.add_edge("request_approval", "verify")     # 审批 → 验证（无论批准与否）
builder.add_edge("report", "exit")                 # 报告 → 出口
builder.add_edge("exit", END)

# Execution SubGraph
builder.add_edge("entry", "act")
builder.add_edge("act", "gate")
builder.add_edge("gate", "exit")
builder.add_edge("exit", END)

# Report / Knowledge SubGraph
builder.add_edge("entry", "act")
builder.add_edge("act", "exit")
builder.add_edge("exit", END)
```

**设计观察**: 普通边用于**确定性流转**——"执行完 A 后一定执行 B"。如果下一个节点有分支可能，使用条件边。

---

## 5. LangGraph 概念 #4: Conditional Edge（条件边）

> **LangGraph 理论**: `add_conditional_edges(source, router_fn, route_map)` — 从 `source` 出发，执行 `router_fn(state)` 返回一个字符串，根据 `route_map` 映射到下一个节点。

这是 LangGraph 最强大的概念之一。没有条件边，LangGraph 就是 DAG（有向无环图）；有了条件边，LangGraph 可以表达**循环**和**动态分支**。

### 本项目的条件边

#### ① `route_next_phase` — 整个系统最核心的路由函数

```python
# sop_graph.py:347-392
def route_next_phase(state: SOPState) -> str:
    # 致命错误 → 立即退出
    if state.get("fatal_error"):
        return "exit"

    # Status 模式 → preflight 后直接退出（只显示状态）
    if state.get("mode") == "status":
        return "exit"

    completed = set(state.get("completed_phases", []))
    skipped = set(state.get("skip_phases", []))

    # ★ 关键逻辑：Bug Analysis 仅当执行失败时才触发
    execution_failed = state.get("agent_outputs", {}).get("execution_failed", False)

    for phase in CANONICAL_PHASES:
        if phase in completed or phase in skipped:
            continue

        if phase == "Bug Analysis" and not execution_failed:
            continue  # 跳过 Bug Analysis，自动进入 Report

        node_name = PHASE_TO_NODE.get(phase)
        if node_name:
            return node_name

    return "exit"

# 注册条件边 — 从 preflight 和每个 Agent 节点出发
builder.add_conditional_edges("preflight", route_next_phase, route_map)
for node_name in ALL_AGENT_NODES:
    builder.add_conditional_edges(node_name, route_next_phase, route_map)
```

**这是 LangGraph 条件边的经典用例**: 同一个路由函数被挂载到多个源节点上。每个 Agent 执行完后都走同一个 `route_next_phase`，决定下一个要执行的节点。

**route_map 映射**:
```python
route_map = {
    "project_agent": "project_agent",
    "requirement_agent": "requirement_agent",
    ...
    "exit": "exit",
}
```
这个 1:1 映射看起来多余，但它是 LangGraph 的条件边契约——路由函数返回的字符串必须映射到一个已注册的节点名。

**状态驱动的条件逻辑**:

```
┌─────────────┬────────────────────┬──────────────────┐
│ State 条件   │ route_next_phase   │ 下一节点          │
├─────────────┼────────────────────┼──────────────────┤
│ fatal_error │ → "exit"           │ exit → END        │
│ mode=status │ → "exit"           │ exit → END        │
│ execution_failed=False          │ 跳过 Bug Analysis  │
│ + Bug Analysis done            │                   │
│ 所有 Phase 完成                 │ → "exit"           │ exit → END        │
│ 正常推进     │ → next agent node │ project_agent 等   │
└─────────────┴────────────────────┴──────────────────┘
```

#### ② `loop_router` — Bug Analysis 的循环条件

```python
# bug_analysis_graph.py:269-301
def loop_router(state: SOPState) -> Literal["loop", "report"]:
    cycle = state.get("bug_cycle_count", 0)
    bug_cycle_max = state.get("bug_cycle_max", 3)
    approved = state.get("fix_approved")
    verify_result = state.get("agent_outputs", {}).get("bug_verify", {})

    # 被拒绝 → 立即退出循环
    if approved is False:
        return "report"

    # 达到最大次数 → 退出
    if cycle >= bug_cycle_max:
        return "report"

    # 验证通过 → 退出
    if verify_result.get("passed"):
        return "report"

    # 否则 → 继续循环
    return "loop"

# 注册 — verify 节点后条件分支
builder.add_conditional_edges("verify", loop_router, {
    "loop": "analyze_fail",    # ← 回到 analyze_fail，形成循环
    "report": "report",        # → 生成报告
})
```

**这是 LangGraph 实现循环的标准模式**: 条件边指回上游节点。

```
                    ┌──────────────────────────┐
                    │                          │
                    ▼                          │
analyze_fail → auto_fix → request_approval → verify
                    │                          │
                    │              条件: loop_router
                    │              ├─ "loop" → analyze_fail (继续)
                    │              └─ "report" → report → exit
                    │
                    └── "report" → report → exit
```

#### ③ `proj_router` / `req_router` — 已归档的 Skill 级重试路由

```python
# _archived/project_graph.py:105-119
def _router(state) -> Literal["continue", "retry", "gate_check"]:
    last = observations[-1]
    suggestion = last.get("suggestion", "continue")
    if suggestion == "retry" and retry_count < 3:
        return "retry"          # → plan → 重试同一个 Skill
    if suggestion in ("continue", "skip"):
        return "continue"       # → plan → 选择下一个 Skill
    return "gate_check"         # → gate → exit
```

**三层路由映射**:
```
"continue"   → plan 节点（选择下一个 Skill）
"retry"      → plan 节点（再次选择同一个 Skill）
"gate_check" → gate 节点（门禁检查 → exit）
```

三种路由都回到 `plan` 或 `gate`，这构成了 AgentLoop 内部的核心循环。

---

## 6. LangGraph 概念 #5: Checkpoint（检查点）

> **LangGraph 理论**: Checkpoint 在每执行一个节点（或 `interrupt()` 调用时）自动保存完整 State。`SqliteSaver` 是 LangGraph 内置的 SQLite 持久化实现。通过 `thread_id` 区分不同的运行实例。

### 本项目的 Checkpoint 实现

文件: [aitest/graphs/checkpoint.py](aitest/graphs/checkpoint.py)

```python
from langgraph.checkpoint.sqlite import SqliteSaver

def get_checkpointer() -> SqliteSaver:
    conn = sqlite3.connect(
        "governance/.graph_state/checkpoints.sqlite",
        check_same_thread=False
    )
    return SqliteSaver(conn)
```

### Checkpoint 在项目中的三个用途

#### 用途 1: 断点续跑（Resume）

```python
# 第一次运行（可能中断）
graph.invoke(state, {"configurable": {"thread_id": "sop-equipment-001"}})
# 执行到 automation_agent 时 API 超时...

# 用同一个 thread_id 恢复 — LangGraph 自动从最后一个 checkpoint 继续
graph.invoke(None, {"configurable": {"thread_id": "sop-equipment-001"}})
```

**底层原理**: `SqliteSaver` 在 SQLite 中存储每次节点执行后的完整 State。当 `invoke` 收到一个已存在的 `thread_id`，它读取最新 checkpoint，从下一个节点继续。

#### 用途 2: 时间旅行调试

```python
# 查看某个 run 的最新状态
state = compiled.get_state({"configurable": {"thread_id": "sop-equipment-001"}})
print(state.values)  # 完整的 SOPState 字典

# 列出所有历史 run
runs = list_runs(limit=20)
# [{"run_id": "sop-equipment-001", "updated_at": "2026-06-14T10:30:00"}, ...]
```

**设计亮点**: `list_runs()` 直接查询 SQLite，不依赖文件系统。这使 CLI 的 `aitest graph status` 和 `aitest graph list` 命令能快速列出所有运行。

#### 用途 3: 多模块隔离

```python
def get_checkpointer_for_thread(thread_id: str) -> SqliteSaver:
    db_path = CHECKPOINT_DIR / f"{thread_id}.sqlite"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    return SqliteSaver(conn)
```

不同模块使用独立的 SQLite 数据库，避免 checkpoint 冲突。例如：
- `equipment` 模块 → `governance/.graph_state/sop-equipment.sqlite`
- `system-user` 模块 → `governance/.graph_state/sop-system-user.sqlite`

### Checkpoint 的自动触发时机

LangGraph 在以下时机自动保存 checkpoint：
1. 每个节点执行完成后
2. `interrupt()` 被调用时（暂停前保存）
3. 图执行完成时

这意味着**每个节点 = 一个 checkpoint**。如果图有 11 个节点，执行中断在第 7 个，就有 7 个 checkpoint 可供回溯。

---

## 7. LangGraph 概念 #6: Human-in-the-Loop (HITL)

> **LangGraph 理论**: `interrupt()` 函数在图执行中**挂起**，将控制权交还给调用方。调用方做出决策后，通过 `Command(resume=value)` 恢复执行。`interrupt()` 的返回值就是 `Command(resume=value)` 中的 `value`。

### 本项目的 HITL 实现

```python
# bug_analysis_graph.py:188-216
def request_approval_node(state: SOPState) -> dict:
    cycle = state.get("bug_cycle_count", 0)
    bug_cycle_max = state.get("bug_cycle_max", 3)

    # ★ 执行在此暂停 — 等待人类输入
    approval = interrupt({
        "type": "bug_fix_approval",
        "cycle": f"{cycle + 1}/{bug_cycle_max}",
        "module": state["module"],
        "page": _get_first_page(state),
        "analysis_summary": "...",     # 根因分析摘要
        "fix_summary": "...",          # 修复方案摘要
        "options": ["approve", "reject", "skip"],
    })

    # 人类输入到达后 — 从这里继续执行
    approved = approval == "approve"
    return {
        "fix_approved": approved,
        "human_input": str(approval),
    }
```

### HITL 的执行流程

```
图执行进行中:
  analyze_fail ✓ → auto_fix ✓ → request_approval [⏸️ 挂起]
                                    │
                                    │ interrupt() 返回
                                    │ {"type": "bug_fix_approval", ...}
                                    │
调用方 (CLI / MCP tool):            │
  1. 收到 interrupt 值              │
  2. 展示给人类:                    │
     "修复方案: 将 time.sleep(3) 替换为 wait_vue_stable()"
     "请选择: [approve] [reject] [skip]"
  3. 人类选择 "approve"             │
  4. 调用 Command(resume="approve") │
                                    │
                                    ▼
  request_approval 恢复 → approval = "approve"
  fix_approved = True → verify → (pass → report / fail → loop)
```

### 为什么 HITL 在循环**内部**？

这是关键的架构决策。对比两种 HITL 位置：

```
❌ HITL 在循环外部:
   analyze → fix → verify (×3) → 【人类看最终结果】
   问题: 3 次修复都可能是错误的，但人类只在最后看一次

✅ HITL 在循环内部（本项目）:
   analyze → fix → 【人类审批】 → verify → (pass ✓ / fail → analyze)
   优势: 每次修复方案在执行前都经过人类审批
```

### 与 LangGraph 理论的映射

| LangGraph 概念 | 本项目实现 |
|---------------|-----------|
| `interrupt(value)` | `request_approval_node` 中的 `interrupt({...})` |
| `Command(resume=value)` | 调用方通过 CLI/MCP tool 传入审批结果 |
| Interrupt 的返回值 | `approval` 变量 = `"approve"` / `"reject"` / `"skip"` |
| 挂起时的状态保存 | SqliteSaver 自动在 interrupt 前保存 checkpoint |

---

## 8. LangGraph 概念 #7: SubGraph（子图）

> **LangGraph 理论**: 一个已编译的 StateGraph 可以作为另一个 StateGraph 的节点使用。`builder.add_node("name", compiled_subgraph)`。LangGraph 自动处理子图的状态传递。

### 本项目的 SubGraph 组合

```python
# sop_graph.py:416-441
def build_sop_graph(use_subgraphs: bool = True) -> StateGraph:
    builder = StateGraph(SOPState)

    # 简单节点
    builder.add_node("entry", entry_node)
    builder.add_node("preflight", preflight_node)
    builder.add_node("exit", exit_node)

    if use_subgraphs:
        # AgentLoop 包装节点（非 SubGraph，是普通节点）
        builder.add_node("project_agent", make_agent_loop_node("project-agent"))

        # ★ 编译后的 SubGraph 作为节点
        builder.add_node("execution_agent",
            build_execution_subgraph().compile())          # 4 节点子图
        builder.add_node("report_agent",
            build_report_subgraph().compile())             # 3 节点子图
        builder.add_node("knowledge_agent",
            build_knowledge_subgraph().compile())          # 3 节点子图
        builder.add_node("bug_analysis_agent",
            build_bug_analysis_compiled())                 # 7 节点子图
```

### SubGraph 的状态传递

LangGraph 自动处理父图和子图之间的 State 传递：

```
父图 state ──→ 子图 entry 节点（接收完整 state）
子图内部节点更新 state
子图 exit 节点返回更新 ──→ 父图 state（自动合并）
```

这意味着 `execution_graph.py` 中的 `exec_act` 返回的 `{"agent_outputs": {"execution_failed": True}}` 会自动合并到父图的 State，被 `route_next_phase` 读取。

### 为什么这些 Agent 保留 SubGraph 而其他统一为 AgentLoop？

```
SubGraph 保留的 Agent              保留原因
──────────────────────────────────────────────────────
execution-agent    exec_act 返回的 execution_failed 标志
                   是顶层 route_next_phase 的输入
                   — 需要显式的节点返回值控制

bug-analysis-agent 需要 7 个节点的复杂循环 + HITL
                   — AgentLoop 无法表达

report-agent       多 Skill 节点 (report_act, optionally report_act2)
                   — 未来可能扩展多模式节点

knowledge-agent    act 节点内执行 EventBus + RAG 索引
                   — 这些是 LangGraph 节点边界外的副作用
                   但 execution_graph 作为容器组织它们
```

---

## 9. LangGraph 概念 #8: Memory（记忆）

> **LangGraph 理论**: LangGraph 区分两种 "记忆"：
> - **Short-term memory**: State 本身，在单次图执行中流转
> - **Long-term memory**: Checkpoint (SqliteSaver)，跨执行持久化
> - 此外还有 **external memory**: 向量数据库、知识库等（超出 LangGraph 范畴，但 Agent 常与之集成）

### 本项目中的三层记忆

| 层级 | 实现 | 生命周期 | 存储内容 |
|------|------|---------|---------|
| **短期记忆** | SOPState (in-memory) | 单次图执行 | Phase 状态、Agent 输出 |
| **中期记忆** | AgentLoop.memory dict | 单个 Agent 执行内 | 前一个 Skill 的产出摘要、调整建议 |
| **长期记忆** | SqliteSaver | 跨执行/跨会话 | 完整的 SOPState checkpoint |
| **外部记忆** | ChromaDB RAG (5 集合) | 永久 | known_issues, tech_analysis, page_context 等 |

### 短期记忆: SOPState 的字段选择

看 State 中的 `artifact_map` 字段：
```python
artifact_map: Dict[str, List[str]]    # phase → 产物文件路径
```

这是一个 **记忆辅助字段**。它不参与路由决策，但在 HITL 中断时提供了上下文——当人类看到审批请求时，`artifact_map` 告诉他们 "之前已经生成了哪些文件"。

### 中期记忆: AgentLoop 的 memory

```python
# agent_runner.py:298
memory: dict = field(default_factory=dict)  # accumulated knowledge

# 使用示例
self.state.memory["prev_output"] = observation.summary
self.state.memory["tech_analysis_summary"] = ...
self.state.memory["retry_adjustments"] = adjustments  # LLM 规划器的调整建议
```

**为什么 AgentLoop 需要自己的 memory？** 因为 Agent 内部的 5 个 Skill 之间有依赖关系。`page-object-generator` 需要知道 `tech-analysis` 的分析结果。这种**Skill 间的知识传递**不适合放在顶层 State（那会污染编排器关心的状态），所以 AgentLoop 维护自己的 memory dict。

### 长期记忆: Checkpoint 的持久化

```
governance/.graph_state/
├── checkpoints.sqlite          ← 默认数据库
├── sop-equipment.sqlite        ← 模块级隔离
├── sop-system-user.sqlite
└── ...
```

每个 SQLite 数据库中，LangGraph 维护以下表结构（自动管理）：
- `checkpoints` — 完整状态快照
- `checkpoint_blobs` — 大字段的二进制存储
- `checkpoint_writes` — 待处理的写入

### 外部记忆: RAG 向量检索

在 `bug_analysis_graph.py` 的 `analyze_fail_node` 中：

```python
rag_matches = search_known_issues(query, n_results=5)         # ChromaDB
cross_module_hits = search_context(query, "tech_analysis")    # 跨模块
page_hits = search_context(query, "page_context")             # 跨页面
```

这层记忆超出了 LangGraph 的范畴，但它是 Agent 系统的关键部分——**语义记忆 (Semantic Memory)**。Checkpoint 记住了 "发生了什么"，RAG 记住了 "知道什么"。

---

## 10. LangGraph 概念 #9: Command（恢复执行）

> **LangGraph 理论**: 当图因 `interrupt()` 挂起后，使用 `Command(resume=value)` 恢复执行。`Command` 还可以用于 `goto` 跳转到任意节点。

### 本项目的使用方式

虽然项目的 CLI 入口代码在 `cli.py`（未展开详读），但从 bug_analysis_graph 的设计可以推断出使用模式：

```python
# 伪代码 — CLI 层的 HITL 处理
from langgraph.types import Command

# 运行图，遇到 interrupt 时返回
for event in compiled.stream(state, config):
    if "interrupt" in event:
        # 向用户展示审批请求
        interrupt_data = event["interrupt"]
        print(f"修复方案: {interrupt_data['fix_summary']}")
        choice = input("选择 [approve/reject/skip]: ")

        # 用 Command(resume=...) 恢复
        for event in compiled.stream(Command(resume=choice), config):
            # 继续处理后续事件
            ...
```

### Command 的两种用法

| 用法 | 语法 | 本项目场景 |
|------|------|-----------|
| Resume | `Command(resume=value)` | HITL 审批后的恢复 |
| Goto | `Command(goto="node_name")` | 尚未使用（潜力：手动跳过某个 Phase） |

---

## 11. 架构演化：P0-1 SubGraph → AgentLoop 统一

这是理解本项目 LangGraph 设计的关键演化。我把全过程还原出来。

### Phase 0 (v1.0): 4 个独立 SubGraph，每个都有 8 节点循环

```
project_graph.py:    entry → perceive → plan → act → observe → update → gate → exit
requirement_graph.py: entry → perceive → plan → act → observe → update → gate → exit
test_design_graph.py: entry → perceive → plan → act → observe → update → gate → exit
automation_graph.py:  entry → perceive → plan → act → observe → update → gate → exit
                       ↑                           ↑
                       完全相同                    相同（仅 Skill 列表不同）
```

**问题**: 4 个 SubGraph 代码几乎完全相同。修改 Perceive→Plan→Act→Observe 循环逻辑要改 4 处。

### Phase 1 (P0-1): 拆出 AgentLoop，4 个 SubGraph → 4 个 pass-through 节点

```python
# 临时方案 — nodes.py:120
def make_pass_through_node(agent_name):
    def pass_through(state):
        agent = AgentLoop(agent_name, ...)
        result = agent.run()
        return {"completed_phases": [phase], ...}
    return pass_through

# 顶层图
builder.add_node("project_agent", make_pass_through_node("project-agent"))
```

**思想**: 让 AgentLoop 包揽感知→规划→执行→观察，LangGraph 节点变成薄薄的 wrapper。

### Phase 2 (P0-1 最终): make_agent_loop_node — 标准化封装 + AgentResult 分层

```python
# nodes.py:25-113
def make_agent_loop_node(agent_name):
    def agent_loop_node(state: SOPState) -> dict:
        agent = AgentLoop(agent_name, ...)
        loop_state = agent.run()

        # P2-4: 构造 AgentResult 封装内部状态
        agent_result = AgentResult(
            agent_name=agent_name,
            success=loop_state.success,
            completed_skills=list(loop_state.completed_skills),
            failed_skills=dict(loop_state.failed_skills),
            ...
        )

        return {
            "agent_outputs": {agent_name: agent_result.to_dict()},
            "completed_phases": [phase] if success else [],
            "failed_phases": [phase] if not success else [],
        }

    return agent_loop_node
```

**关键改进**: AgentResult 封装了 Agent 内部状态（skills/retries/observations），顶层 State 保持干净。

### 为什么这个演化很重要？

它体现了 LangGraph 设计中的一个核心权衡：

```
LangGraph SubGraph 的粒度选择:

太粗 (1 个节点 = 整个 Agent)    太细 (8 个节点 = 每个 Skill 步骤)
    │                               │
    ├─ 优点: 编排图简单            ├─ 优点: 每个 Skill 可见、可 checkpoint
    │  缺点: 无中间可见性          │  缺点: 编排图复杂、4 个图几乎相同
    │                               │
    └────────── 本项目选择 ─────────┘
                    │
         AgentLoop + AgentResult:
         - 编排层: 1 个节点 (编排图简洁)
         - Agent 层: 5 步循环 (AgentLoop 内部可见)
         - 接口: AgentResult (关键状态透传)
```

**教训**: 不是所有 Agent 的内部步骤都需要在 LangGraph 中作为独立节点存在。判断标准：
- Agent 内部步骤需要影响**顶层路由**？→ 独立节点 / SubGraph
- Agent 内部步骤**不需要**影响顶层路由？→ AgentLoop 足够

---

## 12. LangGraph 概念速查表：本项目映射

| LangGraph 概念 | 本项目中的实现 | 文件位置 |
|---------------|---------------|---------|
| **State** | `SOPState` TypedDict | `state.py:194` |
| **Reducer (追加)** | `Annotated[List, operator.add]` | `state.py:213-216` |
| **Reducer (覆盖)** | 默认 TypedDict 行为 | 大部分字段 |
| **State Factory** | `create_initial_state()` | `state.py:256` |
| **Node** | 20+ 节点函数 (entry, preflight, agent_loop_*, ...) | 所有 graph 文件 |
| **Edge (普通边)** | `add_edge("entry", "preflight")` 等 | `sop_graph.py:457` |
| **Conditional Edge** | `route_next_phase`, `loop_router`, `_router` | 3 个图中的条件路由 |
| **SubGraph** | bug_analysis, execution, report, knowledge | 各自编译后作为父图节点 |
| **Agent as Node** | `make_agent_loop_node()` 工厂 | `nodes.py:25` |
| **Checkpoint** | `SqliteSaver` + SQLite | `checkpoint.py:27` |
| **Thread (隔离)** | `thread_id` = `run_id` | invoke 的 configurable |
| **HITL (interrupt)** | `request_approval_node` | `bug_analysis_graph.py:201` |
| **Command (resume)** | CLI 层调用 `Command(resume=choice)` | `cli.py` (推断) |
| **Memory (短期)** | SOPState (单次执行) | in-memory dict |
| **Memory (长期)** | SqliteSaver checkpoint DB | `.graph_state/` |
| **Memory (语义)** | ChromaDB RAG (5 集合) | `rag_engine.py` |
| **Memory (Agent 内部)** | AgentLoop.memory dict | `agent_runner.py:298` |
| **Streaming** | `compiled.stream(state, config)` | `cli.py` (推断) |
| **get_state** | `compiled.get_state(thread)` | `checkpoint.py:97` |

---

## 13. 从本项目学到的 LangGraph 实践经验

### 经验 1: 路由函数应该是纯数据驱动

```python
# ✅ 好: route_next_phase 只读 state，不读文件系统
def route_next_phase(state: SOPState) -> str:
    if state.get("fatal_error"):
        return "exit"
    ...

# ❌ 不好: 路由函数内部读文件（不可缓存、不可重放）
def bad_router(state):
    if os.path.exists("some/file"):
        return "node_a"
```

### 经验 2: Checkpoint 的 thread_id 应该有业务含义

```python
# ✅ 好: thread_id = "sop-equipment-1718300000"
# 可以从 ID 知道这是 equipment 模块的 run

# ❌ 不好: thread_id = random UUID
# 无法从 ID 知道是哪个模块
```

### 经验 3: 用 Annotated[List, operator.add] 的字段应该是真正需要累积的

```python
# ✅ 需要追加: gate_results — 每个门禁节点追加检查结果
gate_results: Annotated[List[Dict], operator.add]

# ❌ 不需要追加: agent_outputs — 需要整体替换而非追加
agent_outputs: Dict[str, Any]  # 用 {**prev, new_key: val} 手动合并
```

### 经验 4: HITL 的 interrupt 值应该包含足够的上下文让人类决策

```python
# ✅ 好: interrupt 包含分析摘要、修复摘要、选项
interrupt({
    "type": "bug_fix_approval",
    "analysis_summary": "...",   # 为什么需要修复
    "fix_summary": "...",        # 修复方案是什么
    "options": ["approve", "reject", "skip"],
})

# ❌ 不好: interrupt 不提供上下文
interrupt("Approve?")
```

### 经验 5: 不是所有 Agent 内部循环都需要变成 LangGraph 节点

SubGraph 不是免费的——每个节点 = 一次 checkpoint 写入 = 一次状态序列化。20 个节点的 SubGraph 比 1 个 AgentLoop 节点慢很多。只有需要**顶层路由决策**或**HITL interrupt**的步骤才值得作为独立节点。

---

> **文档版本**: 2026-06-14 · 基于项目 P0-1 LangGraph 架构 · 纯教学用途
