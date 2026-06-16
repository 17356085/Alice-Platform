# Agent 工程逆向拆解：从鞍集涂源管理系统学习多 Agent 架构

> **写作目的**: 教学文档。以本项目为真实案例，逆向拆解 Agent 体系的设计思想。
> **读者假设**: 已了解 Agent 基础概念（如 Tool Use、Prompt Engineering），希望深入学习多 Agent 系统设计。
> **案例项目**: 鞍集涂源管理系统 — AI 辅助测试开发平台（8 Agent v2.0 + LangGraph 编排器）

---

## 0. 先决知识：Agent ≠ Chatbot

在深入分析之前，先建立基础概念框架。

```
普通 Chatbot          Agent                   多 Agent 系统
    │                    │                        │
    │  用户问→AI答       │  感知→规划→行动→观察   │  多个 Agent 协作
    │  无状态            │  有状态循环             │  通过文档/事件通信
    │  单一能力          │  绑定工具/Skill         │  职责分离
    │                    │                        │
    └── 对话驱动 ────────┴── 目标驱动 ────────────┴── 流程驱动
```

本项目位于 "多 Agent 系统" 这一层。下面依次拆解。

---

## 1. 四层架构：从原子到编排

这是理解整个系统的关键。Agent 不是孤立存在的，它运行在一个四层架构中：

```
┌──────────────────────────────────────────────────────┐
│              L4: 编排器 (Orchestrator)               │
│         full-sop → LangGraph sop_graph.py            │
│         职责: Phase 路由、条件分支、断点续跑           │
├──────────────────────────────────────────────────────┤
│              L3: 图引擎 (Graph Engine)               │
│         LangGraph StateGraph + SubGraph               │
│         职责: 状态机、checkpoint、HITL interrupt       │
├──────────────────────────────────────────────────────┤
│              L2: Agent 层 (8 Agents)                 │
│         AgentLoop: Perceive→Plan→Act→Observe→Update  │
│         职责: Skill 编排、质量验证、自主决策           │
├──────────────────────────────────────────────────────┤
│              L1: Skill 层 (24 Skills)                │
│         单个 Prompt 模板 + 上下文注入 + LLM 调用       │
│         职责: 原子任务执行（分析/生成/检查）            │
└──────────────────────────────────────────────────────┘
```

### 为什么需要四层？

这是本系统最核心的设计决策。很多 Agent 项目失败的原因是把所有逻辑塞进一层：

| 只有一层 | 后果 |
|---------|------|
| 只有 Skill | 每次都要人工决定"下一步做什么"，无法自动化 |
| 只有 Agent | 每个 Agent 都重新实现路由逻辑，重复代码 |
| 只有编排器 | 一个巨大的 if-else 路由，无法处理复杂决策 |

**核心思想: 每层解决不同粒度的问题。**

- **Skill** 解决 "怎么做"（How to generate a Page Object）
- **Agent** 解决 "做什么 + 做对了没"（What skills to run + Did it work）
- **Graph** 解决 "何时做"（When to run which Agent）
- **编排器** 解决 "全局去哪"（Where are we in the pipeline）

---

## 2. 纵向拆解：8 个 Agent 逐一分析

对每个 Agent，回答七个问题：

1. **为什么需要** — 存在的理由
2. **如果没有** — 反事实推演
3. **解决了什么问题** — 核心痛点
4. **和 Skill 有什么区别** — 抽象层级
5. **和 Workflow 有什么区别** — 执行载体
6. **和 LangGraph 节点是什么关系** — 实现关系
7. **属于什么 Agent 模式** — 学术归类

---

### Agent ①: Project Agent（项目 Agent）

```
Phase: 0
Skills: project-context-manager, context-sync, completeness-check
LangGraph 节点: project_agent → make_agent_loop_node("project-agent")
```

#### 为什么需要

任何多 Agent 系统面临的第一个问题：**冷启动**。8 个 Agent 各司其职，但如果没有一个统一的"项目地图"，每个 Agent 都要自己去探索项目结构——这会带来三个灾难：

- **不一致**: Agent A 认为配置文件在 `config/`，Agent B 认为在 `settings/`
- **浪费**: 每个会话都要重新扫描目录结构
- **漂移**: 代码在变，但没人更新全局视图

Project Agent 的职责就是**一次性把项目结构转化为结构化上下文**，写入 `PROJECT_CONTEXT.md` 和 `MODULE_INDEX.md`，作为所有下游 Agent 的单一事实源（Single Source of Truth）。

#### 如果没有 Project Agent

