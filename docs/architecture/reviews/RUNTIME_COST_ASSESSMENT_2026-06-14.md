# AI Agent 系统 — 运行时成本与结构评估报告

> **评估日期**: 2026-06-14  
> **评估范围**: 8 Agent v2.0 + LangGraph 编排引擎 + AgentLoop 执行引擎  
> **评估模式**: 分析 Only（不修改代码）  
> **用途**: 为后续优化设计提供数据基础

---

## 1. 当前 Agent 架构简述

系统采用 **四层架构**：

```
┌─ L0: 治理层 (声明式) ──────────────────────────────────┐
│  agent-definitions.yaml → 8 Agent 定义 (单一事实源)      │
│  governance/skills/ → 24 个 Skill Markdown (Prompt 模板) │
│  governance/context/ → 项目/模块/页面上下文 (事实源)      │
│  .claude/skills/*/SKILL.md → Claude Code 适配层          │
└──────────────────────────────────────────────────────────┘
                          ↓ 被调用
┌─ L1: LangGraph 编排层 (Python) ─────────────────────────┐
│  sop_graph.py → 9 Phase DAG (entry→preflight→route→...)  │
│  nodes.py → AgentLoop节点工厂 / pass-through 占位节点     │
│  bug_analysis_graph.py → 自动循环修复子图 (max 3 cycles)  │
│  execution_graph.py → 执行/报告/知识 子图                  │
└──────────────────────────────────────────────────────────┘
                          ↓ 调用
┌─ L2: AgentLoop 执行引擎 (Python) ───────────────────────┐
│  Perceive→Plan→Act→Observe→Update 循环                   │
│  Skill 顺序执行 (无并行)                                  │
│  Plan 阶段: 规则决策 + LLM 回退决策                        │
│  Observe 阶段: 机械检查 (grep 红线) + 文件存在性检查       │
└──────────────────────────────────────────────────────────┘
                          ↓ 调用
┌─ L3: LLM 基础设施 ──────────────────────────────────────┐
│  skill_loader.py → 加载 Skill Markdown                   │
│  context_injector.py → RAG + 文件读取注入上下文            │
│  prompt_adapter.py → Provider 适配 + 截断                 │
│  provider.py → LLM API 调用                              │
└──────────────────────────────────────────────────────────┘
```

**关键特征**：
- Agent 间通过**文件系统**传递状态（不共享会话，不传递上下文）
- 每个 Agent 是 **Skill 的顺序链**（5 for automation-agent, 3 for test-design-agent, 1-2 for others）
- 存在**双重执行路径**：LangGraph 编排 (headless) vs Claude Code SKILL.md (交互式)
- AgentLoop 是 P0-1 统一后的**唯一执行引擎**

---

## 2. 运行时行为分析

### 2.1 Token 使用结构

**Prompt 构成（每次 Skill 调用）**：

| 组成部分 | 来源 | 估算 Tokens | 说明 |
|----------|------|------------|------|
| Skill Prompt | `governance/skills/*.md` | 1,200–1,800 | ~150行 Markdown，含指令+规则+示例 |
| RAG 上下文 | ChromaDB 检索 (≤3条×500chars) | 200–400 | 按 Skill 类型注入 |
| 文件上下文 | PAGE_CONTEXT.md 等 (截断到3000chars) | 0–800 | 仅部分 Skill 需要 |
| 用户输入 | AgentLoop._build_user_input() | 50–150 | 模块/页面/重试信息 |
| 重试附加上下文 | 之前的错误/质量问题 | 0–300 | 仅在重试时注入 |

**单次 Skill LLM 调用总输入**: **约 1,500–3,500 tokens**

**完整 Agent 执行的 Token 消耗估算（以 automation-agent 为例，5 Skills）**：

| 场景 | Skills × Tokens | 额外调用 | 总输入估算 |
|------|----------------|---------|-----------|
| 全部首次通过 | 5 × 2,500 | 0 | ~12,500 |
| 2个Skill各重试1次 | 7 × 2,800 | 2× LLM Plan (~300 each) | ~20,200 |
| 最坏情况 (每Skill重试3次) | 15 × 3,000 | 8× LLM Plan | ~47,400 |

