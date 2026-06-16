# AI自动化测试平台架构审计报告 v2

> **审计日期**: 2026-06-12
> **审计立场**: 批判性审查。目标基线——平台独立、真正 Agent、RAG 知识库
> **v1 反馈**: v1 的"废弃建议"忽略了去平台化和学习目标。v2 从正确基线重审。

---

## 摘要

项目处于一个**关键转折点**: 你建了两层架构——Claude Code 原生层（当前实际运行）和 aitest/ 平台独立层（基础设施完备但休眠）。两层之间的张力是当前所有架构问题的根源。

**一句话**: 平台层地基打得不错，但上面没盖房子。Claude Code 层房子已经住人了，但它盖在租来的地上。

---

## 一、总体评价（修正基线后）

| 维度 | 得分 | 评语 |
|------|------|------|
| 平台独立性设计 | 72 | 方向正确，LLM 抽象层/agent_runner/MCP 是对的 |
| Agent 真实性 | 25 | **硬伤。当前无真正 Agent，只有顺序 Skill 执行器** |
| 架构一致性 | 40 | 两层系统并行，定义分散在 3 处 |
| RAG 工程质量 | 55 | 骨架好，集成浅 |
| 代码工程质量 | 68 | aitest/ 代码规范，但测试覆盖 0 |

---

## 二、成熟度评级（修正基线后）

| 体系 | 级别 | 关键判断 |
|------|------|---------|
| Context 体系 | **L4** | SSoT + 按需加载 + PAGE_INTERFACE.yaml 方向正确 |
| Workflow 体系 | **L3** | YAML DAG 引擎本身质量好，但与执行层脱节 |
| Skill 体系 | **L3** | 分类和注册表合理，但 Skill 仍是"Prompt 模板"非"Agent 工具" |
| Agent 体系 | **L1** | **核心问题。有 Agent 之名，无 Agent 之实** |
| Knowledge 体系 | **L2** | RAG 索引管线完整，但 Agent 不自动使用 |
| LLM 抽象层 | **L3** | 3 Provider + Prompt 适配 + 能力检查，设计合理 |
| Tool 体系 | **L2** | MCP Server 8 tools，但本质是 CLI 包装器 |
| Platform 体系 | **L2** | 组件齐全但未集成 |

**总体: L2+ (52/100)**。平台地基 L3，Agent 实现 L1，拉低了整体。

---

## 三、核心架构问题（Part 2 重审）

### 问题一：双层架构——最严重的结构性缺陷

当前存在两套平行系统在做同一件事：

```
Layer A: Claude Code 原生层 (当前实际运行)
├── .claude/skills/<agent>/SKILL.md        ← Agent 定义 (System Prompt + 编排规则)
├── governance/agents/<agent>.md           ← Agent 文档
├── governance/agents/<agent>.workflow.js  ← Agent 实现 (Workflow 脚本)
└── governance/agents/full-sop.workflow.js ← 编排器

Layer B: 平台独立层 (aitest/) (基础设施完备但休眠)
├── aitest/agent_runner.py                 ← Agent 执行器 (AGENT_SKILL_MAP)
├── aitest/workflow_engine.py              ← YAML DAG 工作流引擎
├── aitest/agent_scheduler.py              ← 状态机调度器
├── aitest/event_bus.py                    ← 事件总线
├── aitest/llm/provider.py                 ← 3 Provider 统一接口
├── aitest/llm/skill_loader.py             ← Skill 加载器
├── aitest/llm/context_injector.py         ← 上下文注入 + RAG
├── aitest/llm/prompt_adapter.py           ← 跨模型 Prompt 适配
├── aitest/llm/skill_registry.py           ← Skill 能力分级矩阵
├── aitest/rag_engine.py                   ← ChromaDB 向量检索
└── aitest/mcp_server.py                   ← MCP 协议服务
```

**问题本质**: 同一个 Agent（如 automation-agent）的定义分散在：
1. `.claude/skills/automation-agent/SKILL.md` — 实际运行时的 System Prompt
2. `governance/agents/automation-agent.md` — 人类阅读的文档
3. `governance/agents/automation-agent.workflow.js` — Workflow 脚本
4. `aitest/agent_runner.py` `AGENT_SKILL_MAP` — 硬编码的 Skill 列表