```
Requirement Agent: "这个项目有哪些模块？让我扫描一下..."
Test Design Agent: "配置文件在哪？让我扫描一下..."  
Automation Agent:  "BasePage 在哪个目录？让我扫描一下..."
                   ↓
              每个 Agent 都做一遍目录扫描
              每个 Agent 都可能得出不同的结论
              上下文冲突消费
```

#### 解决了什么问题

**冷启动问题 (Cold Start Problem)** — 多 Agent 系统的 bootstrapping。这类似于操作系统的 `init` 进程或 Kubernetes 的 control plane：在所有工作负载运行之前，需要有一个组件先把基础架构梳理清楚。

#### 和 Skill 的区别

- `project-context-manager` (Skill): **知道如何**分析项目目录并写出 PROJECT_CONTEXT.md
- `context-sync` (Skill): **知道如何**对比新旧上下文、增量更新
- `completeness-check` (Skill): **知道如何**审计产物完整性
- Project Agent: **知道何时**调用这些 Skill、**如何验证**产出质量、**何时重试**

```
Skill = "我能写一个项目上下文文档"
Agent = "我要确保项目上下文文档存在、完整、最新。如果不存在，我生成它；如果过期，我更新它；如果缺失，我补充它。"
```

#### 和 Workflow 的区别

`project-takeover` workflow 定义了 Project Agent 执行的流程规范（输入→处理→输出→门禁）。Workflow 是**流程定义**，Agent 是**流程的执行者**。

类比：Workflow = 菜谱，Agent = 厨师。菜谱说"先放油再放菜"，厨师决定"油温够了吗？菜洗了吗？要不要多炒30秒？"

#### 和 LangGraph 节点的关系

在 `sop_graph.py` 中，`project_agent` 是一个 LangGraph 节点：

```python
builder.add_node("project_agent", make_agent_loop_node("project-agent"))
```

LangGraph 负责**何时调用**这个节点（`route_next_phase` 判断 "Project Init" 是否已完成），而 Agent 负责**节点内部做什么**（AgentLoop 运行 3 个 Skill 链）。

**关键洞察**: LangGraph 节点 = Agent 的**外骨骼**（管理它在流水线中的位置），Agent = 节点的**大脑**（管理内部的 Skill 执行决策）。

#### Agent 模式归类

**Bootstrapper Agent（引导 Agent）** — 一种特殊的 Executor，职责是在其他 Agent 工作之前建立基础上下文。类似于：
- Terraform 在部署应用前 provision infrastructure
- `npm init` 在写代码前建立项目骨架

---

### Agent ②: Requirement Agent（需求 Agent）

```
Phase: 0.5~0.8
Skills: module-modeling, requirement-analysis
LangGraph 节点: requirement_agent → make_agent_loop_node("requirement-agent")
```

#### 为什么需要

测试设计需要知道"被测系统是什么"。但一个模块可能有几十个页面、上百个功能点、复杂的业务规则。直接跳到"这个按钮怎么写定位"会遗漏大量测试场景。

Requirement Agent 的职责是**在写任何测试之前，先把模块的业务模型建立起来**——页面清单、路由结构、核心业务流程、数据流向。

这是 SOP 核心原则 #3 的体现：**先分析后编码**。

#### 如果没有 Requirement Agent

```
用户: "测 equipment 模块"
Test Design Agent: 直接打开页面→分析元素→设计用例
                   ↓
              漏掉 3 个隐藏页面（只有特定权限可见）
              漏掉跨页面的业务流程（A页面操作→影响B页面）
              漏掉非 UI 功能（定时任务、WebSocket 推送）
```

#### 解决了什么问题

**领域建模鸿沟 (Domain Modeling Gap)** — 测试人员（或 Test Design Agent）对业务域的初始理解是零散的。Requirement Agent 强制在测试设计之前先建立完整的模块模型。

这也是**范围管理**：如果一个模块有 15 个页面但你只测了 10 个，Requirement Agent 的产出（MODULE_CONTEXT.md）会让这个 gap 显式可见。

#### 和 Skill 的区别

- `module-modeling` (Skill): 从模块代码/文档中提取页面清单、路由结构
- `requirement-analysis` (Skill): 分析功能需求、识别测试范围
- Requirement Agent: 先运行 module-modeling 建立骨架，再运行 requirement-analysis 填充细节，验证两者一致性

#### Agent 模式归类

**Analyzer Agent（分析 Agent）** — 消费非结构化的源材料（代码、文档、截图），产出结构化的领域模型。这类 Agent 的特征是：
- 输入高度非结构化（可能是自然语言 PRD、也可能是代码目录）
- 输出高度结构化（MODULE_CONTEXT.md 有固定模板）
- 核心能力是**抽象和归纳**