**Token 结构问题识别**：
1. **Prompt 重复加载**: 每次 `run_skill()` 都重新 `load_skill()` → `inject()` → `adapt()`，Skill Markdown 文件每次都从磁盘重新读取，但 RAG 检索也是每次重新执行
2. **上下文重复注入**: `context_injector.py` 中 `PAGE_CONTEXT.md` 等文件在 automation-agent 的 2-3 个 Skill 中都会被注入（tech-analysis 注一次、page-object-generator 可能再注一次），无缓存
3. **SKILL_CONTEXT_MAP 存在 but 无重用**: 每个 Skill 独立做 RAG 查询，相邻 Skill（如 tech-analysis → auto-strategy）查询结果大部分重叠

### 2.2 Step 行为分析

**单个 Agent 执行的步骤数**：

| Agent | Skills | 最小 Steps | 典型 Steps (含1次重试) | 最大 Steps |
|-------|--------|-----------|----------------------|-----------|
| project-agent | 3 | 3 | 4 | 9 |
| requirement-agent | 2 | 2 | 3 | 6 |
| test-design-agent | 3 | 3 | 4 | 9 |
| **automation-agent** | **5** | **5** | **7** | **15** |
| execution-agent | 1 | 1 | 2 | 3 |
| bug-analysis-agent | 1(3) | 1(3) | 2(5) | 3(9) |
| report-agent | 1 | 1 | 2 | 3 |
| knowledge-agent | 1 | 1 | 2 | 3 |

> 注：bug-analysis 在 LangGraph 中拆为子图 (analyze→fix→approve→verify→loop)，每次循环=4个节点+2-3个LLM调用。

**循环思考识别**：

1. **Plan 阶段的 LLM 回退 (`_llm_plan()`)**: 当 Skill 失败或部分通过时触发。这是一个**额外 LLM 调用**（~500 input tokens + 300 output tokens），相当于每一步失败都多花一次调用。回退决策prompt (~750 chars) 会重新列出所有 Skill 状态 + 质量问题 + 决策规则。

2. **Bug-analysis 循环**: 每次循环 = analyze_fail (LLM + RAG 5 collections) → auto_fix (LLM) → verify (pytest subprocess)。最多3次。如果3次都失败，消耗约 6-9 次 LLM 调用 + 15 次 RAG 查询（5 collections × 3 cycles）+ 3 次 pytest 执行。

3. **AgentLoop 主循环的 Plan 重试逻辑**: `plan()` 方法中，当 `observation.suggestion == "retry"` 时不增加 skill_index，下次循环走 `_llm_plan()` 再次决策。这允许同一 Skill 被重试最多3次，但每次都消耗一次 LLM Plan 调用。

### 2.3 Tool Call 使用情况

**按 Skill 类型的工具调用模式**：

| Skill 类型 | 调用前 | 调用中 | 调用后 |
|-----------|--------|--------|--------|
| LLM Skills | ContextInjector (RAG×2-3 + File×1-2) | LLM API call | Observe (文件检查 + grep) |
| 机械 Skills (code-consistency-checker) | 无 | 本地 grep | Observe (parse output) |
| Execution | AgentLoop.run() | pytest subprocess | gate check |

**重复 Tool Call 识别**：

1. **RAG 重复查询**: `bug_analysis_graph.py` 的 `analyze_fail_node()` 对 **5 个不同的 ChromaDB collection** 分别做 RAG 查询（known_issues, tech_analysis × 跨模块 + 本模块, page_context × 跨模块），其中已知问题查询与 `context_injector.py` 中 `diagnosis/bug-analysis` 的 SKILL_CONTEXT_MAP 存在重叠。

2. **Preflight 全量扫描**: `preflight_node()` 每次调用都扫描所有页面目录和文件，无论 mode 是什么。`status` 模式也会全量扫描再退出。

3. **文件读取无缓存**: `context_injector._resolve_file()` 每次调用都重新读取文件。同一个 PAGE_CONTEXT.md 在 automation-agent 的多个 Skill 中可能被读取2-3次。

4. **Gate 检查调用 Python 子进程**: 每个 Agent 启动时运行 `python ZJSN_Test-master526/tools/check_sop_gate.py`，这是一个独立的 Python 进程调用。

**低价值 Tool Call**：