四处定义在说同一件事：automation-agent 由哪些 Skill 组成、按什么顺序执行。

**风险**: 修改 Agent 行为需要同步 4 处。当前已经有不一致——`AGENT_SKILL_MAP` 里的 automation-agent 包含 `conftest-generator`，但 `.claude/skills/automation-agent/SKILL.md` 里的编排规则也包括它。但如果一方改了另一方没改，就会出现"平台层说能做，Claude Code 层实际不做"的诡异 bug。

### 问题二：Agent 不是 Agent——这是硬伤

**当前 `run_agent()` 的实现（agent_runner.py:248）:**

```python
for i, skill_id in enumerate(skills):  # 顺序 for 循环
    response = run_skill(skill_id, ...)
```

这就是一个 for 循环。它不包含任何 Agent 应有的能力：

| 真 Agent 能力 | 当前状态 | 缺失什么 |
|-------------|---------|---------|
| **感知** | ⚠️ 半有 | context_injector 注入上下文 + RAG 检索，但 Agent 不主动感知 |
| **规划** | ❌ 无 | Skill 顺序硬编码在 AGENT_SKILL_MAP 中。Agent 从不决定"下一步做什么" |
| **行动** | ✅ 有 | run_skill → LLM 调用，能执行工具 |
| **观察** | ❌ 无 | Skill 执行完后不验证产出质量。门禁检查在 workflow 层，不在 agent 层 |
| **重规划** | ❌ 无 | 如果 TECH_ANALYSIS 写错了定位器，page-object-generator 不会回头要求修正 |
| **状态** | ❌ 无 | 每次 run_agent 调用是无状态的。没有 Agent 记忆 |
| **协作** | ❌ 无 | event_bus 有，但 Agent 不订阅事件。knowledge-agent 在 SOP 末尾被手动调用 |

**结论**: 当前的 8 个 Agent 是 **Skill 编排脚本** + **角色化 System Prompt**。它们不是 Agent。

### 问题三：平台层与执行层脱节

这是三个具体的脱节：

1. **workflow_engine.py 不被 workflow 使用**: 503 行代码实现了 YAML 解析、拓扑排序、checkpoint/resume。但 full-sop.workflow.js 用 Claude Code Workflow 工具独立实现了同样的功能。workflow_engine 从未被调度过实际任务。

2. **agent_scheduler.py 不被 agent 使用**: 397 行代码实现了状态机和前置条件检查。但它的输出是 "建议下一个 Agent 是 X"，然后由人类或 full-sop 编排器去调用。真正的 Agent 应该自己调用 scheduler 来决定下一步。

3. **event_bus.py 没有订阅者**: 4 种事件类型定义了。但 knowledge-agent 不是在监听的——它是在 full-sop 末尾被显式调用的。`emit("AgentCompleted", ...)` 发出去了，但没有任何进程在 `listen()`。

---

## 四、真正有价值的建设（重新评估）

### 高价值 ✅

| # | 建设 | 理由 |
|---|------|------|
| 1 | **aitest/llm/provider.py** | 3 Provider 统一接口是去平台化的核心。没有这个，所有上层逻辑都绑定 Claude |
| 2 | **Context 按需加载策略** | 从 4500 tokens 降到 900 tokens，节省 80%。真实 ROI |
| 3 | **SKILL_CONTEXT_MAP + context_injector** | 每个 Skill 声明自己需要什么上下文，RAG 自动检索。这是 Agent 感知能力的基础 |
| 4 | **skill_registry 能力分级矩阵** | Provider 能力检查 + Skill 最低要求。切换到 Ollama 时自动降级提示——这是多模型支持的必要组件 |
| 5 | **prompt_adapter** | Claude→OpenAI→Ollama 的 Prompt 格式适配。XML tag 剥离、few-shot 注入。去平台化必需 |
| 6 | **PAGE_INTERFACE.yaml** | Agent 间结构化数据传递替代通读 Markdown。正确方向 |
| 7 | **workflow_engine 的 checkpoint/resume** | 拓扑排序 + 断点续跑的设计正确，只是需要和实际执行层对接 |