---

### Agent ③: Test Design Agent（测试设计 Agent）

```
Phase: 1~2.5
Skills: page-analysis → risk-modeling → testcase-design → test-data-generation
         (+ api-testing, miniapp-testing 可选)
LangGraph 节点: test_design_agent → make_agent_loop_node("test-design-agent")
```

#### 为什么需要

这是 SOP 中**最关键的分界线**——"测什么"和"怎么测"的分离。

Test Design Agent 回答"测什么"：
- 页面上有哪些元素？(page-analysis)
- 哪些功能最容易出问题？(risk-modeling)
- 应该设计哪些测试用例？(testcase-design)
- 需要什么测试数据？(test-data-generation)

它的产出（PAGE_CONTEXT.md + TEST_CASES.md）是 Automation Agent 的**强制前置依赖**。没有这些，Automation Agent 不能启动（SOP 门禁 L2 阻断）。

#### 如果没有 Test Design Agent

会出现经典的**代码飞弹问题 (Code-First Anti-Pattern)**：

```
用户: "给 alarm-config 页面写自动化"
Automation Agent: 直接生成 Page Object → 生成测试脚本
                  ↓
              生成的测试覆盖了 40% 的功能（遗漏了 60%）
              定位器基于猜测而非真实 DOM 分析
              测试用例没有风险优先级（全测=没测）
              3 天后发现漏了关键的异常流程
```

#### 解决了什么问题

1. **"测什么 vs 怎么测"的分离 (Concern Separation)** — 这是测试工程中最古老的教训。把测试分析师和自动化工程师的角色分开，让每个 Agent 专注于自己擅长的领域。
2. **风险驱动测试 (Risk-Based Testing)** — 不是"所有功能都测一遍"，而是"高风险先测、深测"。
3. **门禁前置 (Gate Enforcement)** — AUTOMATION_AGENT 启动时必须检查 PAGE_CONTEXT.md 和 TEST_CASES.md 是否存在。**没有设计就没有代码。**

#### 内部 Skill 编排

这是 Agent 内部的最长 Skill 链：

```
page-analysis ──→ risk-modeling ──→ testcase-design ──→ test-data-generation
    │                   │                   │
    │ 分析页面结构        │ 识别风险区域        │ 设计具体用例
    │ DOM 元素清单        │ 评估影响×概率        │ 正向/异常/边界
    └── 下游依赖 ────────┴── 下游依赖 ─────────┘
```

如果 page-analysis 产出有问题，risk-modeling 和 testcase-design 都会受影响。AgentLoop 的 `perceive()` + `plan()` 机制会在这种情况下做出回退决策（replan）。

#### Agent 模式归类

**Planner Agent（规划 Agent）** — 制定"做什么"的计划，但不执行"怎么做"。

这是 Multi-Agent 系统中最常见也最重要的一类 Agent。它与 Executor Agent 的分离是 Agent 工程的经典模式：
- Planner 输出: 测试用例清单（人类可读）
- Executor 输入: 测试用例清单 → 生成自动化代码

---

### Agent ④: Automation Agent（自动化 Agent）

```
Phase: 3~4
Skills: tech-analysis → auto-strategy → page-object-generator → test-script-generator → code-consistency-checker
Modes: generate (完整生成) | fix (增量修复)
LangGraph 节点: automation_agent → make_agent_loop_node("automation-agent")
```

#### 为什么需要

这是整个系统**最复杂的 Agent**。它把 Test Design Agent 的"测什么"转化为可执行的 Python 代码。复杂性来自：

1. **5 个 Skill 的链式依赖** — 每个下游 Skill 依赖上游产出
2. **8 条代码红线** — 自动检查 + 自动修复
3. **双模式** — generate（完整生成）和 fix（增量修复）
4. **LLM 自主决策** — 失败时的 retry/skip/replan/abort 决策

#### 如果没有 Automation Agent

需要人工编写所有 Page Object 和测试脚本。对于一个中等规模的 Web 应用（20+ 页面 × 每个页面 10+ 用例），这就是数百个 Python 文件。

更关键的是**一致性**——人工编写会导致：
- 有人用 `time.sleep(3)`，有人用 `WebDriverWait`
- 有人用绝对 XPath，有人用 CSS Selector
- 有人继承 BasePage，有人不继承

Automation Agent 通过 `code-consistency-checker`（机械化检查，不需要 LLM）强制这 8 条规则。

#### 解决了什么问题

