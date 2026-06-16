# 项目→AI工程体系 完整映射

> **写作目的**: 教学文档。将当前项目每个组件映射到 AI 工程的概念体系，评估已掌握的/缺失的能力，定位到主流技术栈，给出学习路线图。
> **核心论点**: 本项目的每一块代码都是某个 AI 工程概念的**工程化落地**。理解映射关系 = 理解 AI 工程的实战全景。

---

## 1. 项目组件 → AI 工程概念 映射表

```
┌──────────────────────────────────────────────────────────────────┐
│                     AI 工程 10 大领域                             │
│                                                                  │
│  ① Context Engineering    ② Prompt/Capability Engineering         │
│  ③ Agent Engineering      ④ Orchestration Engineering            │
│  ⑤ Memory Architecture    ⑥ RAG Architecture                     │
│  ⑦ Tool/MCP Engineering   ⑧ Guardrails & Safety                  │
│  ⑨ Evaluation/Observability  ⑩ Human-in-the-Loop                 │
└──────────────────────────────────────────────────────────────────┘
```

### ① Context Engineering（上下文工程）

> **AI 工程定义**: 将非结构化的项目知识转化为 LLM 可高效消费的结构化上下文。管理上下文的生命周期：创建→索引→注入→更新。

| 项目组件 | 文件位置 | AI 工程概念 | 说明 |
|---------|---------|-----------|------|
| PROJECT_CONTEXT.md | `governance/context/.../PROJECT_CONTEXT.md` | **Structured Context / Source of Truth** | 全项目单一事实源。项目级稳定共性，所有 Agent 的入口上下文 |
| MODULE_CONTEXT.md | `context/.../modules/{m}/MODULE_CONTEXT.md` | **Modular Context** | 模块级上下文。页面清单、权限矩阵、业务流程 |
| PAGE_CONTEXT.md | `context/.../modules/{m}/pages/{p}/PAGE_CONTEXT.md` | **Page-Level Context** | 页面元素清单。DOM 级别细节，最细粒度上下文 |
| ContextInjector | `aitest/llm/context_injector.py` | **Context Injection / RAG-on-the-fly** | 每个 Skill 执行前，按需从 5 个 ChromaDB 集合 + 文件系统检索相关上下文，注入到 System Prompt |
| SKILL_CONTEXT_MAP | `context_injector.py:27-82` | **Context Routing Table** | 定义了 "哪个 Skill 需要哪种上下文" — 类似依赖注入的 IoC 容器 |
| context-sync Skill | `governance/skills/project/context-sync.md` | **Context Lifecycle Management** | 会话结束后同步上下文：稳定事实→context/，过程产物→artifacts/，生成 CURRENT_TASK.md |
| CURRENT_TASK.md | `context/.../modules/{m}/CURRENT_TASK.md` | **Session Continuity** | 跨会话的上下文恢复机制——"上次做到哪了" |

**掌握程度**: 🟢 **深度掌握**。本项目最突出的 AI 工程能力。实现了上下文的三级分层（项目→模块→页面）+ 双通道注入（RAG 检索 + 文件读取）+ 生命周期管理（创建→同步→归档）。

---

### ② Prompt / Capability Engineering（提示词/能力工程）

> **AI 工程定义**: 将 AI 能力封装为可复用、可版本化、可组合的 Prompt 模块。管理能力的注册、发现、能力分级。

| 项目组件 | 文件位置 | AI 工程概念 | 说明 |
|---------|---------|-----------|------|
| 24 个 Skill .md 文件 | `governance/skills/{category}/{name}.md` | **Prompt Template / Capability Module** | 每个 Skill = 结构化 Prompt 模板（目标+输入+输出+规则+检查清单） |
| skill-registry.yaml | `governance/skills/skill-registry.yaml` | **Capability Registry** | 集中注册表：Skill ID、分类、状态、依赖、替换关系 |
| agent-definitions.yaml | `governance/agents/agent-definitions.yaml` | **Capability Composition** | Agent = Skill 集合的编排声明。定义了 Agent→Skill 的绑定关系 |
| skill_loader.py | `aitest/llm/skill_loader.py` | **Prompt Loader** | 按 Skill ID 动态加载 Prompt 模板，支持 category/skill-name 格式 |
| skill_registry.py | `aitest/llm/skill_registry.py` | **Capability Tier System** | Skill 能力分级矩阵：mechanical/low/medium/high。执行前自动检查 Provider 兼容性 |
| prompt_adapter.py | `aitest/llm/prompt_adapter.py` | **Prompt Adaptation Layer** | 将 Claude 优化的 Skill Prompt 适配到 OpenAI/Ollama。XML→Markdown 转换、上下文截断、few-shot 注入 |
| Deprecated Skills (8个) | `skills/_deprecated/` | **Capability Lifecycle Management** | Skill 的归档与合并管理。6个通过多模式合并，2个因粒度过细合并 |

