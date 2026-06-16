# Agent 设计模式实战分析：9 种模式在鞍集涂源管理系统中的落地

> **写作目的**: 教学文档。从本项目代码中提取 Agent 设计模式的实际应用，每种模式都绑定到具体代码位置。
> **核心论点**: 设计模式的价值不在理论定义，而在它解决了什么实际工程问题。

---

## 模式总览

本项目使用了 **9 种** Agent 设计模式，按架构层级组织：

```
编排层
├── Supervisor (full-sop → sop_graph.py)
├── Router     (route_next_phase / loop_router)
├── State Machine (SOPState + CANONICAL_PHASES)
└── Hierarchical Agent (SOP → Agent → Skill 三级 + LangGraph SubGraph 嵌套)

Agent 层
├── ReAct      (AgentLoop: Perceive→Plan→Act→Observe→Update)
├── Plan & Execute (Test Design Agent → Automation Agent)
├── Reflection (Bug Analysis 循环 / AgentLoop.plan 中的 LLM 自主重试决策)
└── HITL       (Bug Analysis request_approval_node)

系统层
└── Multi-Agent (8 Agent + 文档通信 + 唯一写入原则)
```

---

## 模式 1: ReAct (Reasoning + Acting)

### 在项目中的体现位置

**核心文件**: [aitest/agent_runner.py:422-1168](aitest/agent_runner.py#L422)

AgentLoop 类的 `run()` 方法是 ReAct 模式的完整实现：

```python
# agent_runner.py:1057-1152 (简化)
def run(self) -> AgentState:
    while not self.state.done and self.state.step < self.state.max_steps:
        # 1. Perceive — 感知当前环境
        perception = self.perceive(current_skill)

        # 2. Plan — 决定下一步执行哪个 Skill
        plan_result = self.plan(skill_index, perception)
        # plan_result = {"action": "execute"|"retry"|"skip"|"abort", "skill_id": "...", "reason": "..."}

        # 3. Act — 调用 LLM 执行 Skill
        response = self.act(skill_id)

        # 4. Observe — 验证产出质量
        observation = self.observe(skill_id, response)

        # 5. Update — 更新状态
        self.update(skill_id, observation)

    return self.state
```

**每一个 Agent（project/requirement/test-design/automation/execution）内部都运行这个循环。**

### 为什么采用 ReAct

一个 Agent 执行 Skill 链时，遇到过两种情况：

**情况 A（无 ReAct — v1.0 的做法）**：顺序 for 循环跑完所有 Skill，不管中间结果：
```python
# ❌ v1.0 的简单方案
for skill in skills:
    result = run_skill(skill, input)
    # 不管 result 是对是错，直接继续下一个
```

问题：如果 `tech-analysis` 定位器设计错误，`page-object-generator` 会基于错误的定位器生成代码——浪费 3 个 Skill 的执行。

**情况 B（有 ReAct — v2.0）**：每一步都先感知环境、再规划动作、执行后观察结果、根据结果更新状态：
```python
# ✅ v2.0 的 ReAct
perceive: "TECH_ANALYSIS.md 已存在 → 跳过 tech-analysis"
plan:     "下一步 → page-object-generator"
act:      LLM 生成 PageObject
observe:  "PageObject 生成但有 2 个红线违规"
update:   status=fail → 触发 LLM 自主规划器决策
```

### 解决了什么问题

**盲执行问题 (Blind Execution Problem)**：Agent 执行完一个 Skill 后不知道产出质量如何，盲目继续下一个。ReAct 强制在每个 Skill 后执行 Observe → Plan，让 Agent **根据观察结果调整行为**。

### 优点

- **中间失败不会级联放大**：tech-analysis 失败会被 observe 捕获，Agent 可以选择 retry/skip/abort，不会把错误输入传递给下游 Skill
- **幂等性内建**：perceive 检查产物是否已存在 → 自动跳过已完成的 Skill → 支持断点续跑
- **混合决策节省 Token**：确定性情况用规则决策（零 LLM 调用），模糊情况用 LLM 决策

### 缺点

- **每个 Skill 后多了 4 步开销**（perceive/plan/observe/update），对于简单 Skill（如 completeness-check）来说过度设计
- **Plan 阶段的 LLM 调用可能不稳定**（低 temperature 的 JSON 输出偶尔解析失败，有回退机制）

### 与纯 ReAct 的区别

理论上的 ReAct 每一步都是 "思考→行动→观察"，思考内容是人类可读的推理链。本项目的 ReAct 做了工程化剪裁：

| 理论 ReAct | 本项目 ReAct |
|-----------|-------------|
| 每步 Thought 都是 LLM 自由文本 | Plan 分两档：规则决策（zero token）/ LLM 决策（structured JSON） |
| Action 是调用外部工具 | Act 是调用 Skill（封装了 LLM 调用 + 文件保存） |
| Observation 来自环境 | Observe 是代码级验证（文件存在性 + grep 红线检查） |

---

## 模式 2: Plan & Execute

### 在项目中的体现位置

**两层 Plan & Execute**：

**第一层：Agent 级别**
- Planner: Test Design Agent (Phase 1-2.5) — 产出 TEST_DESIGN.md + TEST_CASES.md
- Executor: Automation Agent (Phase 3-4) — 消费 TEST_CASES.md → 生成 Page Object + 测试脚本

文件位置: [agent-definitions.yaml:67-98](governance/agents/agent-definitions.yaml#L67) 和 [agent-definitions.yaml:103-145](governance/agents/agent-definitions.yaml#L103)

**关键门禁**：
```yaml
# sop-gate.template.md:24
automation-agent | Phase 2.5 | ⛔ 缺失 PAGE_CONTEXT.md / TEST_CASES.md
→ 先执行 /test-design-agent 或 /full-sop mode=from-test-design
```

**第二层：Skill 级别（Automation Agent 内部）**
- Planner: auto-strategy Skill — 决定自动化策略、PageObject 拆分方案、ROI
- Executor: page-object-generator + test-script-generator — 根据策略生成代码

### 为什么采用 Plan & Execute

在测试自动化中，最昂贵的错误是**生成了一堆不能用的代码**。Plan & Execute 强制在写代码之前先回答：
1. 哪些用例需要自动化？（覆盖矩阵）
2. 哪些不需要？为什么？（ROI 分析）
3. Page Object 如何拆分？（架构设计）

这些决策在 AUTO_STRATEGY.md 中显式记录，生成代码前可以人工 review。

### 解决了什么问题

**Code-First Anti-Pattern**：没有 Plan & Execute 时，Automation Agent 拿到"给 XX 页面写自动化"就直接生成代码——不知道测试范围、不知道策略、不知道拆分方案。结果是：
- 写了 20 个测试方法但只覆盖了 40% 的场景
- 漏了关键的异常流程
- Page Object 设计混乱（一个类 500 行）

Plan & Execute 强制分两步：先设计（人可 review），再执行（代码生成）。

### 优点

- **Plan 是人可读的 Markdown 文档**，不是黑盒决策。在代码生成前 review 策略可以避免大部分返工
- **Plan 可以被复用**：同一个 TEST_CASES.md 可以被多个 automation-agent 会话消费
- **分离了关注点**：测试分析师（Plan）和自动化工程师（Execute）是不同的技能

### 缺点

- **增加了一个 Phase 的耗时**：从"直接生成代码"变成"先设计再生成"
- **Plan 和 Execute 之间可能不一致**：如果 Plan 变更了但 Execute 没有重新执行

### 与纯 Plan & Execute 的区别

理论上的 Plan & Execute：一个 Agent 自己先规划再执行。
本项目的 Plan & Execute：**跨 Agent 的 Plan & Execute**——两个不同的 Agent 分别负责规划和执行，通过文档传递 Plan。

这样设计的原因：测试设计和自动化代码生成需要的系统提示词完全不同。合并到一个 Agent 会导致系统提示词膨胀到 5000+ tokens。

---

## 模式 3: Supervisor (监督者/编排器)

### 在项目中的体现位置

**核心文件**: [aitest/graphs/sop_graph.py](aitest/graphs/sop_graph.py) 整个文件

Full SOP 编排器是典型的 Supervisor 模式：

```python
# sop_graph.py:399-473 (简化)
def build_sop_graph(use_subgraphs: bool = True) -> StateGraph:
    builder = StateGraph(SOPState)

    # Supervisor 节点
    builder.add_node("entry", entry_node)
    builder.add_node("preflight", preflight_node)

    # Worker 节点（被监督的 Agent）
    builder.add_node("project_agent", make_agent_loop_node("project-agent"))
    builder.add_node("requirement_agent", make_agent_loop_node("requirement-agent"))
    # ... 其他 6 个 worker

    builder.add_node("exit", exit_node)

    # Supervisor 通过条件路由分配任务
    builder.add_conditional_edges("preflight", route_next_phase, route_map)
    for node_name in ALL_AGENT_NODES:
        builder.add_conditional_edges(node_name, route_next_phase, route_map)
```

Supervisor（route_next_phase）**不执行具体任务**，只负责：
1. 检查每个 Agent 的完成状态
2. 根据规则决定下一个 Agent
3. 特殊条件：Bug Analysis 仅在 execution_failed 时触发
4. 全局错误处理：fatal_error → 立即终止

### 为什么采用 Supervisor

8 个 Agent 的依赖关系不是简单的线性链：

```
Project Init ──→ Requirement ──→ Test Design ──→ Automation ──→ Execution
                                                                    │
                                                           ┌───────┴───────┐
                                                           │ 成功   失败    │
                                                           ▼       ▼       │
                                                         Report  Bug     │
                                                                  Analysis │
                                                                     │     │
                                                                     └─────┘
                                                                  (循环 ≤3次)
```

执行失败时触发 Bug Analysis→fix→verify 循环，成功时直接跳到 Report。这种条件分支无法用简单的顺序脚本表达，需要 Supervisor 做动态路由。

### 解决了什么问题

**流水线僵化问题**：如果 8 个 Agent 固定顺序执行，会出现两个问题：
1. 执行成功时也跑 Bug Analysis（浪费）
2. 执行失败时直接报错退出（无法自动修复）

Supervisor 根据运行时状态动态决定下一个 Agent。

### 优点

- **集中式决策**：所有路由逻辑在一处（`route_next_phase`），容易理解和修改
- **全局异常处理**：fatal_error 在任何 Agent 后都能被捕获，统一跳转到 exit
- **支持 skip_phases**：mode=from-automation 可以跳过前 3 个 Phase，Supervisor 自动处理

### 缺点

- **单点复杂性**：`route_next_phase` 随着 Agent 数量增加会越来越复杂
- **Supervisor 不执行具体任务**：如果 Supervisor 出 bug（如错误地跳过了某个 Phase），Worker 不会感知到

### 与 Router 模式的区别

本项目同时使用了 Supervisor 和 Router 两种模式。区别在于：

| | Supervisor | Router |
|---|-----------|--------|
| 决策复杂度 | 全局状态 + 多因素 | 单一状态 + 枚举分支 |
| 本项目体现 | `route_next_phase`（检查 5+ 个状态字段） | `loop_router`（检查 cycle/passed/approved 3 个字段） |
| 决策结果 | 8 个可能的 Agent 节点 | 2 个可能（loop/report） |

**关键区分**：Router 是 Supervisor 的实现手段，但不是所有 Router 都是 Supervisor。`loop_router` 只是一个条件分支，不监督其他 Agent。

---

## 模式 4: Router (路由器)

### 在项目中的体现位置

项目中 **3 个 Router** 函数：

**① `route_next_phase` — 顶层 Phase 路由**
文件: [sop_graph.py:347-392](aitest/graphs/sop_graph.py#L347)
```python
def route_next_phase(state: SOPState) -> str:
    if fatal_error: return "exit"
    if mode == "status": return "exit"
    for phase in CANONICAL_PHASES:
        if phase in completed or phase in skipped: continue
        if phase == "Bug Analysis" and not execution_failed: continue
        return PHASE_TO_NODE[phase]
    return "exit"
```

**② `loop_router` — Bug Analysis 循环路由**
文件: [bug_analysis_graph.py:269-301](aitest/graphs/bug_analysis_graph.py#L269)
```python
def loop_router(state) -> Literal["loop", "report"]:
    if approved is False: return "report"
    if cycle >= bug_cycle_max: return "report"
    if verify_result.get("passed"): return "report"
    return "loop"  # 回到 analyze_fail
```

**③ `_router` — Skill 级重试路由（已归档）**
文件: [_archived/project_graph.py:105-119](aitest/graphs/_archived/project_graph.py#L105)
```python
def _router(state) -> Literal["continue", "retry", "gate_check"]:
    if suggestion == "retry" and retry_count < 3: return "retry"
    if suggestion in ("continue", "skip"): return "continue"
    return "gate_check"
```

### 为什么采用 Router

这三个 Router 解决的问题各不相同：

**`route_next_phase`**：解决的是 8 个 Agent 之间的**动态编排**。不是简单的 A→B→C，而是"如果执行成功则跳过 Bug Analysis，如果失败则进入修复循环"。

**`loop_router`**：解决的是 Bug Analysis 的**循环退出条件**。不是固定次数循环，而是"修复通过→退出；人类拒绝→退出；达到上限→退出；否则→继续"。

**`_router`**：解决的是 Skill 级别的**重试还是跳过还是放弃**。

### 解决了什么问题

**硬编码 if-else 地狱**。如果没有 Router，你需要：
```python
# ❌ 没有 Router 的写法
if phase == "Project Init":
    project_agent()
elif phase == "Requirement":
    requirement_agent()
elif phase == "Test Design":
    test_design_agent()
# ... 8 个 elif

# 而且每个 Agent 执行后还要重新判断下一个 Phase！
```
Router 把决策逻辑集中到一个纯函数中，输入 State，输出节点名，可以被 LangGraph 的条件边机制自动调用。

### 优点

- **纯函数**：Router 只读 State，不产生副作用，可以安全地重放和测试
- **可组合**：LangGraph 的条件边允许同一个 Router 被挂载到多个源节点（所有 Agent 节点都挂载 `route_next_phase`）
- **决策透明**：所有路由逻辑都在这几行代码中，不会分散到各处

### 缺点

- **Router 无法做复杂推理**：如果路由逻辑需要 LLM 决策（如"这个失败看起来严重吗？应不应该触发 Bug Analysis？"），纯规则 Router 做不到
- **状态依赖隐式**：Router 依赖 State 中的多个字段（fatal_error, mode, completed_phases, skip_phases, execution_failed），字段之间的关系没有显式文档

---

## 模式 5: Reflection (反思)

### 在项目中的体现位置

项目中 **3 处** 使用了 Reflection 模式：

**① Bug Analysis 自动修复循环 — 最完整的 Reflection**
文件: [bug_analysis_graph.py:35-340](aitest/graphs/bug_analysis_graph.py#L35)

```
analyze_fail → auto_fix → verify → (验证失败 → 回到 analyze_fail)
                 ↑                                    │
                 └────────────────────────────────────┘
                        最多循环 3 次
```

每次循环都是一次完整的 Reflection：分析错误 → 提出修复 → 验证修复 → 反思结果。

**② AgentLoop 的 LLM 自主决策 — 单个 Skill 级别的 Reflection**
文件: [agent_runner.py:657-756](aitest/agent_runner.py#L657)

```python
def _llm_plan(self, skill_index, perception, last_obs):
    # LLM 根据当前状态决定: retry / execute / replan / skip / abort
    prompt = f"""你是 Agent 规划器。根据当前状态决定下一步动作。
    ## Skill 链状态
    [1] tech-analysis — ✅ 完成
    [2] page-object-generator — ❌ 失败
    ## 质量问题
    - 禁止 print 调试 (line 42)
    ## 决策规则
    - retry: 可通过调整修复
    - execute: 问题不阻塞后续
    ...
    输出 JSON: {{"action": "...", "reason": "..."}}"""
```

当 observe 发现产出质量问题时，AgentLoop 不是盲目重试，而是调用 LLM 做**反思决策**——这个错误是否可以通过调整修复？还是应该跳过？还是应该中止？

**③ code-consistency-checker 的 review 模式 — 代码级别的 Reflection**
文件: [code-consistency-checker.md](governance/skills/automation/code-consistency-checker.md)

```markdown
| Mode | 执行方式 | Token | 用途 |
|------|---------|:-----:|------|
| mechanical (默认) | grep 扫描，不调 LLM | 0 | 快速检查 8 条红线 |
| review | LLM 对抗性审查 | ~2K | 深度审查定位器稳定性、等待策略、断言充分性 |
```

### 为什么采用 Reflection

**没有 Reflection 的 Agent 是盲目的**：
- 生成了错误代码 → 不检查 → 继续生成下一个
- 修复了 Bug → 不验证 → 以为修好了

Reflection 强制 Agent 在行动后**审视自己的产出**。

### 解决了什么问题

**错误级联和虚假修复**：
- Bug Analysis 的 Reflection：修复 → 验证 → 不通过 → 换个方式修复 → 再验证。防止"修了但没修对"。
- AgentLoop 的 Reflection：观察产出质量 → 判断是否需要重试 → 重试时注入调整建议。防止"重试了但用同样的方式重试"。
- code-consistency-checker：每次代码生成后必执行。防止"生成了但不符合规范"。

### 优点

- **自动修复闭环**：Bug Analysis 最多 3 次自动修复循环，减少人工介入
- **LLM 决策有上下文**：AgentLoop 的 LLM 反思会看到完整的 Skill 链状态和质量问题列表
- **机械化反思零成本**：code-consistency-checker 的 mechanical 模式不消耗 Token

### 缺点

- **LLM 反思可能做出错误决策**：如果 LLM 错误地判断 "skip"，可能跳过关键 Skill
- **循环上限是硬编码的**：Bug Analysis 的 3 次限制对某些复杂 Bug 可能不够

### 与纯 Reflection 模式的区别

理论上的 Reflection：Agent 执行 → 自我评估 → 如果不好就重新执行。
本项目的 Reflection 做了**分层**：

| 层级 | Reflection 粒度 | 执行者 |
|------|----------------|--------|
| Agent 循环级 | 修复→验证→再修复 | Bug Analysis SubGraph |
| Skill 级 | 产出→检查→重试/跳过 | AgentLoop._llm_plan() |
| 代码级 | 代码→红线扫描→合规报告 | code-consistency-checker |

---

## 模式 6: Multi-Agent (多 Agent 协作)

### 在项目中的体现位置

**8 个 Agent = 一种 Multi-Agent 系统**。

定义文件: [agent-definitions.yaml](governance/agents/agent-definitions.yaml)

### 为什么采用 Multi-Agent

这是本项目最核心的架构决策。为什么不做一个全能 Agent？

**一个全能 Agent 的问题**：
```
系统提示词 = "你是测试架构师" + "你是需求分析师" + "你是测试设计师"
           + "你是 Selenium 专家" + "你是 CI 工程师" + "你是报告分析师"
           + "你是知识管理专家"
           = 8000+ tokens 的系统提示词

每次调用都要加载全部 8000 tokens（即使是简单的"检查代码合规"）
每次对话上下文都混杂了 7 种不同的角色身份
一个角色的错误推理会污染其他角色的判断
```

**8 个 Agent 的方案**：
```
project-agent:      系统提示词 ~500 tokens（项目架构师）
requirement-agent:  系统提示词 ~500 tokens（需求分析师）
test-design-agent:  系统提示词 ~600 tokens（测试设计师）
automation-agent:   系统提示词 ~800 tokens（Selenium 专家）
execution-agent:    系统提示词 ~300 tokens（执行工程师）
bug-analysis-agent: 系统提示词 ~700 tokens（诊断专家）
report-agent:       系统提示词 ~400 tokens（报告分析师）
knowledge-agent:    系统提示词 ~500 tokens（知识管理专家）

每次调用只加载对应 Agent 的提示词
每个 Agent 在自己的专业领域内推理，不受其他角色干扰
```

### 解决了什么问题

**超级提示词膨胀 (Mega-Prompt Bloat)** 和 **角色混淆 (Role Confusion)**。

### Agent 间通信方式：文档通信

这是本项目 Multi-Agent 设计的核心特征——Agent 通过**文件系统**传递状态，而不是通过共享内存：

```
Agent A 写入 → context/projects/.../PAGE_CONTEXT.md
                                                ↓
Agent B 读取 ← context/projects/.../PAGE_CONTEXT.md
```

对比三种 Multi-Agent 通信方式：

| 通信方式 | 本项目 | 优点 | 缺点 |
|---------|:-----:|------|------|
| 共享内存 | ❌ 不采用 | 快速 | 无法断点续跑；Agent 必须同进程 |
| 消息队列 | ❌ 不采用 | 解耦 | 需要额外基础设施 |
| **文档通信** | ✅ 采用 | 可调试、可恢复、可审计 | 需要显式的文件 I/O |

### 优点

- **提示词隔离**：每个 Agent 的 system prompt 保持在 300-800 tokens
- **断点续跑**：Agent B 不需要 Agent A 在同一个进程中运行。从 PROJECT_CONTEXT.md 读取和从内存读取一样
- **可审计**：中间产物（PAGE_CONTEXT.md, TEST_CASES.md, TECH_ANALYSIS.md）可以被人类 review
- **支持人工介入**：人可以在 Agent 之间插入修改（如修改 TEST_CASES 后再让 automation-agent 执行）

### 缺点

- **文件 I/O 开销**：每个 Agent 都要读写文件
- **格式一致性风险**：如果 Agent A 的输出格式变化，Agent B 可能解析失败
- **延迟发现上游错误**：Agent B 执行到一半才发现 Agent A 的产出有问题

### 与其他 Multi-Agent 实现的区别

常见的 Multi-Agent 框架（AutoGen, CrewAI）依赖 Agent 之间的**对话**进行通信。本项目选择了**文档**作为通信媒介。原因：
- 测试工程的产出本身就是文档（测试用例、技术分析、Bug 报告）
- 文档可以被非 AI 消费者使用（人类 QA、PM）
- 文档天然支持断点续跑

---

## 模式 7: Hierarchical Agent (层级 Agent)

### 在项目中的体现位置

**三级层级**:

```
L3: Full SOP (Orchestrator)
    │
    ├── 监督 8 个 L2 Agent
    │
    └── L2: Agent (project / requirement / test-design / automation /
    │           execution / bug-analysis / report / knowledge)
    │
    └── 每个 L2 Agent 管理 1-6 个 L1 Skill
        │
        └── L1: Skill (page-analysis / risk-modeling / tech-analysis / ...)
```

体现在两个地方：

**① Agent → Skill 的层级关系**
文件: [agent-definitions.yaml](governance/agents/agent-definitions.yaml)
```yaml
automation-agent:
  skills:
    - automation/tech-analysis
    - automation/auto-strategy
    - automation/page-object-generator
    - automation/test-script-generator
    - automation/code-consistency-checker
```

**② LangGraph 的父图-子图层级**
文件: [sop_graph.py:430-441](aitest/graphs/sop_graph.py#L430)
```python
# 父图（sop_graph）包含子图作为节点
builder.add_node("execution_agent", build_execution_subgraph().compile())
builder.add_node("bug_analysis_agent", build_bug_analysis_compiled())
builder.add_node("report_agent", build_report_subgraph().compile())
builder.add_node("knowledge_agent", build_knowledge_subgraph().compile())
```

### 为什么采用层级结构

**没有层级的替代方案**：24 个 Skill 平铺在一个超级工作流中。编排器需要处理 24 个节点的路由——路由逻辑会爆炸。

**有层级**：编排器只需要处理 8 个 Agent 节点的路由。每个 Agent 内部的 Skill 编排由 AgentLoop 负责。这符合 **分治原则 (Divide and Conquer)**。

### 解决了什么问题

**编排复杂度爆炸**。如果 24 个 Skill 全部平铺在顶层图中：
- 条件路由函数需要处理 24! 种可能的路径
- 断点续跑需要记住 24 个节点的完成状态
- 任何 Skill 的变更都可能影响顶层路由

有了层级，编排器只看到 8 个 Agent，每个 Agent 内部封闭管理自己的 Skill 链。

### 优点

- **关注点分离**：编排器不关心 Agent 内部细节（用了几个 Skill？哪个失败了？），只关心 Agent 的整体成功/失败
- **独立优化**：Agent 内部的 ReAct 循环可以独立优化，不影响编排器
- **子图复用**：bug_analysis_graph 可以被其他图引用（虽然目前只在 sop_graph 中）

### 缺点

- **状态传递开销**：父图→子图→父图的状态合并需要 LangGraph 的 SubGraph 机制支持
- **调试困难**：子图内部的错误可能被父图吞掉

### 与纯 Hierarchical Agent 的区别

理论上的 Hierarchical Agent：高层 Agent 分派子任务给底层 Agent，底层 Agent 返回结果。

本项目的层级不是 "Agent 分派 Agent"，而是 **Orchestrator 调度 Agent + Agent 管理 Skill**。Skill 不是 Agent——Skill 是被动的 Prompt 模板，没有自主决策能力。

---

## 模式 8: State Machine Agent (状态机)

### 在项目中的体现位置

**SOPState 的状态机**:

文件: [state.py:126-145](aitest/graphs/state.py#L126) 和 [state.py:194-249](aitest/graphs/state.py#L194)

```python
# 规范 Phase 顺序 — 状态机的合法状态
CANONICAL_PHASES = [
    "Project Init",
    "Requirement",
    "Test Design",
    "Automation",
    "Execute & Debug",
    "Bug Analysis",       # ← 条件状态：仅 execution_failed 时进入
    "Report",
    "Knowledge",
]

# Mode → skip_phases 映射 — 状态机的初始转移
MODE_SKIP_MAP = {
    "full": [],
    "from-requirement": ["Project Init"],
    "from-test-design": ["Project Init", "Requirement"],
    "from-automation": ["Project Init", "Requirement", "Test Design"],
}
```

状态转移在 `route_next_phase` 中实现：
```
当前状态 = 遍历 CANONICAL_PHASES，找到第一个未完成且未跳过的 Phase
转移条件 = fatal_error? → exit
          mode=status? → exit
          execution_failed + Bug Analysis? → 进入 Bug Analysis
          execution_success + Bug Analysis? → 跳过 Bug Analysis
          所有 Phase 完成? → exit
转移目标 = PHASE_TO_NODE[phase]
```

### 为什么采用状态机

SOP 的 Phase 顺序是一组有严格依赖关系的状态转移：
- Bug Analysis 只能在 Execute & Debug 失败后进入
- Knowledge 必须在所有 Agent 完成后执行
- 部分 Phase 可以通过 mode 跳过

状态机是表达这种约束最自然的方式。如果用 if-else 实现，需要 ~40 行嵌套条件；状态机用 15 行完成。

### 解决了什么问题

**Phase 依赖关系的显式表达**。没有状态机，Phase 之间的依赖关系散落在代码各处（"这个 Phase 需要那个 Phase 先完成"），新人很难理解完整流程。

状态机把所有合法状态和转移规则集中在一处（`CANONICAL_PHASES` + `route_next_phase`）。

### 优点

- **状态转移可预测**：给定当前 State，下一个 Phase 是确定性的
- **支持 skip**：skip_phases 是状态机的 "初始状态注入"，可以优雅地跳过已完成 Phase
- **条件转移**：Bug Analysis 的条件触发是状态机的高级特性

### 缺点

- **线性状态机缺乏并行能力**：当前状态机是严格线性的（一个 Phase 接一个 Phase），不支持并行执行（如 Test Design 和 Automation 不能对不同页面并行执行）
- **未来 Phase 增加时需要修改 CANONICAL_PHASES 列表**

---

## 模式 9: Human-in-the-Loop (人机协作)

### 在项目中的体现位置

**Bug Analysis 的修复审批**:

文件: [bug_analysis_graph.py:188-216](aitest/graphs/bug_analysis_graph.py#L188)

```python
def request_approval_node(state: SOPState) -> dict:
    approval = interrupt({
        "type": "bug_fix_approval",
        "cycle": f"{cycle + 1}/3",
        "module": state["module"],
        "analysis_summary": "...",    # 根因分析摘要
        "fix_summary": "...",         # 修复方案摘要
        "options": ["approve", "reject", "skip"],
    })
    approved = approval == "approve"
    return {"fix_approved": approved}
```

### 为什么采用 HITL

**为什么不在循环外部审批？**

```
❌ 循环外:
   AI 执行 3 次 analyze→fix→verify → 人类看最终结果
   问题: 3 次修复可能都是错的，但人类只在最后知道

✅ 循环内（本项目）:
   analyze → fix → 【人类审批】 → verify → (pass/fail → loop)
   优势: 每次修复执行前都经过人类审批
```

自动化测试代码的修改有风险——一个错误的修复可能导致：
- CI 流水线中的破坏性用例误删数据
- 定位器修改后影响其他用例
- 等待策略修改后引入新的不稳定

所以修复方案必须经过人工审批，不能由 AI 自主执行。

### 解决了什么问题

**AI 自主修改代码的安全性问题**。AI 可能做出看似合理但实际有害的修复——比如删除一个看似多余的等待但实际上那个等待是另一个用例需要的。

HITL 在修复方案和实际执行之间插入了一个**人审批的屏障**。

### 优点

- **安全第一**：破坏性修复不会自动执行
- **审批上下文完整**：interrupt 携带分析摘要、修复摘要、选项，人类有足够信息做决策
- **LangGraph 原生支持**：interrupt() 自动暂停图执行并保存 checkpoint，恢复后从暂停点继续

### 缺点

- **阻塞流水线**：如果人不及时响应，整个 SOP 流水线会卡在审批环节
- **审批质量依赖人**：如果审批人不理解修复方案就点了 "approve"，HITL 形同虚设

### 与纯 HITL 的区别

常见的 HITL 实现是在 Agent 循环外部等待人工输入。本项目的 HITL 是**循环内部的**——人是 Agent 决策循环的一部分，不是外部观察者。这意味着：
- 如果人拒绝了一个修复方案，Agent 会进入下一轮循环，重新分析→生成新的修复方案→再审批
- 人不是在 "事后检查"，而是在 "事中审批"

---

## 模式组合关系

这 9 种模式不是独立的，它们在本项目中形成了分层组合：

```
┌─────────────────────────────────────────────────────────┐
│                   State Machine                          │
│         定义 Phase 状态和合法转移                        │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Supervisor                          │   │
│  │        (full-sop → sop_graph.py)                 │   │
│  │        调度 8 个 Agent，监控全局状态              │   │
│  │                                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │   │
│  │  │ Router   │  │ Router   │  │ Router   │      │   │
│  │  │(顶层路由)│  │(循环路由)│  │(重试路由)│      │   │
│  │  └──────────┘  └──────────┘  └──────────┘      │   │
│  │       │              │              │           │   │
│  │  ┌────┴────┐   ┌────┴────┐   ┌───┴──────┐     │   │
│  │  │ Plan &  │   │Reflection│   │  HITL    │     │   │
│  │  │ Execute │   │ 循环     │   │ interrupt │     │   │
│  │  └─────────┘   └─────────┘   └──────────┘     │   │
│  │                                                  │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │         Multi-Agent (8 Agents)            │   │   │
│  │  │    文档通信 + 唯一写入原则                 │   │   │
│  │  │                                           │   │   │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐     │   │   │
│  │  │  │  ReAct  │ │  ReAct  │ │  ReAct  │ ... │   │   │
│  │  │  │  Loop   │ │  Loop   │ │  Loop   │     │   │   │
│  │  │  │(Agent-1)│ │(Agent-2)│ │(Agent-3)│     │   │   │
│  │  │  └─────────┘ └─────────┘ └─────────┘     │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│              Hierarchical: SOP → Agent → Skill            │
└─────────────────────────────────────────────────────────┘
```

**层级关系**：
- **State Machine** 在最外层，定义了 "什么状态是合法的"
- **Supervisor** 在状态机之上，实现了 "状态之间如何转移"
- **Router** 是 Supervisor 的实现手段
- **Multi-Agent** 是被监督的 Worker 集合
- **ReAct** 是每个 Agent 内部的执行引擎
- **Plan & Execute** 是跨 Agent 的分工（Test Design Agent → Automation Agent）
- **Reflection** 是特定 Agent（Bug Analysis + AgentLoop）的内部循环机制
- **HITL** 是 Reflection 循环中的安全闸门
- **Hierarchical** 贯穿全部三层（Orchestrator → Agent → Skill）

---

> **文档版本**: 2026-06-14 · 基于项目 v2.0 Agent 体系 · 纯教学用途