1. **代码生成的质量闭环** — "生成 → 自检 → 修复 → 再检"
2. **技术分析与代码生成的解耦** — tech-analysis 分析 DOM 定位策略，page-object-generator 只负责写代码。如果定位策略错了，只需重做 tech-analysis，不用重新生成整个 Page Object。
3. **机械化质量检查** — `code-consistency-checker` 是一个**零 Token 的 Skill**（纯 grep + regex），不消耗 LLM 调用。这体现了"能用代码检查的不要让 LLM 检查"的设计原则。

#### 内部 AgentLoop 的真 Agent 行为

Automation Agent 是 AgentLoop 最完整的展示案例。看它的决策树：

```
Perceive: "TECH_ANALYSIS.md 已存在 → 跳过 tech-analysis"
          "PageObject 文件不存在 → 需要执行 page-object-generator"

Plan:     正常推进 → 执行 page-object-generator

Act:      LLM 生成 PageObject 代码

Observe:  "文件已生成，但有 2 个红线违规: line 42 time.sleep(3), line 78 绝对 XPath"

Plan:     LLM 自主决策 → "retry，调整建议: 将 time.sleep(3) 替换为 wait_vue_stable()
          将绝对 XPath 替换为 CSS Selector .el-dialog__body"

Act:      LLM 根据调整建议重新生成（仅修改违规部分）

Observe:  "所有红线检查通过 ✅"
```

这不是简单的 for 循环——Agent 在 Plan 阶段做了**自主决策**。

#### 和 Skill 的区别

Automation Agent 最清楚地展示了 Agent 和 Skill 的本质区别：

| 维度 | Skill (e.g., page-object-generator) | Agent (automation-agent) |
|------|--------------------------------------|---------------------------|
| 知道什么 | 知道怎么写 Page Object | 知道什么时候需要写、写完后检查什么、失败了怎么办 |
| 决策权 | 无（执行指令） | 有（retry/skip/replan/abort） |
| 循环 | 无（调用即完成） | 有（Perceive→Plan→Act→Observe→Update） |
| 状态 | 无状态 | 有状态（completed_skills, failed_skills, retry_counts） |

#### Agent 模式归类

**Executor Agent with Internal Planner（带内部规划器的执行 Agent）**

这是最成熟的 Agent 模式。它既是 Executor（生成代码），又是 Planner（在失败时自主决策修复策略）。

值得注意的是，Automation Agent 内部的 Planner 是一个**混合规划器**：
- **确定性情况** (产物已存在 / 正常推进 / 达到最大重试次数) → 规则决策，零 Token
- **模糊情况** (失败重试 / 部分质量 / 上游问题) → LLM 自主决策

这体现了一个关键设计原则：**不要为确定性决策浪费 LLM Token。**

---

### Agent ⑤: Execution Agent（执行 Agent）

```
Phase: 4.5~7
Skills: allure-report-analyzer
LangGraph 节点: execution_agent → build_execution_subgraph().compile()
```

#### 为什么需要

Automation Agent 生成了代码，但代码对不对？这只能通过实际运行来验证。

Execution Agent 是整个 SOP 中**唯一不是 LLM 主导的 Agent**。它的核心操作是：

```python
# exec_act 节点的核心逻辑
agent = AgentLoop("execution-agent", ...)
result = agent.run()  # 内部执行 pytest 子进程
```

它运行 `pytest` 并收集 Allure 结果。它的 LLM 调用（allure-report-analyzer Skill）只用于**解读**执行结果，而不是执行本身。

#### 如果没有 Execution Agent

生成的代码永远不会被验证。这在自动化测试中是最致命的——**未经验证的测试代码比没有测试更危险，因为它制造了虚假的安全感。**

#### 解决了什么问题

**代码→验证的闭环**。在 SOP 流水线中，Execution Agent 是"自动化→执行→Bug分析→报告"连接的枢纽：

```
Automation → Execution → (成功 → Report)
                        → (失败 → Bug Analysis → Automation(fix) → Execution)
```

#### 为什么它有独立的 SubGraph 而不是 AgentLoop？

这是一个重要的设计决策。看 `execution_graph.py` 的图结构：

```
entry → act → gate → exit
```

Execution Agent 有独特的逻辑：
- `exec_gate`: 检查 allure-results 目录是否有产出（门禁）
- `exec_act`: 内部调用 AgentLoop（因为需要 subprocess 管理）
- `execution_failed` 标志：这个标志被顶层 `route_next_phase` 读取，决定是否触发 Bug Analysis

**关键洞察**: 不是所有 Agent 都用纯 AgentLoop。Execution Agent 因为需要设置 `execution_failed` 标志（影响顶层路由），所以用 SubGraph 提供了更细粒度的控制。