**掌握程度**: 🟢 **深度掌握**。实现了完整的 Capability Engineering 链路：定义→注册→加载→分级→适配→注入→生命周期管理。

---

### ③ Agent Engineering（Agent 工程）

> **AI 工程定义**: 设计具有自主决策能力的 Agent，包括感知、规划、执行、观察循环，以及 Agent 间的职责划分。

| 项目组件 | 文件位置 | AI 工程概念 | 说明 |
|---------|---------|-----------|------|
| AgentLoop | `aitest/agent_runner.py:422-1168` | **ReAct Agent Loop** | Perceive→Plan→Act→Observe→Update 循环。混合规划器：规则决策（零 Token）+ LLM 决策（模糊情况） |
| AgentState | `aitest/agent_runner.py:282-321` | **Agent Internal State** | Agent 跨步骤状态：goal、completed_skills、failed_skills、retry_counts、memory |
| AgentResult | `aitest/graphs/state.py:161-191` | **Agent Output Encapsulation** | 封装 Agent 执行结果（skills/retries/observations），隔离 Agent 内部状态与编排层 State |
| 8 Agent 定义 | `governance/agents/agent-definitions.yaml` | **Agent Role Definition** | 每个 Agent 的 system_prompt_role、skills 绑定、boundaries、trigger_keywords |
| Agent 分工 | 8 Agent = project/requirement/test-design/automation/execution/bug-analysis/report/knowledge | **Role-Based Agent Architecture** | 按测试工程中的专业角色分工，非按技术能力分工 |
| Agent 间通信 | Agent A 写入 context/ → Agent B 读取 context/ | **Document-Based Agent Communication** | 通过结构化文档传递状态，非共享内存或消息队列 |
| LLMProvider | `aitest/llm/provider.py` | **Model Abstraction Layer** | 统一 Claude/OpenAI/Ollama 调用接口。工厂模式 get_provider() |
| 模型能力兼容检查 | `skill_registry.py:246-326` | **Model-Aware Skill Routing** | 执行前检查 Provider+Model 是否满足 Skill 的能力要求 |

**掌握程度**: 🟢 **深度掌握**。实现了自主 Agent 循环（ReAct）、混合规划器（规则+LLM）、Agent 间文档通信、模型抽象层。

---

### ④ Orchestration Engineering（编排工程）

> **AI 工程定义**: 管理多个 Agent/Workflow 的执行顺序、条件分支、并行、状态传递。提供断点续跑和状态持久化。

| 项目组件 | 文件位置 | AI 工程概念 | 说明 |
|---------|---------|-----------|------|
| sop_graph.py | `aitest/graphs/sop_graph.py` | **Supervisor Graph (顶层编排)** | 11 节点 StateGraph。entry→preflight→条件路由→8 Agent→exit |
| bug_analysis_graph.py | `aitest/graphs/bug_analysis_graph.py` | **Cyclic SubGraph (循环子图)** | 7 节点：analyze→fix→approve→verify→(loop/report) |
| execution_graph.py | `aitest/graphs/execution_graph.py` | **Linear SubGraph × 3** | execution(4节点)/report(3节点)/knowledge(3节点) |
| route_next_phase | `sop_graph.py:347-392` | **Conditional Router** | 条件路由函数：检查 fatal_error/mode/completed_phases/execution_failed → 返回下一个节点 |
| loop_router | `bug_analysis_graph.py:269-301` | **Loop Controller** | 循环退出条件：修复通过/人拒绝/达到上限→退出；否则→继续 |
| make_agent_loop_node | `aitest/graphs/nodes.py:25-113` | **Agent as Graph Node** | 将 AgentLoop 封装为 LangGraph 节点。Agent 内部状态→AgentResult 封装→Phase 完成/失败标志 |
| SubGraph 组合 | `sop_graph.py:430-441` | **SubGraph Composition** | 编译后的子图作为父图节点。LangGraph 自动处理状态传递 |
| SOPState | `aitest/graphs/state.py:194-249` | **Orchestration State** | 共享 TypedDict。Annotated[List, operator.add] 实现多节点累积 |
| CANONICAL_PHASES | `state.py:126-135` | **Phase State Machine** | 定义合法的 Phase 顺序和状态转移规则 |
| MODE_SKIP_MAP | `state.py:138-145` | **Skip Logic** | 不同 mode 下跳过的 Phase 集合 |