### 需要重构 ⚠️

| # | 建设 | 问题 | 建议 |
|---|------|------|------|
| 1 | **双层 Agent 定义** | 同一个 Agent 的定义在 4 处 | 以 aitest/agent_runner.py 的 AGENT_SKILL_MAP 为单一事实源。.claude/skills/ 的 SKILL.md 从它自动生成 |
| 2 | **agent_runner.run_agent()** | for 循环不是 Agent | 改为 Agent 执行循环：plan → execute skill → observe → replan |
| 3 | **full-sop.workflow.js 与 workflow_engine 双轨** | 两份编排逻辑 | full-sop.workflow.js 改为调用 workflow_engine 的 thin wrapper |
| 4 | **MCP Server tools 6-8** | 返回的是 "建议你在 AI 客户端执行 /xxx 命令"，不是真正执行 | MCP tool 应该直接调用 agent_runner.run_agent() |

---

## 五、Skill 体系评估（Part 3 重审）

原 v1 建议废弃 5 个 Skill。在"平台独立 + 真正 Agent"目标下，重新评估：

### 保留 + 提升 ✅

| Skill | 角色 | 提升方向 |
|-------|------|---------|
| tech-analysis | Agent 核心 Skill | 需要 tool calling——应能主动读取 HTML/DOM |
| page-analysis | Agent 核心 Skill | 同上 |
| testcase-design | Agent 核心 Skill | 需要消费结构化 PAGE_INTERFACE.yaml |
| page-object-generator | Agent 核心 Skill | 需要消费 TECH_ANALYSIS + 自我合规检查 |
| test-script-generator | Agent 核心 Skill | 需要消费 TEST_CASES + AUTO_STRATEGY |
| code-consistency-checker | 机械化检查 | 当前实现正确（不消耗 LLM Token） |
| bug-analysis | Agent 核心 Skill | RAG 自动检索应集成到此 Skill 的 context_injector |
| knowledge-manager | Agent 核心 Skill | 应成为 event_bus 的订阅者，而非被动调用 |
| report-generator | Agent 核心 Skill | OK |

### 可以合并的 🔀

| 合并 | 理由 |
|------|------|
| module-modeling + requirement-analysis → `module-onboarding` | 同一 Agent 内总是顺序调用。合并减少 context 切换 |
| auto-strategy + tech-analysis → `automation-analysis` | 实践中是同一篇文档的上下半场 |
| conftest-generator → 合并到 test-script-generator | conftest.py 是一次性产物，不需要独立 Skill |
| ci-pipeline-analysis → 合并到 bug-analysis | CI 日志是 Bug 分析的输入源之一，非独立维度 |

### 不建议急于废弃的

v1 建议废弃的 `test-data-generation`, `jenkinsfile-generator`, `api-testing`, `miniapp-testing` 在当前 Skill 数量下不构成维护负担。如果未来 3 个月确实不使用，再归档。**当前优先修复架构问题，Skill 数量不是瓶颈。**

---

## 六、Agent 真实能力评估（Part 4 重审）

### 严格定义

一个真正的 AI Agent 必须满足：
1. **自主感知**: 主动获取环境信息（读文件、RAG 检索、执行工具）
2. **目标导向规划**: 根据目标自主决定下一步动作（选哪个 Skill？按什么顺序？）
3. **执行与观察闭环**: 执行后检查结果、判断是否成功、失败时自我修正
4. **状态管理**: 跨步骤维护内部状态（已完成什么、当前进度、已知信息）
5. **Agent 间协作**: 通过消息/事件与其他 Agent 通信

### 当前 8 个 Agent 的评分