#### Agent 模式归类

**Executor Agent（纯执行 Agent）** — 最小的自主决策权，最大的确定性。它的"智能"不在于决策，而在于可靠地执行 pytest、收集结果、生成 Allure 报告。

这是 Agent 光谱上的另一端：从 Automation Agent 的高自主性到 Execution Agent 的高确定性。

---

### Agent ⑥: Bug Analysis Agent（Bug 分析 Agent）

```
Phase: 4.5~7（仅 Execution 失败时触发）
Skills: bug-analysis, ci-pipeline-analysis, jenkinsfile-generator
Modes: single (单个失败) | batch (批量分类)
LangGraph 节点: bug_analysis_agent → build_bug_analysis_compiled()
```

#### 为什么需要

测试失败后，错误信息往往不直观：
```
ElementClickInterceptedException: element click intercepted
  at line 47 in test_alarm_config.py
```

这是定位器问题？Vue 渲染问题？Element Plus 弹窗遮挡？网络延迟？

Bug Analysis Agent 负责**超越异常堆栈进行根因分析**，特别集成了 RAG 已知问题匹配。

#### 如果没有 Bug Analysis Agent

```
Execution Agent: "3 个用例失败"
人类: "为什么失败？"
Automation Agent(fix): "我试试... 改了定位器 → 还是失败"
人类: "为什么还失败？"
Automation Agent(fix): "我再试试... 加了等待 → 还是失败"
                       ↓
              变成了"修→跑→失败"的无限猜谜游戏
              同一个 Bug 在 equipment 模块修了
              3 天后 system-user 模块遇到同样的问题，重新猜一遍
```

#### 解决了什么问题

1. **根因分析的 RAG 加速** — 首先搜索已知问题库（"这个 ElementClickIntercepted 以前遇到过吗？"），如果匹配直接复用已知修复方案。只有新问题才进行 LLM 深度分析。

2. **自动修复循环 + Human-in-the-Loop** — 这是整个系统最复杂的状态机：

```
analyze_fail → auto_fix → request_approval ─┬─approved→ verify ─┬─cycle<3→ analyze_fail
                                             │                    └─cycle=3→ report
                                             └─rejected→ report → exit
```

**关键设计: HITL in the loop, not on the side**。修复方案**必须**经人工审批才能执行。这不是"AI 修完了人看看"，而是"AI 提出方案→人批准→AI 执行→验证→达标则闭环"。

3. **跨模块知识复用** — Bug Analysis 的 RAG 搜索不仅查本模块的已知问题，还查：
   - 其他模块的技术分析（类似 UI 组件可能有相同问题）
   - 其他模块的页面分析（类似页面结构可能有相同坑位）

```
# analyze_fail_node 的 RAG 逻辑（摘要）
rag_matches = search_known_issues(query, n_results=5)        # 已知问题库
cross_module_hits = search_context(query, "tech_analysis")   # 跨模块技术分析
page_hits = search_context(query, "page_context")            # 跨模块页面分析
```

#### 它有整个系统中最复杂的 SubGraph

Bug Analysis Agent 不能用 AgentLoop，因为它需要：
- **循环**: analyze → fix → verify → (重新 analyze)
- **HITL interrupt**: `interrupt()` 暂停执行等待人工输入
- **条件路由**: 循环还是退出？

这些超出了 AgentLoop 的能力范围。LangGraph 的 `interrupt()` + 条件边完美解决了这个问题。

#### Agent 模式归类

**Reviewer/Debugger Agent with HITL（带人机协作的审查 Agent）**

这是学术界最前沿的 Agent 模式之一。关键特征：
- **自主分析**（RAG + LLM 深度分析）
- **自主修复**（生成 fix code）
- **人在回路中**（修复方案必须审批）
- **自动验证**（重新运行测试）
- **循环直至解决**（最多 3 次）

这实际上实现了一个**受限的自主循环 (Constrained Autonomous Loop)**——Agent 有自主权，但受限于：(1) 人的审批 (2) 最大 3 次循环 (3) 验证必须通过。

---

### Agent ⑦: Report Agent（报告 Agent）

```
Phase: 8~9
Skills: report-generator (三模式: test-summary | progress | excel), excel-exporter
LangGraph 节点: report_agent → build_report_subgraph().compile()
```

#### 为什么需要

原始测试结果（Allure JSON）对非技术人员是不可读的。团队 PM 需要看"测了多少、通过率多少、风险在哪"，而不是看 JSON。

Report Agent 是**信息聚合和格式转换** Agent。

#### 如果没有 Report Agent

所有结果散落在 Allure JSON 文件中，每次汇报都要人工整理。