**掌握程度**: 🟢 **深度掌握**。LangGraph 全栈使用：StateGraph + SubGraph + ConditionalEdge + Checkpoint + interrupt。是本项目第二大突出的 AI 工程能力。

---

### ⑤ Memory Architecture（记忆架构）

> **AI 工程定义**: 为 Agent 系统设计多层记忆——短期（单次执行）、中期（跨步骤）、长期（跨会话）、语义（知识检索）。

| 项目组件 | 文件位置 | AI 工程概念 | 说明 |
|---------|---------|-----------|------|
| SOPState (in-memory) | `aitest/graphs/state.py` | **Short-Term Memory (Working Memory)** | 单次 SOP 执行的完整状态。随图执行流转，节点间共享 |
| AgentLoop.memory dict | `aitest/agent_runner.py:298` | **Medium-Term Memory (Episodic)** | 单个 Agent 执行内的步骤间记忆：prev_output、tech_analysis_summary、retry_adjustments |
| SqliteSaver | `aitest/graphs/checkpoint.py` | **Long-Term Memory (Persistent)** | LangGraph Checkpoint。每次节点执行后自动持久化完整 State 到 SQLite |
| ChromaDB (5 集合) | `aitest/rag_engine.py` | **Semantic Memory (Vector Store)** | 235 文档的向量索引：known_issues(16)、project_context(12)、tech_analysis(72)、page_context(102)、page_objects(33) |
| CURRENT_TASK.md | `context/.../CURRENT_TASK.md` | **Session Memory (Explicit)** | 显式的跨会话记忆——"上次做到哪了、下一步做什么、需要什么文件" |
| known-issues.yaml | `governance/context/known-issues.yaml` | **Knowledge Base (Symbolic)** | 结构化符号记忆：EP/FP/ENV 分类、occurrence_count、solution |

**掌握程度**: 🟢 **深度掌握**。四层记忆架构：短期(in-memory State)→中期(AgentLoop.memory)→长期(SqliteSaver)→语义(ChromaDB RAG)。这是 AI 工程中记忆架构的完整实现。

---

### ⑥ RAG Architecture（检索增强生成）

> **AI 工程定义**: 将外部知识通过向量检索注入 LLM 上下文。包括索引管线、分块策略、检索接口、结果重排序。

| 项目组件 | 文件位置 | AI 工程概念 | 说明 |
|---------|---------|-----------|------|
| ChromaDB | `aitest/rag_engine.py` | **Vector Database** | 本地持久化向量库。5 个 Collection 按数据域隔离 |
| chunk_markdown_by_headings | `rag_engine.py:31-54` | **Chunking Strategy** | 按 ## 标题分割 Markdown，带元数据标注（module/page/heading） |
| search_known_issues | `rag_engine.py` | **Domain-Specific Retrieval** | 已知问题库专用检索接口。bug-analysis 的 L0 步骤 |
| search_context | `rag_engine.py` | **Cross-Domain Retrieval** | 跨 Collection 检索。支持跨模块技术分析、跨模块页面模式匹配 |
| RAG 在 bug-analysis 中的使用 | `bug_analysis_graph.py:60-95` | **RAG-Augmented Agent** | Bug 分析时 3×RAG 检索：本模块已知问题 + 跨模块技术分析 + 跨模块页面模式 |
| RAG 在 context_injector 中的使用 | `context_injector.py:156-178` | **RAG as Context Provider** | Skill 执行前按 query 检索相关上下文片段（非全文） |
| 索引自动更新 | `execution_graph.py:189-199` | **Incremental Indexing** | Knowledge Agent 结束时自动重新索引 known_issues/tech_analysis/page_context |

**掌握程度**: 🟢 **深度掌握**。实现了完整 RAG 管线：分块→索引→多域检索→跨域匹配→增量更新→Agent 内集成。

---

### ⑦ Tool / MCP Engineering（工具/MCP 工程）

> **AI 工程定义**: 为 Agent 提供调用外部工具的能力。MCP (Model Context Protocol) 是 Anthropic 提出的标准化工具协议。