| Agent | 感知 | 规划 | 执行 | 观察 | 状态 | 协作 | 总分 | 判定 |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|------|
| project-agent | 2 | 0 | 3 | 1 | 0 | 0 | 6/30 | 伪 Agent |
| requirement-agent | 2 | 0 | 3 | 0 | 0 | 0 | 5/30 | 伪 Agent |
| test-design-agent | 3 | 0 | 3 | 1 | 0 | 0 | 7/30 | 伪 Agent |
| automation-agent | 3 | 0 | 4 | 2 | 0 | 0 | 9/30 | 伪 Agent |
| execution-agent | 2 | 0 | 3 | 1 | 0 | 0 | 6/30 | 伪 Agent |
| bug-analysis-agent | 3 | 0 | 3 | 1 | 0 | 0 | 7/30 | 伪 Agent |
| report-agent | 2 | 0 | 3 | 1 | 0 | 0 | 6/30 | 伪 Agent |
| knowledge-agent | 2 | 0 | 3 | 1 | 1 | 0 | 7/30 | 半 Agent |

> 注: 感知 3 分 = context_injector + RAG 自动检索已工作。knowledge-agent 状态 1 分 = 能去重检查已有 known_issues。

### 核心诊断

**不是 Agent 太少，是 8 个 Agent 没有任何一个具有 Agent 循环。** 每个 Agent 本质上是一个带角色设定的 `for skill in skills: run_skill(skill)`。

这不是说 8 个 Agent 的概念错了。概念（项目分析→需求→测试设计→自动化→执行→诊断→报告→知识）是正确的领域分解。**问题在于实现——Agent 的执行体不是一个自主循环，而是一个固定顺序的 Skill 执行脚本。**

---

## 七、知识库与 RAG 评估（Part 5 重审）

### 投入成本

| 组件 | 成本 |
|------|------|
| ChromaDB | pip install，零运维 |
| embedding 模型 | ChromaDB 内置 ONNX（sentence-transformers 可选），~100MB |
| 索引管线 | `rag_engine.py` 已实现 Markdown 分块 + YAML 结构化索引 |
| 检索接口 | `rag_engine.search_context()` 已实现 |

投入不高。当前是可接受的学习成本。

### 当前工程质量

**做得好的**:
- 5 个 Collection 分类合理（known_issues / project_context / tech_analysis / page_context / page_objects）
- Markdown 按 `##` 标题分块的策略适合文档检索
- context_injector 的 `SKILL_CONTEXT_MAP` 设计——每个 Skill 声明自己需要什么 RAG 查询——这是正确的 Agent 上下文注入模式

**需要改进的**:

1. **索引不是自动的**。`context_injector._resolve_rag()` 每次调用时实时检索，但索引重建是手动的。`PROJECT_CONTEXT.md` 更新后，`project_context` collection 不会自动重建。Agent 可能基于过期的上下文做决策。

2. **检索没有被 Agent 主动使用**。当前 RAG 检索发生在 `context_injector.inject()` 里——这是"系统在 Agent 启动时被动注入"。一个真正的 Agent 应该在执行过程中主动发起 RAG 查询："这个 el-cascader 的错误模式我之前见过吗？"

3. **235 docs 规模下的语义检索收益不大，但这不是问题**。你是在为 2350 docs 的规模建基础设施。方向正确。

### 结论

**保留并深化 RAG。** 不是废弃它，而是让 Agent 真正使用它——RAG 应该从"被动注入"变成"Agent 主动查询"。

---

## 八、Token 成本评估（Part 6 重审）

### 当前每次 Agent 调用的 Token 构成（通过 agent_runner）

| 阶段 | Token |
|------|-------|
| Skill Prompt 加载 | 500-2,000 |
| Context 注入（RAG + 文件） | 300-3,000 |
| Prompt 适配 | 0（纯变换） |
| LLM 调用 (input) | 2,000-8,000 |
| LLM 调用 (output) | 1,000-4,000 |
| **单 Skill 合计** | **~4,000-17,000** |

一个 automation-agent 执行 6 个 Skill：~24,000-102,000 tokens

### 真正的优化方向

不是减少 Skill 数量（那是用减少功能来省 Token）。而是：

1. **PAGE_INTERFACE.yaml 全覆盖**: 当前只有 1 个示例。如果一个页面有 PAGE_INTERFACE.yaml，automation-agent 的 tech-analysis 不需要通读 PAGE_CONTEXT.md 全量——节省 ~2,000 tokens per page。如果 10 个模块 × 平均 4 页 = 40 个页面，每次全 SOP 节省 ~80,000 tokens。