#### 解决了什么问题

**结构化输出 (Structured Output)** — 把机器可读的测试结果转化为人类可读的报告。三种模式覆盖不同场景：

| 模式 | 用途 | 消费者 |
|------|------|--------|
| test-summary | 单次执行的测试总结 | QA Lead |
| progress | 模块整体进度 | PM |
| excel | 综合数据导出 | 管理层 |

#### Agent 模式归类

**Synthesizer Agent（合成 Agent）** — 消费多个数据源，产出聚合视图。和 Analyzer Agent 的区别：
- Analyzer: 非结构化 → 结构化（提取信息）
- Synthesizer: 多个结构化 → 一个聚合视图（合并信息）

---

### Agent ⑧: Knowledge Agent（知识 Agent）

```
Phase: 横向贯穿（所有 Agent 输出都可能触发）
Skills: knowledge-manager (双模式: extract | precipitate), completeness-check (Secondary)
LangGraph 节点: knowledge_agent → build_knowledge_subgraph().compile()
```

#### 为什么需要

在 8 个 Agent 中，Knowledge Agent 是最特殊的一个。它是**唯一有跨 Agent 写入权限的 Agent**（唯一写入原则）。

为什么需要这个限制？考虑如果没有这个原则：

```
Bug Analysis Agent: "这个经验值得沉淀" → 写入 known_issues.yaml
Automation Agent:   "这个定位技巧值得记录" → 写入 element-plus-pitfalls.yaml
Test Design Agent:  "这个测试模式值得复用" → 写入 test-patterns.yaml
                    ↓
            三个 Agent 都往知识库写
            没有一个统一的入口
            内容格式不一致
            重复和冲突无法检测
```

#### 如果没有 Knowledge Agent

**知识流失 (Knowledge Attrition)** — 每个 Bug 只被修复一次，但同样的根因可能在不同模块反复出现。没有 Knowledge Agent，每次都要从零开始分析。

具体场景：
```
6 月 1 日: equipment 模块发现 "el-dialog 关闭后页面未刷新导致 StaleElement"
          → Bug Analysis 分析并修复 → 修复完成，经验未记录

6 月 15 日: system-user 模块出现同样的 StaleElement 问题
           → Bug Analysis 重新分析（浪费 20 分钟）
           → RAG 中没有匹配（因为上次没记录）
           → 从头分析根因 → 发现和 equipment 一样的问题
```

有 Knowledge Agent：
```
6 月 1 日: Bug 修复完成
          → Knowledge Agent 提取模式: "el-dialog 关闭后页面未刷新 → StaleElement"
          → 写入 known_issues.yaml
          → RAG 自动索引

6 月 15 日: system-user 模块同样问题
           → Bug Analysis RAG 匹配命中 (score 0.92)
           → 直接复用修复方案 (30 秒)
```

#### 解决了什么问题

1. **知识去重和标准化** — 只有一个入口写入知识库，所以可以：
   - 检查是否与已有条目重复
   - 强制使用统一的格式
   - 维护知识条目之间的关联

2. **事件驱动沉淀** — Knowledge Agent 在 SOP 末尾运行，处理 Event Bus 上积压的事件：
   ```python
   # knowledge_act 节点
   process_pending()  # 处理所有积压的 AgentCompleted/CycleEnd 事件
   index_known_issues()  # 确保 RAG 索引是最新的
   ```

3. **全局审计** — Knowledge Agent 也是 `completeness-check` 的 Secondary Owner，可以在测试周期结束时检查是否有遗漏的产物。

#### 为什么使用 SubGraph 而不是 AgentLoop？

Knowledge Agent 的独特之处在于**事件总线处理**和**RAG 增量索引**是程序化操作（不需要 LLM），只有 `knowledge-manager` Skill 需要 LLM：

```
entry → act (AgentLoop + EventBus + RAG) → exit
```

#### Agent 模式归类

**Curator Agent（策展 Agent）** — 横向贯穿的元 Agent。它不产生直接的测试产出（不分析页面、不生成代码、不运行测试），而是**管理和维护其他 Agent 产生的知识**。

在学术分类中，这属于**正交关注点 Agent (Cross-Cutting Concern Agent)**。它的工作方向是"横向"的——贯穿所有 Phase，而不是"纵向"的——完成一个特定 Phase。

---

## 3. 横向分析：Full SOP 编排器

```
Category: Orchestrator（非独立 Agent）
LangGraph: build_sop_graph() → CompiledGraph
```

### 编排器 vs Agent

Full SOP 不是 Agent，它是编排器。区别在于：