| 项目组件 | 文件位置 | AI 工程概念 | 说明 |
|---------|---------|-----------|------|
| aitest-tools MCP Server | `aitest/mcp_server.py` | **MCP Server (Tools)** | 5 个 Tool：check_code_quality、rag_search_known_issues、get_module_status、run_pytest、run_sop_graph |
| aitest-knowledge MCP Server | `aitest/knowledge_server.py` | **MCP Server (Resources)** | 分层资源暴露：project://、module://、page://、known-issues:// |
| mcp.types.Tool | `mcp_server.py` | **Tool Definition** | 符合 MCP 协议的工具定义（name + description + inputSchema） |
| mcp.types.Resource | `knowledge_server.py` | **Resource Definition** | 符合 MCP 协议的资源定义。按需加载，避免全量传输 |
| stdio transport | 两个 MCP Server 均使用 | **MCP Transport** | 基于 stdin/stdout 的标准 MCP 传输层 |
| mechanimal Skill (code-consistency-checker) | `agent_runner.py:864-911` | **Zero-LLM Tool** | 本地 grep 脚本作为 "工具"——MCP Tool 的前身 |

**掌握程度**: 🟡 **良好掌握**。双 MCP Server（Tools + Resources）+ 标准 stdio transport。但 Tool 数量偏少（5+分层资源），且未使用 MCP 的 streaming/sampling 等高级特性。

---

### ⑧ Guardrails & Safety（护栏与安全）

> **AI 工程定义**: 为 Agent 系统设置安全边界——输入校验、输出验证、执行前审批、约束执行。

| 项目组件 | 文件位置 | AI 工程概念 | 说明 |
|---------|---------|-----------|------|
| SOP 三层门禁 | `sop-gate.template.md` + `sop_graph.py` | **Multi-Layer Gate System** | L1(编排器 Phase 前后检查)、L2(Agent 启动前置条件检查)、L3(Python 脚本校验) |
| Agent boundaries | `agent-definitions.yaml` 每个 Agent 的 boundaries 字段 | **Agent Guardrails (Declarative)** | 否定规则："不执行测试"、"不生成代码"、"不分析 Bug"——定义 Agent 不能做什么 |
| 8 条代码红线 | `CLAUDE.md` + `coding-standards.md` + `code-consistency-checker.md` | **Output Validation** | 代码生成后的机械化检查：继承 BasePage、禁止绝对 XPath、禁止 time.sleep、禁止 print |
| code-consistency-checker mechanical 模式 | `agent_runner.py:864-911` | **Deterministic Validator** | 生成后自检内置在 page-object-generator 和 test-script-generator 的 Prompt 模板中 |
| check_provider_compatibility | `skill_registry.py:246-326` | **Capability Gate** | 执行前检查 Provider+Model 是否满足 Skill 的最低能力要求 |
| knowledge-agent 唯一写入原则 | `agent-definitions.yaml:248-249` | **Write Gate (Single Writer)** | 只有 Knowledge Agent 能写入知识库。防止多 Agent 并发写入导致冲突 |

**掌握程度**: 🟢 **深度掌握**。三层门禁 + 声明式边界 + 红线自动检查 + 唯一写入原则——这是 AI 安全工程的完整实践。

---

### ⑨ Evaluation & Observability（评估与可观测性）

> **AI 工程定义**: 追踪 Agent 行为、评估输出质量、对比实验效果。包括 tracing、logging、metrics、eval harness。

| 项目组件 | 文件位置 | AI 工程概念 | 说明 |
|---------|---------|-----------|------|
| SkillObservation | `aitest/agent_runner.py:267-279` | **Step-Level Evaluation** | 每个 Skill 执行后的结构化观察结果：status(pass/fail/partial)、artifacts_found/missing、quality_issues、suggestion |
| code-consistency-checker review 模式 | `skills/automation/code-consistency-checker.md` | **LLM-as-Judge** | 对抗性代码审查——LLM 深度审查定位器稳定性、等待策略、断言充分性 |
| completeness-check | `skills/knowledge/completeness-check.md` | **Artifact Completeness Evaluation** | 按 SOP Phase 标准检查文档完整性（P0/P1/P2 优先级） |
| allure-report-analyzer | `skills/execution/allure-report-analyzer.md` | **Test Result Evaluation** | Allure JSON→结构化摘要。通过率、失败分布、趋势对比、不稳定用例检测 |
| artifact_map + preflight | `sop_graph.py:90-265` | **Pre-execution Evaluation** | 启动前扫描已有产物，评估完成度，推荐最优 mode |
| LangSmith 集成（声明） | `CLAUDE.md` 中 `LANGCHAIN_TRACING_V2=true` | **Tracing (Partial)** | 声明了 LangSmith 可观测性，但未见深度集成代码 |
| error_logger | `aitest/error_logger.py` | **Error Logging** | 结构化错误日志（被多个模块引用） |
| EventBus | `aitest/event_bus.py` | **Event Tracking** | AgentCompleted/BugClosed/CycleEnd/ContextUpdated 事件记录 |