1. `prompt_adapter.py` 的 `_inject_few_shot()` — 对 Claude provider 永远是 no-op（`add_examples: False`），但每次都会执行检查。
2. `agent_runner.py` 的 TraceEvent 发射在每个 Skill 执行后，虽然有 try/except 保护，但正常情况下每次都会尝试写入追踪文件。
3. `execution_graph.py` 的 `knowledge_act()` 中显式调用 `index_known_issues()`、`index_tech_analysis()`、`index_page_context()` 做全量 RAG 索引更新 — 这是 O(N) 的全量操作。

### 2.4 Context 管理

**当前 Context 传递机制**：

```
Agent A (文件产出) → 文件系统 (context/modules/X/pages/Y/*.md)
                  → Agent B (通过 context_injector 读取)
```

**无会话级上下文传递** — Agent 之间完全通过文件系统解耦。这是设计原则（SOP 规则2），但也带来成本：

1. **每个 Agent 独立加载全部上下文**: automation-agent 的 tech-analysis Skill 通过 context_injector 加载 PAGE_CONTEXT.md（最多3000 chars），但 page-object-generator Skill 又需要通过 PAGE_INTERFACE.yaml 或 PAGE_CONTEXT.md 重新获取页面信息。

2. **AgentLoop.memory 字段存在但范围有限**: `AgentState.memory` 在 Agent 执行期间跨 Skill 累积信息（`prev_output`、`tech_analysis_summary`、`retry_adjustments`），但**不跨 Agent 传递**。每个新 Agent 启动时 memory 为空。

3. **无 Context Compression**: `context_injector._resolve_file()` 的截断方式是简单粗暴的 `content[:max_chars]`，不区分关键信息和冗余信息。PromptAdapter 的截断方式也是 `head + tail`，中间直接丢弃。

4. **State 膨胀**: `SOPState` 使用 `Annotated[list, operator.add]` reducer 做跨节点累积，`trace_events`、`skill_observations`、`gate_results`、`per_page_results` 都会在整个 SOP 运行期间无限增长。LangGraph checkpoint 会持久化整个 State。

### 2.5 Failure / Retry 行为

**当前 Retry 机制**：

| 层级 | 机制 | 最大次数 | 退避 | 策略变化 |
|------|------|---------|------|---------|
| Skill 级 | AgentLoop.MAX_RETRIES | 3 | ❌ 无 | ❌ 依赖 LLM Plan 决策 |
| Bug 循环 | bug_cycle_max | 3 | ❌ 无 | ❌ 同策略循环 |
| LLM Plan 回退 | _llm_plan() → 规则回退 | 1 (then fallback) | ❌ 无 | ✅ 一次 LLM 尝试后回退规则 |

**Retry 风暴风险**：

1. **最坏情况**: automation-agent 的 5 个 Skill 各重试 3 次 → 15 次 LLM 调用 + 8 次 LLM Plan 调用 = **23 次 LLM 调用**。加上 bug-analysis 的 3 次循环（每次 2-3 次 LLM + 5 次 RAG），单个模块可能消耗 **30+ 次 LLM 调用**。

2. **策略收敛**: `_llm_plan()` 在 Skill 重试时会注入 `adjustments` 建议到 memory，但 bug-analysis 的循环 (`analyze_fail → auto_fix → verify`) **无策略变化**——每次都是同样的 analyze → fix 流程。如果根因是环境问题或产品 Bug，3 次循环都是浪费。

3. **无指数退避**: 重试之间无延迟，失败后立即重试。

4. **确定性失败的浪费**: `code-consistency-checker` 的 Observe 正确标记了 `suggestion: "continue"` (而非 "retry")，因为机械检查是确定性的。但 LLM-based Skill 的重试决策依赖 LLM Plan，可能误判。

---

## 3. 成本浪费点清单（按严重程度排序）

### 🔴 P0 — 高严重度