| | Agent | Orchestrator |
|---|-------|-------------|
| 知道什么 | 知道自己领域的 Skill 和决策规则 | 知道所有 Agent 的顺序、依赖和触发条件 |
| 决策什么 | 这个 Skill 要不要重试 | 下一个执行哪个 Agent |
| 状态范围 | Agent 内部状态 | 全局 Phase 状态、Page 迭代状态 |

### 编排器的条件路由

`sop_graph.py` 的核心是 `route_next_phase` 函数：

```python
def route_next_phase(state: SOPState) -> str:
    # 致命错误 → exit
    if state.get("fatal_error"):
        return "exit"

    # 按 CANONICAL_PHASES 顺序检查
    for phase in CANONICAL_PHASES:
        if phase in completed or phase in skipped:
            continue

        # Bug Analysis 的特殊规则: 仅执行失败时触发
        if phase == "Bug Analysis" and not execution_failed:
            continue  # 自动跳过

        return PHASE_TO_NODE[phase]

    return "exit"  # 所有 Phase 完成
```

**设计亮点**: 条件路由不是硬编码的 if-else，而是**数据驱动的状态机**。每个 Agent 完成后调同一个 `route_next_phase`，根据 `completed_phases` + `skip_phases` + `execution_failed` + `fatal_error` 决定下一步。

### 断点续跑 (Checkpoint/Resume)

LangGraph 的 SqliteSaver 提供了**时间旅行调试**能力：

```python
# 每个 Agent 执行后的状态自动持久化
compiled.invoke(state, {"configurable": {"thread_id": "my-run"}})

# 如果中断（API 超时/用户取消），用同一个 thread_id 恢复
compiled.invoke(None, {"configurable": {"thread_id": "my-run"}})
```

这是 Agent 工程的**生产级需求**——真实的 Agent 流水线可能运行数小时，必须能从中断点恢复。

---

## 4. 综合：Agent 模式全景图

```
                        自主性高
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   Bug Analysis       Automation        Knowledge
   (Reviewer/HITL)    (Executor+Planner) (Curator)
        │                  │                  │
   ─────┼──────────────────┼──────────────────┼───── 决策复杂度
        │                  │                  │
   Test Design         Requirement        Project
   (Planner)           (Analyzer)         (Bootstrapper)
        │                  │                  │
   ─────┼──────────────────┼──────────────────┼─────
        │                  │                  │
   Execution           Report
   (Deterministic      (Synthesizer)
    Executor)
        │
   确定性高
```

### 按模式的完整分类

| # | Agent | 模式 | 自主决策 | 核心特征 |
|---|-------|------|---------|---------|
| ① | Project Agent | **Bootstrapper** | 低 | 一次性建立全局上下文 |
| ② | Requirement Agent | **Analyzer** | 中低 | 非结构化→结构化领域模型 |
| ③ | Test Design Agent | **Planner** | 中 | 制定"测什么"的计划 |
| ④ | Automation Agent | **Executor + Internal Planner** | 高 | 混合规划器（规则+LLM），质量闭环 |
| ⑤ | Execution Agent | **Deterministic Executor** | 极低 | 子进程执行，最大化确定性 |
| ⑥ | Bug Analysis Agent | **Reviewer w/ HITL** | 高 | 受限自主循环+人机协作 |
| ⑦ | Report Agent | **Synthesizer** | 低 | 多源聚合，结构转换 |
| ⑧ | Knowledge Agent | **Curator (Cross-Cutting)** | 中 | 横向贯穿，唯一写入权 |
| — | Full SOP | **Supervisor/Orchestrator** | — | 条件路由+断点续跑 |

---

## 5. 核心设计原则提炼

从本项目中可以提炼出以下 Agent 工程设计原则：

### 原则 1: 分层是 Agent 工程的第一性原理

```
Skill (怎么做) → Agent (做什么+做对没) → Graph (何时做) → Orchestrator (全局去哪)
```

每一层解决不同粒度的问题。不要把路由逻辑放在 Agent 里，不要把质量检查放在 Skill 里，不要把编排逻辑放在路由里。

### 原则 2: 确定性决策不应该消耗 LLM Token

Automation Agent 的混合规划器是最好的例子：

| 情况 | 决策者 | Token 消耗 |
|------|--------|-----------|
| 产物已存在，跳过 | 规则 | 0 |
| 正常推进下一步 | 规则 | 0 |
| 达到最大重试次数 | 规则 | 0 |
| 失败但原因模糊 | LLM | ~300 |

**问自己**: "这个决策的规则能写出来吗？" 如果能，就不要调用 LLM。

### 原则 3: 唯一写入原则预防知识漂移