**掌握程度**: 🟡 **基本掌握**。有步骤级评估（SkillObservation）、代码级评估（code-consistency-checker）、完整性评估（completeness-check）。但缺少：
- ❌ 系统性 Agent 评估框架（如 AgentEval、LangSmith eval）
- ❌ A/B 测试不同 Prompt 模板的效果
- ❌ 全链路 tracing（单个 Skill 的 token/progress 追踪不够系统化）
- ❌ 回归测试（修改 Skill Prompt 后自动验证效果不退化）

---

### ⑩ Human-in-the-Loop（人机协作）

> **AI 工程定义**: 在 Agent 自主执行流程中插入人工决策点。人在循环内部审批/修正，而非外部事后检查。

| 项目组件 | 文件位置 | AI 工程概念 | 说明 |
|---------|---------|-----------|------|
| request_approval_node | `bug_analysis_graph.py:188-216` | **HITL Interrupt** | LangGraph interrupt() 挂起执行，等待人工审批修复方案 |
| interrupt 携带的上下文 | `bug_analysis_graph.py:201-209` | **HITL Context** | cycle、module、analysis_summary、fix_summary、options |
| HITL 在循环内部 | `bug_analysis_graph.py:373-380` | **In-Loop HITL** | 审批后进入 verify 节点。reject→退出、approve→验证、验证失败→重新分析 |
| L2 门禁阻断提示 | `sop-gate.template.md:19-28` | **Human-Actionable Gate Message** | "⛔ 缺失 PAGE_CONTEXT.md → 先执行 /test-design-agent" — 告诉人该做什么 |
| doc 可 review | 所有 Agent 产出是 .md 文件 | **Human-Reviewable Artifacts** | Agent 间通过文档传递状态的核心原因之一——人可以在 Agent 间插入修改 |

**掌握程度**: 🟡 **良好掌握**。HITL 设计质量很高（循环内+上下文完整+LangGraph 原生支持）。但只有一个 HITL 点（Bug 修复审批）。可以扩展的点：
- 自动化策略审批（AUTO_STRATEGY.md—>人 review—>再生成代码）
- 测试用例审批（重要模块的 P0 用例需要人确认）

---

## 2. 能力雷达图

```
                    Context Engineering
                          ██████
                          ██████ 🟢 深度
                          ██████
     Human-in-the-Loop  ██      ██  Prompt/Capability Eng.
                   🟡  ██        ██ 🟢 深度
                       ██          ██
                       ██          ██
   Eval/Observability  ██          ██  Agent Engineering
                 🟡    ██          ██ 🟢 深度
                       ██          ██
                       ██          ██
      Guardrails/Safety ██        ██  Orchestration Eng.
                   🟢  ██        ██ 🟢 深度
                       ██      ██
                    🟢 ██    ██ 🟢 深度
                     ██████████
                  Memory    RAG Architecture
```

**7 个领域深度掌握（🟢），3 个领域良好/基本掌握（🟡），0 个领域缺失（🔴）**。

---

## 3. 缺少的 AI 工程能力

这些都是 "再往前走一步" 的方向：

### 缺失 1: 系统化 Agent 评估 (Agent Evaluation Framework)

**现状**: SkillObservation 提供步骤级评估，code-consistency-checker 提供代码级评估。但都是通过/失败的二元判断。

**缺失**: 
- 没有 "这个 Agent 的执行质量评分是多少？"
- 没有 "修改了 page-analysis Skill 的 Prompt，效果变好了还是变差了？"
- 没有回归测试集（golden test set）来评估 Skill 变更的影响

**主流方案**: LangSmith Eval、Braintrust、自定义 eval harness

---

### 缺失 2: 全链路可观测性 (End-to-End Observability)

**现状**: 有 error_logger（错误日志）、EventBus（事件记录）、SkillObservation（步骤观察）。提到了 LangSmith 但未深度集成。