2. **Agent 间传递结构化数据**: 当前上游 Agent 输出 Markdown，下游 Agent 重新通读。改为上游输出 JSON/YAML schema + 摘要，下游只消费结构化数据——每个传递环节节省 ~3,000 tokens。

3. **按 Agent 状态分级加载**: 如果 Agent 有状态（知道自己上次做到哪了），可以只加载增量上下文而非全量。这是"真 Agent"带来的 Token 节省——不是靠削减功能，而是靠智能感知。

---

## 九、单人维护性评估（Part 7 重审）

### 真实维护负担

| 负担 | 严重程度 | 说明 |
|------|---------|------|
| 双层 Agent 定义同步 | 🔴 高 | 改一个 Agent 行为要改 2-4 个文件 |
| aitest/ 代码零测试 | 🟡 中 | ~2,500 行 Python，0 个 test_*.py。重构时无安全网 |
| Context 文档版本漂移 | 🟡 中 | 100+ context 文件，无过期检测 |
| 废弃文件积累 | 🟢 低 | _deprecated/ 归档干净，目前管理良好 |

### 最大风险

**单人维护下，双层架构是最危险的。** 当你 3 个月后回来继续开发，你会面对两层系统——一层是 Claude Code Skills（当时 work 的），一层是 aitest/（当时在建的）。你会不确定应该在哪一层改东西。

---

## 十、企业落地评估（Part 8 重审）

### 如果推广到团队

**可以直接推广**:
- Context 事实源体系（SSoT + 模块隔离）
- 8 条代码红线 + grep 自检
- BasePage 封装
- known-issues.yaml 模式

**可以推广但需要 MCP Server 包装**:
- Skill Prompt 库——通过 MCP 协议暴露给各 AI 客户端
- PAGE_INTERFACE.yaml 结构化接口

**团队场景下平台层的价值才真正体现**:
- 多 LLM Provider 支持——不同成员用不同的模型
- MCP Server——统一的工具入口
- 事件总线——多人协作时需要事件通知
- Agent 状态管理——避免多人对同一模块重复执行

**当前缺失**:
- Agent 执行结果持久化（谁在什么时间对哪个模块做了什么）
- Agent 间冲突检测（两个人同时对同一模块跑 SOP）

---

## 十一、路线图审计（Part 9 重审）

在"平台独立 + 真 Agent"目标下，当前建设顺序的问题：

### 建设顺序正确的地方 ✅
1. LLM 抽象层 → Agent Runner → MCP Server 的顺序是对的（先有统一接口，再包装协议）
2. RAG 在 context_injector 之前建设是对的（RAG 是 context_injector 的依赖）
3. skill_registry 的能力分级矩阵在 prompt_adapter 之前建设是对的

### 建设顺序的问题 ⚠️

1. **workflow_engine 和 agent_scheduler 建在了 agent_runner 不具备 Agent 循环之前。** 这两个模块是"多 Agent 编排"的基础设施。但在单个 Agent 都不具备自主循环的情况下，多 Agent 编排是空中楼阁。**应该先让一个 Agent 真正工作，再谈编排。**

2. **event_bus 建在了没有订阅者之前。** 事件驱动架构的前提是有活跃的订阅者。当前最自然的订阅者是 knowledge-agent（监听 AgentCompleted → 自动沉淀），但 knowledge-agent 本身还是被动调用的。**先把 knowledge-agent 变成真正的事件订阅者，event_bus 才有意义。**

3. **MCP Server 的 8 个 tool 有 3 个（run_test_design_agent, run_automation_agent, run_full_sop）只返回"请在 AI 客户端执行 /xxx 命令"。** 这说明 agent_runner 和 MCP Server 没有集成——MCP tool 应该能直接调用 agent_runner.run_agent()。**先把 agent_runner 变成 MCP tool 的真正后端，再暴露更多 tool。**

---

## 十二、核心建议：从伪 Agent 到真 Agent 的路径