多 Agent 系统中，如果一个资源（知识库、上下文文件）可以被多个 Agent 写入，冲突和重复是必然结果。指定一个 Agent 为 Primary Owner。

### 原则 4: Agent 通过文档通信，不共享内存

```
Agent A → 写入 MODULE_CONTEXT.md → Agent B 读取 MODULE_CONTEXT.md
```

不是：
```
Agent A → 共享内存 / 共享变量 → Agent B
```

文档通信的优势：
- **可调试**: 中间产物可以人工检查
- **可恢复**: 从任意 Phase 恢复只需读取文档
- **去耦合**: Agent B 不依赖 Agent A 的运行环境

### 原则 5: 每个 Agent 有明确的 "不要做什么"

观察 `agent-definitions.yaml` 中每个 Agent 的 `boundaries`:

```yaml
automation-agent:
  boundaries:
    - 不设计测试用例
    - 不分析页面元素清单
    - 不诊断失败根因
    - 不执行测试
```

这些否定规则比肯定规则更重要。肯定规则定义 Agent 的范围（scope），否定规则定义 Agent 的边界（boundary）。没有边界的 Agent 会逐渐侵占其他 Agent 的职责。

### 原则 6: HITL 是循环内部的，不是循环外部的

Bug Analysis Agent 的 HITL 模式：
```
✅ analyze → fix → 【人类审批】 → execute → verify
```

而不是：
```
❌ analyze → fix → execute → verify → 【人类看结果】
```

人在循环**内部**意味着：错误的修复不会被执行，人的判断是流程的必要环节而非事后检查。

---

## 6. 反模式警示

本项目架构演化的过程中也经历了反模式，值得记录：

### 反模式 1: One Big Agent

v1.0 时代只有 4 个 Agent（analysis/design/code/diagnosis），每个职责过重。

| v1.0 | v2.0 | 拆分理由 |
|------|------|---------|
| analysis-agent | project-agent + requirement-agent + test-design-agent | 项目/需求/设计是三个不同的关注点 |
| design-agent | test-design-agent + automation-agent | 设计和实现必须分离 |
| code-agent | automation-agent | 升级为带内部规划器的真 Agent |
| diagnosis-agent | bug-analysis-agent + report-agent + knowledge-agent | 诊断/报告/知识是三种不同的产出 |

**教训**: 如果一个 Agent 的 Skill 链超过 5 个，或者它的触发关键词列表跨了三个不同的领域，那么它应该被拆分。

### 反模式 2: AgentLoop vs SubGraph 双重实现

P0-1 统一前，project/test-design/automation 既有 AgentLoop 的实现，又在各自的 SubGraph 中重复实现相同的 Perceive→Plan→Act→Observe→Update 逻辑。这是**最危险的重复**——两者会漂移。

**教训**: 对于简单的 Skill 链 Agent，AgentLoop 足够。对于需要循环/条件/HITL 的 Agent，使用 SubGraph 但不要同时在 AgentLoop 中实现相同逻辑。

### 反模式 3: 没有明确 Primary Owner 的 Skill

`completeness-check` 曾经被多个 Agent 引用，但没有明确谁负责它的维护和优化。修复方式是：Project Agent = Primary Owner，Knowledge Agent = Secondary Owner。

**教训**: 每个跨 Agent 共享的能力（Skill/MCP Tool/RAG Collection）必须有一个 Primary Owner Agent。

---

## 7. 总结：这条 Agent 架构的学习路径

如果你要从这个项目中学习 Agent 工程，建议按以下顺序：

1. **先理解 Skill 层** — 读 `skill-registry.yaml` 和任意 2-3 个 Skill markdown 文件。理解 "一个 Skill 就是一个 Prompt 模板 + 上下文注入 + LLM 调用"。

2. **再理解一个 Agent** — 最好从 Automation Agent 开始（它最完整），读 `agent_runner.py` 的 AgentLoop 类。理解 Perceive→Plan→Act→Observe→Update 循环。

3. **再理解编排层** — 读 `sop_graph.py` 和 `bug_analysis_graph.py`。理解 Agent 如何被组织成状态图，条件路由如何工作，HITL 如何实现。

4. **最后看全局** — 读 `agent-definitions.yaml`，理解 8 个 Agent 的职责划分和协作关系。

5. **动手实验** — 尝试回答："如果要加第 9 个 Agent（比如 Security Testing Agent），它应该放在哪个 Phase？绑定哪些 Skill？边界在哪里？"

---

> **文档版本**: 2026-06-13 · 基于项目 v2.0 Agent 架构 · 纯教学用途