**缺失**:
- 没有单个 SOP 执行的完整 trace（每个 Skill 的输入/输出/token/耗时）
- 没有 Agent 级别的性能 dashboard
- 没有 "这个模块的 SOP 执行了多久？哪个 Phase 最慢？"

**主流方案**: LangSmith、LangFuse、Phoenix (Arize)

---

### 缺失 3: A2A (Agent-to-Agent) 通信协议

**现状**: Agent 通过文件系统（Markdown 文档）通信。

**缺失**:
- 没有实时的 Agent 间通信（Agent A 执行完可以主动通知 Agent B）
- 没有标准化的 Agent 发现机制（Agent B 如何知道 Agent A 已经完成了？目前靠文档存在性检查）

**注意**: 对于当前项目，文档通信是**正确选择**（因为需要人类可 review 和断点续跑）。但作为学习方向，A2A 协议值得了解。

**主流方案**: Google A2A、OpenAI Agents SDK 的 handoff

---

### 缺失 4: Prompt 版本管理与 A/B 测试

**现状**: Skill .md 文件在 git 中版本化。但没有 Prompt 的正式版本号或 A/B 测试框架。

**缺失**:
- Skill v1.0 vs v2.0 的效果对比
- "新的 Prompt 模板生成的代码更规范吗？"
- 回滚机制（发现新 Prompt 效果变差时快速回退）

**主流方案**: LangSmith Hub、自定义 registry + eval

---

### 缺失 5: 多模态集成

**现状**: page-analysis 支持基于截图分析（上传截图到 LLM）。但这是通过 Prompt 中的 "上传截图" 指令手动完成的。

**缺失**:
- 自动化截图采集（Selenium screenshot → 自动送入 page-analysis）
- 基于截图的定位器验证（"这个定位器真的指到了截图中的这个元素吗？"）

**主流方案**: Claude Vision API、GPT-4V、Selenium 自动截图

---

### 缺失 6: Agent 沙箱执行

**现状**: code-consistency-checker 是唯一的 "代码执行" Skill（grep 扫描，零风险）。生成的代码（Page Object + test）不在此 Agent 系统中执行。

**缺失**:
- 生成的代码的隔离执行环境
- "这段生成的 Page Object 代码真的能跑吗？"（语法检查 + 导入检查）

**主流方案**: Docker sandbox、E2B、自定义 subprocess 隔离

---

## 4. 主流技术栈映射

### LangGraph → 🟢 核心依赖

| 能力 | 本项目使用程度 |
|------|:----------:|
| StateGraph | ✅ 顶层编排图 + 3 个子图 |
| TypedDict State + Reducer | ✅ Annotated[List, operator.add] |
| ConditionalEdge | ✅ 3 个路由函数 |
| Checkpoint (SqliteSaver) | ✅ 断点续跑 + 时间旅行 |
| SubGraph (compiled graph as node) | ✅ 4 个子图组合 |
| interrupt() + Command(resume) | ✅ HITL 审批节点 |
| Node Factory (make_agent_loop_node) | ✅ 自定义封装 |
| Streaming | ⚠️ 在 CLI 中使用但未深度集成 |

---

### LangChain → 🟡 间接使用

| 能力 | 本项目使用程度 |
|------|:----------:|
| LangSmith tracing | ⚠️ 声明了环境变量但未见深度集成代码 |
| LangChain 的 Chain/Agent | ❌ 未使用。本项目选择 LangGraph（更底层）而非 LangChain 高级封装 |

**决策理由**: LangGraph 比 LangChain 的 AgentExecutor 提供更细粒度的控制（自定义节点+条件路由+状态机），更适合本项目的 Supervisor 编排需求。

---

### MCP (Model Context Protocol) → 🟢 双 Server

| 能力 | 本项目使用程度 |
|------|:----------:|
| MCP Server (Tools) | ✅ aitest-tools: 5 个 Tool |
| MCP Server (Resources) | ✅ aitest-knowledge: 分层资源 URI |
| MCP Transport (stdio) | ✅ 标准实现 |
| MCP Client | ❌ 本项目 MCP Server 用于被外部 Client 调用，自身不作为 Client |

---

### OpenAI Agent SDK → 🔴 未使用

| 能力 | 对比本项目 |
|------|-----------|
| Agent 定义 | Agent SDK: Python decorator；本项目: agent-definitions.yaml |
| Handoff (Agent 间切换) | Agent SDK: 内置 handoff 机制；本项目: LangGraph 条件路由 |
| Guardrails | Agent SDK: 内置 input/output guardrails；本项目: 自建三层门禁 |