| # | 浪费点 | 机制 | 每次成本估算 | 频率 |
|---|--------|------|------------|------|
| 1 | **automation-agent Skill 链顺序执行 + 重试** | 5 Skills × (1 + retries) LLM 调用，无并行 | 12,500–47,400 input tokens | 每个页面 |
| 2 | **Bug-analysis 全量 RAG (5 collections)** | `analyze_fail_node()` 启动时查询 known_issues + tech_analysis(跨模块) + tech_analysis(本模块) + page_context(跨模块) | 5 次 ChromaDB 查询 + embedding 计算 | 每个失败 |
| 3 | **LLM Plan 额外调用** | 每个 Skill 失败/部分通过时触发 `_llm_plan()`，重新列出全部 Skill 状态 | ~800 input + 300 output tokens | 每次重试 |
| 4 | **Preflight 全量文件扫描** | 扫描所有页面 × 所有产物文件 | 数十次 `Path.exists()` + `stat()` | 每次编排启动 |

### 🟡 P1 — 中严重度

| # | 浪费点 | 机制 | 成本 | 频率 |
|---|--------|------|------|------|
| 5 | **上下文无跨 Skill 缓存** | 同一个 PAGE_CONTEXT.md 在 automation-agent 的 3 个 Skill 中被分别加载 | 每次 3,000 chars R/O | 每个 Agent 内 2-3 次 |
| 6 | **RAG 重复查询** | context_injector 的 RAG 与 bug_analysis 的 RAG 各自独立查询 ChromaDB | 每次 3-5 次 embedding | 跨 Skill 重复 |
| 7 | **SOPState 无限累积** | trace_events/skill_observations/gate_results 用 operator.add 无限追加，LangGraph checkpoint 持久化全部 | checkpoint DB 膨胀 | 全流程 |
| 8 | **每次 Skill 独立 load_skill + inject + adapt** | Pipeline 无缓存，相同 Skill Prompt 被反复从磁盘加载和适配 | 磁盘 I/O + YAML 解析 | 每次 run_skill() |

### 🟢 P2 — 低严重度

| # | 浪费点 | 机制 |
|---|--------|------|
| 9 | `_inject_few_shot` 对 Claude provider 永远是 no-op | 每次都执行模板匹配 + 字符串检查 |
| 10 | `knowledge_act()` 全量 RAG 索引更新 | `index_known_issues()` + `index_tech_analysis()` + `index_page_context()` O(N) |
| 11 | `prompt_adapter.py` 截断策略粗糙 | head+tail 丢弃中间，可能丢失关键信息 |
| 12 | TraceEvent 每次 Skill 执行后都写文件 | 累积 I/O |

---

## 4. 风险评估

### 🔴 高风险

| 风险 | 触发条件 | 影响 |
|------|---------|------|
| **Token 消耗爆炸** | automation-agent 在一个复杂页面全部 Skill 失败+重试 | 单模块单页面 **47K input tokens**，约 $0.15-0.70 (按模型) |
| **Bug-analysis 循环失控** | 环境问题/产品 Bug 无法通过代码修复解决 | 3 次循环 × (2 LLM + 5 RAG + pytest) = 6 LLM + 15 RAG + 3 subprocess，全部浪费 |
| **多页面 × 多 Agent 串行叠加** | full-sop 对 5 页面模块，每个页面走 automation-agent 全流程 | 5 × 47K = **235K tokens** 仅自动化阶段 |

### 🟡 中风险

| 风险 | 触发条件 | 影响 |
|------|---------|------|
| **State 无限膨胀导致 checkpoint 过大** | 长时间运行 + 多页面 | SqliteSaver checkpoint 膨胀，resume 时恢复成本高 |
| **Preflight 扫描成本** | 每个模块启动都全量扫描 | 文件 I/O 成本与页面数线性增长 |
| **上下文碎片化** | 同一文件在多 Skill 间独立加载，截断点不同 | 下游 Skill 可能看到不完整或不一致的上下文 |

### 🟢 低风险

| 风险 | 说明 |
|------|------|
| PromptAdapter 截断丢失信息 | 仅影响非 Claude provider (OpenAI 8K limit / Ollama 4K limit) |
| TraceEvent I/O 累积 | 有 try/except 保护，不会导致主流程中断 |

---

## 5. 优化建议（仅建议，不修改代码）

### 5.1 P0 优先级

**建议 1: Skill 间上下文缓存**
- 在 AgentLoop 中维护一个 `_context_cache`，存储 context_injector 的结果（RAG 结果 + 文件内容）
- 同一 Agent 内的多个 Skill 共享缓存，避免重复 RAG + 文件读取
- 预估节省: automation-agent 减少 40-60% 的 context 加载成本