### 第一步：让一个 Agent 真正工作

选择一个 Agent（建议 automation-agent，因为它有最明确的输入输出：PAGE_INTERFACE.yaml → PageObject.py）作为"真 Agent 原型"。

当前实现：
```python
# agent_runner.py — 伪 Agent
for skill in skills:            # 固定顺序
    response = run_skill(...)    # 执行
    # 不检查产出质量
    # 不决定下一步
```

目标实现：
```python
# 真 Agent 循环
state = AgentState(goal=..., context=..., memory=...)
while not state.goal_achieved and state.steps < max_steps:
    # 1. 感知: 读取当前上下文 + RAG 检索相关信息
    perception = await self.perceive(state)
    
    # 2. 规划: 自主决定下一步（选哪个 Skill？需要什么输入？）
    next_action = await self.plan(state, perception)  
    
    # 3. 执行: 执行选定的 Skill
    result = await self.act(next_action)
    
    # 4. 观察: 验证产出质量
    observation = await self.observe(result)
    
    # 5. 更新状态
    state.update(next_action, result, observation)
    
    # 6. 如果需要协作: 发射事件
    if observation.milestone_reached:
        event_bus.emit("SkillCompleted", ...)
```

### 第二步：激活 knowledge-agent 为事件订阅者

knowledge-agent 应该是平台上**唯一持续运行的 Agent**。它订阅 event_bus 的事件：
- `AgentCompleted` → 检查产出中是否有可沉淀的知识
- `BugClosed` → 更新已知问题库
- `CycleEnd` → 执行批量知识沉淀

这不需要复杂的后台进程。aiest 可以通过 cron 或 loop 定期执行：
```bash
python -m aitest.event_bus process  # 每 5 分钟处理积压事件
```

### 第三步：workflow_engine 对接 agent_runner

workflow_engine 当前只做 DAG 解析。它应该成为 Agent 的执行调度器：
```python
engine = WorkflowRunner(workflow_def)
state = engine.start()

while not engine.is_finished():
    ready_steps = engine.get_next_steps()
    for step in ready_steps:
        engine.mark_step_running(step.id)
        result = run_agent(step.agent, module=..., page=...)  # 调用 agent_runner
        engine.mark_step_completed(step.id, ...)
```

full-sop.workflow.js 变成 thin wrapper：解析参数 → 调用 workflow_engine → 汇报进度。

### 优先级排序

| 优先级 | 任务 | 预期工作量 | 影响 |
|--------|------|-----------|------|
| **P0** | 解决双层 Agent 定义——以 AGENT_SKILL_MAP 为单一事实源 | 1-2 天 | 消除最大的维护风险 |
| **P0** | agent_runner 从 for 循环改为 Agent 循环（先从 automation-agent 开始） | 3-5 天 | 让一个 Agent 真正"活"起来 |
| **P1** | MCP tool (run_*) 对接 agent_runner | 1 天 | MCP Server 从"建议器"变成"执行器" |
| **P1** | knowledge-agent 成为 event_bus 订阅者 | 1-2 天 | 事件驱动架构首次闭环 |
| **P2** | workflow_engine 对接 agent_runner | 2-3 天 | 消除双轨编排 |
| **P2** | RAG 索引自动重建管线 | 1 天 | 保证检索新鲜度 |
| **P3** | 其余 7 个 Agent 逐个改为 Agent 循环 | 3-5 天/个 | 全平台真 Agent 化 |

---

## 十三、最终输出

### 总体评价

项目有两个正确的核心洞察：(1) AI 测试需要平台独立、(2) Context 按需注入 + RAG 是 Agent 感知的基础。aitest/ 的 LLM 抽象层、context_injector、skill_registry 的设计质量高于平均水平。

**但项目当前卡在了一个中间状态**: 平台层基础设施建好了，但 Agent 没有接入。Claude Code 层能跑通，但绑定平台。这造成了"两套系统并行维护"的负担。

### 优势分析