**为什么不使用**: 本项目在 Agent SDK 发布前就已建立。Agent SDK 的 handoff 机制适合对话式 Agent，本项目的 Phase 流水线式编排更适合 LangGraph 的图引擎。

---

### CrewAI → 🔴 未使用

| 能力 | 对比本项目 |
|------|-----------|
| Multi-Agent 通信 | CrewAI: Agent 间对话；本项目: 文档通信 |
| Task 定义 | CrewAI: Task + expected_output；本项目: Skill + 检查清单 |
| Process (sequential/hierarchical) | CrewAI: 内置；本项目: LangGraph 自定义路由 |

**为什么不使用**: CrewAI 的 Agent 间对话通信不适合测试工程场景（对话不可审计、不支持断点续跑）。本项目的文档通信更符合测试工程的特点。

---

### AutoGen → 🔴 未使用

| 能力 | 对比本项目 |
|------|-----------|
| Agent 间对话 | AutoGen: 对话驱动；本项目: 文档驱动 |
| GroupChat | AutoGen: 多 Agent 群聊；本项目: Supervisor 模式 |
| Code Executor | AutoGen: 内置代码执行器；本项目: subprocess 直接调用 pytest |

**为什么不使用**: 与 CrewAI 同理。对话式 Multi-Agent 不适合确定性的测试流水线。Supervisor+Router 模式比 GroupChat 更适合 Phase 顺序依赖的场景。

---

### Dify → 🔴 未使用

| 能力 | 对比本项目 |
|------|-----------|
| 工作流编排 | Dify: 可视化拖拽；本项目: Python 代码（LangGraph） |
| Prompt 管理 | Dify: Web UI；本项目: Markdown 文件 + Git 版本化 |
| RAG Pipeline | Dify: 可视化配置；本项目: Python ChromaDB 代码 |

**为什么不使用**: Dify 是面向非开发者的低代码平台。本项目是面向开发者的代码化 Agent 系统——灵活性 > 易用性。两者定位不同。

---

### A2A (Agent-to-Agent) → 🔴 未使用

| 能力 | 本项目替代方案 |
|------|--------------|
| Agent 发现 | 预定义的 Agent 注册表 (agent-definitions.yaml) |
| Agent 通信 | 文件系统（文档传递） |
| Agent 任务分派 | LangGraph Supervisor (route_next_phase) |

**为什么不使用**: A2A 协议还很新（Google 2025 年发布）。本项目的文档通信方式在测试工程场景下有自己的优势（人类可 review、断点续跑）。

---

### ChromaDB → 🟢 核心依赖

| 能力 | 本项目使用程度 |
|------|:----------:|
| 向量嵌入 | ✅ 使用内置 ONNX 模型 |
| 多 Collection | ✅ 5 个 Collection 按数据域隔离 |
| 元数据过滤 | ✅ 按 module/page 过滤 |
| 增量索引 | ✅ 每次 Knowledge Agent 结束后自动更新 |

---

## 5. 学习路线图

基于当前项目已掌握的能力，推荐如下学习路径：

```
当前位置: ★ (本项目位于此处)
学习方向: →
```

### 第一站: 巩固已掌握能力 (你在这里)

```
✅ 已完成:
  Context Engineering (三级分层 + 双通道注入)
  Prompt/Capability Engineering (24 Skill + 注册表 + 能力分级)
  Agent Engineering (ReAct Loop + 混合规划器 + 文档通信)
  Orchestration (LangGraph Supervisor + SubGraph + 条件路由)
  Memory (四层: 短期/中期/长期/语义)
  RAG (ChromaDB 5 集合 + 分块 + 增量索引)
  Guardrails (三层门禁 + 红线 + 唯一写入)
  HITL (循环内 interrupt)
```

**自查题**:
- 能不能向一个 AI 工程师解释清楚 ContextInjector 的设计？
- 能不能独立设计一个 3-Agent 的 Supervisor 图？
- 能不能解释为什么选文档通信而不是共享内存？

---

### 第二站: 可观测性提升

```
当前: SkillObservation + error_logger + EventBus
下一步 →
  ┌─ LangSmith / LangFuse 全链路 tracing
  ├─ 每个 Skill 的 token 消耗仪表盘
  ├─ Agent 执行耗时热力图
  └─ 失败模式统计分析
```

**学习资源**:
- LangSmith SDK: `langsmith` Python package
- LangFuse: 开源替代，自托管