**建议 2: Bug-analysis RAG 查询合并**
- 将 `analyze_fail_node()` 的 5 次独立 RAG 查询合并为 2-3 次批量查询
- ChromaDB 支持 `query_texts` 的 batch 模式，一次 embedding 多个 query
- 预估节省: bug-analysis 启动成本减少 50%

**建议 3: LLM Plan 调用条件化**
- 仅在特定条件下触发 `_llm_plan()`（如首次失败、或上次重试无改善）
- 对明确的代码红线违规（time.sleep/绝对XPath），规则决策即可，不必调 LLM
- 预估节省: 每个失败 Skill 节省 1 次 LLM 调用

**建议 4: Skill Prompt 加载缓存**
- `skill_loader.load_skill()` 的结果在 AgentLoop 生命周期内缓存
- 同一 Skill 重试时不需要重新从磁盘加载 + YAML 解析
- 预估节省: 重试场景减少磁盘 I/O

### 5.2 P1 优先级

**建议 5: State 字段分级持久化**
- 区分"编排必需"字段 (completed_phases, failed_phases) 和"追踪/调试"字段 (trace_events, skill_observations)
- 追踪字段用 ring buffer 或限制最大条目数
- 预估效果: checkpoint 大小稳定

**建议 6: Preflight 结果缓存**
- `preflight_node()` 结果按 module 缓存为 JSON
- 仅在上下文文件 mtime 变化时重新扫描
- 预估节省: resume/status 模式的扫描成本

**建议 7: PAGE_INTERFACE.yaml 推广**
- 当前已设计但仅在 automation-agent 中使用
- test-design-agent 的 page-analysis 产出此文件后，应强制下游 Skill 优先消费 YAML (~200 tokens) 而非 Markdown (~2000 tokens)
- 预估节省: automation 阶段每个 Skill 节省 ~500-800 input tokens

### 5.3 P2 优先级

**建议 8: Prompt 模板预热**
- 在 AgentLoop 初始化时预加载所有 Skill Prompt
- 避免每个 Skill 逐个冷加载

**建议 9: 分批 RAG 索引更新**
- `knowledge_act()` 的全量索引改为增量（仅索引新文件/变更文件，使用 mtime 检测）

**建议 10: 跟踪 Bug-analysis 失败模式**
- 记录每次 bug-analysis 循环的最终 resolution（fixed / rejected / max_cycles_exceeded / env_issue）
- 当某模块 2 次达到 max_cycles 且根因为 env_issue 时，跳过后续自动循环

---

## 总结

| 维度 | 当前状态 | 核心问题 | 严重度 |
|------|---------|---------|--------|
| Token 使用 | 每次 Skill 1,500-3,500 input tokens，无缓存 | 上下文重复加载，跨 Skill 无复用 | 🔴 |
| Step 行为 | Skill 顺序执行 + 失败 LLM 回退 | LLM Plan 在每个失败上额外消耗 | 🟡 |
| Tool Call | RAG + 文件读取 + grep + pytest | RAG 查询重复（bug-analysis 5次） | 🔴 |
| Context 管理 | 文件系统传递，无跨 Agent 上下文 | 文件截断粗糙，State 无限累积 | 🟡 |
| Retry 行为 | MAX_RETRIES=3，bug_cycle_max=3 | 无退避，无策略变化，环境问题浪费循环 | 🟡 |
| 最烧 Token | automation-agent 5 Skills × 重试 | 单页面可达 47K input tokens | 🔴 |
| 最浪费 Step | Bug-analysis 对环境问题做代码修复循环 | 3 次循环全浪费 | 🟡 |
| 最易失控 | LLM Plan 每次失败都调 LLM | 重试风暴 15+23=38 次 LLM 调用 | 🔴 |

**核心结论**: 当前系统最大的成本问题是 **上下文重复加载** 和 **无缓存的 Skill 执行链**。这两个问题叠加导致 automation-agent（最常使用的 Agent）在正常场景下消耗 ~12K tokens/页面，在重试场景下可达 ~47K tokens/页面。优化的最大杠杆点在 **AgentLoop 内引入上下文缓存** 和 **减少 RAG 重复查询**。