1. LLM Provider 抽象层（3 个 Provider + Prompt 适配 + 能力检查）是平台独立的核心资产
2. SKILL_CONTEXT_MAP 的声明式上下文需求设计——这是 Agent 感知能力的正确抽象
3. PAGE_INTERFACE.yaml 的结构化 Agent 间接口——减少 Token 消耗的正确方向
4. 8 条代码红线——具体、可自动化检查、无需 AI 介入

### 核心问题（按严重程度排序）

| # | 问题 | 严重度 | 
|---|------|--------|
| 1 | **Agent 不是 Agent**——顺序 for 循环，无规划/观察/状态/协作 | 🔴 致命 |
| 2 | **双层 Agent 定义**——同一概念在 4 处维护 | 🔴 致命 |
| 3 | **workflow_engine 与 full-sop.workflow.js 双轨**——两份编排逻辑 | 🟡 高 |
| 4 | **MCP tool 只返回建议不执行**——agent_runner 未接入 MCP | 🟡 高 |
| 5 | **event_bus 无订阅者**——事件发出了但无人处理 | 🟡 中 |
| 6 | **RAG 索引非自动**——上下文更新后索引可能过期 | 🟡 中 |

### 最大风险

**在 Agent 不是 Agent 的状态下继续增加 Agent 数量或 Skill 数量，会导致"每个 Agent 都需要手动执行"的维护灾难。** 当前 8 个伪 Agent × 每个 3-6 个 Skill = 每次全 SOP 需要人工确认 8 次（每个 Agent 一次）。如果 Agent 数量增长到 12 个，这个摩擦会让人不愿跑全 SOP。

### 建议保留内容

```
✅ aitest/llm/ (provider + skill_loader + context_injector + prompt_adapter + skill_registry)
✅ aitest/rag_engine.py (保留并深化——增加自动索引重建)
✅ aitest/workflow_engine.py (保留但对接 agent_runner)
✅ aitest/agent_scheduler.py (保留但由 Agent 自主调用)
✅ aitest/event_bus.py (保留但激活 knowledge-agent 为订阅者)
✅ aitest/mcp_server.py (保留但对接 agent_runner)
✅ aitest/agent_runner.py (核心改造对象——从 for 循环变成 Agent 循环)
✅ Context 事实源体系
✅ PAGE_INTERFACE.yaml 结构化接口
✅ 8 条代码红线 + 合规检查
✅ known-issues.yaml
✅ SKILL_CONTEXT_MAP 声明式上下文设计
```

### 建议解决（非废弃，而是重构）

```
🔧 .claude/skills/ 和 governance/agents/ 的双层定义 → 以 AGENT_SKILL_MAP 为单一事实源
🔧 agent_runner.run_agent() → 从 for 循环改为 Agent 循环
🔧 full-sop.workflow.js → 改为调用 workflow_engine 的 thin wrapper
🔧 MCP tool 6-8 → 直接调用 agent_runner
🔧 knowledge-agent → 注册为 event_bus 订阅者
```

### 下一阶段重点建设方向

| 优先级 | 方向 | 理由 |
|--------|------|------|
| **P0** | 单一 Agent 定义源 + Agent 循环原型 | 解决两个最致命的结构问题 |
| **P0** | agent_runner 接入 MCP Server | 让平台层从"建议器"变成"执行器" |
| **P1** | knowledge-agent 事件驱动 | 事件驱动架构首次闭环验证 |
| **P1** | PAGE_INTERFACE.yaml 全覆盖 | Token 优化的高 ROI 投入 |
| **P2** | workflow_engine 对接 agent_runner | 消除双轨编排 |
| **P2** | RAG 自动索引重建 | 保证检索质量 |
| **P3** | 补齐模块测试代码 | 真实产出 |

---

> **审计结论 v2**: 你选择了一条正确的但更难的路——建平台而不仅仅是建工具。这条路的核心挑战不是 Skill 太多或 RAG 太早，而是 **Agent 的实现深度与基础设施的完备度不匹配**。你建了 L3 的基础设施（LLM 抽象、RAG、事件总线、工作流引擎），但在上面跑了 L1 的 Agent（顺序 for 循环）。下一阶段的唯一重点应该是：**让 Agent 真正成为 Agent**。