**动手项目**: 给 AgentLoop.run() 加 tracing，记录每步 Perceive/Plan/Act/Observe/Update 的耗时和 token。

---

### 第三站: 系统性 Agent 评估

```
当前: SkillObservation (通过/失败二元) + code-consistency-checker
下一步 →
  ┌─ 建立 golden test set (预期输出 vs 实际输出)
  ├─ Skill Prompt A/B 测试框架
  ├─ Agent 执行质量评分 (不只是通过/失败)
  └─ 回归测试: "修改了 Prompt，生成质量下降了吗？"
```

**学习资源**:
- LangSmith Eval: 内置 eval harness
- Braintrust: AI 评估平台

**动手项目**: 为 page-object-generator Skill 建立一个评估集——5 个已知页面，记录 Prompt v1 和 v2 生成的代码质量差异。

---

### 第四站: Prompt 版本化与 CI/CD

```
当前: Skill .md 文件在 git 中
下一步 →
  ┌─ Skill 语义版本号 (major.minor)
  ├─ Prompt CI: "修改了 Skill → 自动跑 eval → 报告质量变化"
  ├─ Prompt 回滚机制
  └─ 多模型对比测试 (Claude vs GPT-4o vs DeepSeek)
```

**学习资源**:
- promptfoo: 开源的 Prompt 评估 CLI
- LangSmith Hub: Prompt 版本管理

**动手项目**: 用 promptfoo 对比 Claude Sonnet 和 GPT-4o 在 page-analysis Skill 上的效果。

---

### 第五站: 多模态 Agent

```
当前: page-analysis 依赖人工上传截图
下一步 →
  ┌─ Selenium 自动截图 → 自动送入 Vision LLM
  ├─ 截图 + HTML 源码 双通道页面分析
  └─ 视觉定位验证: "截图中的这个按钮，定位器指对了吗？"
```

**学习资源**:
- Claude Vision API (claude-sonnet-4-6 支持图片)
- GPT-4V API

**动手项目**: 扩展 page-analysis Skill，增加 "自动截图→视觉分析→定位器验证" 的流程。

---

### 第六站: 分布式 Agent

```
当前: 单进程 LangGraph 编排
下一步 →
  ┌─ Agent 间异步执行 (不同模块并行跑 SOP)
  ├─ Agent 服务化 (每个 Agent 独立进程/容器)
  ├─ A2A 协议用于 Agent 发现和通信
  └─ 消息队列驱动 (EventBus → Kafka/NATS)
```

**学习资源**:
- Google A2A Protocol
- Temporal.io (工作流引擎)
- Celery (分布式任务队列)

**动手项目**: 将 8 个 Agent 分别部署为独立 MCP Server，通过 A2A 协议通信。

---

## 6. 总结评价

### 本项目的 AI 工程水平

| 维度 | 评分 | 评语 |
|------|:---:|------|
| Context Engineering | ⭐⭐⭐⭐⭐ | 三级分层 + 双通道注入 + 生命周期管理。工业级。 |
| Prompt/Capability Engineering | ⭐⭐⭐⭐⭐ | 24 Skill + 注册表 + 分级 + 适配 + 生命周期。工业级。 |
| Agent Engineering | ⭐⭐⭐⭐⭐ | ReAct Loop + 混合规划器 + 文档通信 + 8 Agent 分工。工业级。 |
| Orchestration | ⭐⭐⭐⭐⭐ | LangGraph Supervisor + SubGraph + 条件路由 + Checkpoint。工业级。 |
| Memory | ⭐⭐⭐⭐⭐ | 四层记忆架构。业界少见的完整实现。 |
| RAG | ⭐⭐⭐⭐ | 5 集合 + 分块 + 增量索引。缺少重排序。 |
| Guardrails | ⭐⭐⭐⭐⭐ | 三层门禁 + 声明式边界 + 红线 + 唯一写入。工业级。 |
| HITL | ⭐⭐⭐⭐ | 循环内审批，设计正确。只有一个审批点。 |
| Tool/MCP | ⭐⭐⭐⭐ | 双 Server。Tool 数量偏少。 |
| Eval/Observability | ⭐⭐⭐ | 有基础但不够系统化。最大短板。 |

**综合**: 🟢 **AI 工程的高级实践者水平**。在 Context/Capability/Agent/Orchestration/Memory/Guardrails 六个领域达到工业级，在 Eval/Observability 领域有提升空间。

---

> **文档版本**: 2026-06-14 · 基于项目 v2.0 全栈 · 纯教学用途
