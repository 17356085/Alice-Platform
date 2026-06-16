# SOP 体系审计报告

> 审计日期: 2026-06-15 | 审计范围: 测试自动化 SOP 全链路 (governance/ + aitest/graphs/ + aitest/agent_runner.py)
> 审计方法: 静态代码分析 + 文件对比 + 状态文件交叉验证 | 未修改任何代码

---

## A. SOP 执行链路图

### A1. 名义架构 (文档宣称)

```
agent-definitions.yaml (full-sop):
  Preflight → Project Init → Module Modeling → Test Design → Automation
  → Execute & Debug → Report → Knowledge
```

### A2. 实际代码执行链路

存在 **两条并行的执行路径**，共享 Agent 定义但编排逻辑不同：

```
路径 1: Claude Code Skill (/full-sop)
  full-sop.workflow.js → agent() spawn → AgentLoop.run()
  编排逻辑: JS workflow script (7 phases)

路径 2: LangGraph CLI (aitest graph run --module=<m>)
  sop_graph.py → StateGraph.compile().invoke()
  编排逻辑: Python LangGraph (10 nodes, 9 canonical phases)
  entry → preflight → route_next_phase → [agent nodes] → exit
```

### A3. 实际代码流转 (LangGraph 路径)

```
                    ┌─────────────────────────────────────┐
                    │           entry_node()              │
                    │  • 计算 skip_phases (based on mode) │
                    │  • 设置 current_phase = "Preflight" │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │         preflight_node()            │
                    │  • 扫描产物文件系统                  │
                    │  • 自动检测推荐 mode                 │
                    │  • P1-5 缓存命中检查                 │
                    │  • resume: 读 SOP_STATUS JSON        │
                    │    过滤: [p for p in saved if        │
                    │           p in CANONICAL_PHASES]     │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │       route_next_phase()            │
                    │  • 遍历 CANONICAL_PHASES            │
                    │  • 跳过 completed + skipped         │
                    │  • Bug Analysis: 仅 execution_failed│
                    │  • 返回下一节点名或 "exit"          │
                    └──────────────┬──────────────────────┘
                                   │
              ┌────────────────────┼────────────────────────┐
              ▼                    ▼                         ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
    │ project_agent   │  │ requirement_agent│  │ test_design_agent    │
    │ make_agent_loop │  │ make_agent_loop  │  │ make_agent_loop      │
    │ → AgentLoop.run │  │ → AgentLoop.run  │  │ → AgentLoop.run      │
    └────────┬────────┘  └────────┬────────┘  └────────┬─────────────┘
             │                    │                      │
             ▼                    ▼                      ▼
    ┌────────────────────────────────────────────────────────────────┐
    │              automation_agent_pre (P1-3 HITL)                   │
    │  skill_subset: [tech-analysis, auto-strategy]                  │
    │  → automation_strategy_approval_node (HITL interrupt)          │
    │  → automation_agent_post                                       │
    │    skill_subset: [page-object-generator, test-script-generator,│
    │                   code-consistency-checker]                    │
    │  → testcase_approval_node (仅 P0 模块 HITL)                    │
    └────────────────────────────────────────────────────────────────┘
             │
             ▼
    ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │ execution_agent │  │ bug_analysis     │  │ data_sanitization │
    │ (subgraph)      │  │ (subgraph, cond) │  │ (mechanical)      │
    └────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                    │                      │
             ▼                    ▼                      ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ report_agent    │  │ knowledge_agent │
    │ (subgraph)      │  │ (subgraph)      │
    └────────┬────────┘  └────────┬────────┘
             │                    │
             └──────────┬─────────┘
                        ▼
              ┌─────────────────────┐
              │    exit_node()      │
              │  • 写入 SOP_STATUS  │
              │  • 发射 CycleEnd    │
              └─────────────────────┘
```

### A4. AgentLoop 内部执行 (每个 Agent 节点内)

```
AgentLoop.run()
  ├── perceive()       ← 检查已存在产物 (幂等性 gate)
  ├── plan()           ← 基于规则 + LLM fallback 决定下一步 Skill
  │   ├── 规则1: 已达 MAX_RETRIES(3) → 强制推进
  │   ├── 规则2: code-consistency-checker 失败 → 强制推进 (确定性)
  │   └── 规则3: 连续文件缺失 → 强制推进
  ├── act(skill_id)    ← 执行 Skill
  │   ├── code-consistency-checker → _act_mechanical_consistency_check()
  │   │   └── ★ 永远走 mechanical 模式 (grep), review 模式从未被调用
  │   └── 其他 Skill → run_skill() → LLM 调用
  ├── observe()        ← 验证产物 (存在性 + 代码红线)
  └── update()         ← 更新 AgentState
```

---

## B. 状态流图

### B1. Phase 名称不一致 — 三个不同标准并存

| 文件 | Phase 列表 | 数量 |
|------|-----------|------|
| `aitest/graphs/state.py` | Project Init, **Requirement**, Test Design, Automation, **Execute & Debug**, Bug Analysis, **Data Sanitization**, Report, Knowledge | 9 |
| `governance/validators/sop_validator.py` | **Preflight**, Project Init, **Module Modeling**, Test Design, Automation, **Execution**, Bug Analysis, Report, Knowledge | 9 |
| `governance/agents/agent-definitions.yaml` (full-sop) | Preflight, Project Init, Module Modeling, Automation, Execute & Debug, Report, Knowledge | 8 (无 Bug Analysis, Data Sanitization) |
| `governance/workflows/sop-summary.md` (legacy) | Phase 0~9 + decimal sub-phases (0.5, 0.8, 1.5, 2.5, 3.5) | 18 |

**冲突矩阵**:

| 概念 | state.py | sop_validator.py | agent-definitions.yaml | sop-summary.md |
|------|----------|------------------|----------------------|----------------|
| 前置检查 | (无, 隐式) | "Preflight" | "Preflight" | Phase 0 |
| 需求分析 | **"Requirement"** | **"Module Modeling"** | **"Module Modeling"** | Phase 0.5/0.8 |
| 测试执行 | **"Execute & Debug"** | **"Execution"** | **"Execute & Debug"** | Phase 4.5/5 |
| 数据清理 | **"Data Sanitization"** | (缺失) | (缺失) | (缺失) |
| Bug分析 | "Bug Analysis" | "Bug Analysis" | (缺失) | Phase 4.5/5 |

### B2. 状态存储源 (6 个并发状态源)

```
┌──────────────────────────────────────────────────────────────────┐
│                      状态存储架构 (现状)                          │
├───────────────┬──────────────────────┬───────────────────────────┤
│ 存储位置       │ 格式                  │ 更新方式                  │
├───────────────┼──────────────────────┼───────────────────────────┤
│ ① SOP_STATUS  │ JSON 文件             │ exit_node() 写入          │
│   artifacts/  │ (格式不统一)           │ ★ 仅写 completed_phases   │
│   sop-status/ │                       │   不写 per-page 详情      │
├───────────────┼──────────────────────┼───────────────────────────┤
│ ② LangGraph   │ SQLite               │ SqliteSaver 自动          │
│   .graph_state│ (checkpoints)         │ ★ 包含完整 State          │
│   checkpoints │                       │   但格式与 JSON 不兼容    │
├───────────────┼──────────────────────┼───────────────────────────┤
│ ③ EventBus    │ JSON 文件             │ emit() 事件触发           │
│   .events/    │ (AgentCompleted etc.) │ ★ 事件驱动, 非状态快照    │
├───────────────┼──────────────────────┼───────────────────────────┤
│ ④ Trace logs  │ JSONL                 │ run_skill() 自动          │
│   .traces/    │ (trace_log.jsonl)     │ ★ 细粒度, 非聚合          │
├───────────────┼──────────────────────┼───────────────────────────┤
│ ⑤ ChromaDB   │ SQLite + binary       │ knowledge_agent 更新      │
│   .chroma/    │ (向量嵌入)            │ ★ 语义索引, 非流程状态    │
├───────────────┼──────────────────────┼───────────────────────────┤
│ ⑥ Workflow    │ JSON 文件             │ workflow 引擎写入         │
│   .workflow_  │ (run-*.json)          │ ★ 仅 workflow 级, 非 SOP  │
│   state/runs/ │                       │                           │
└───────────────┴──────────────────────┴───────────────────────────┘
```

### B3. source-of-truth.md 自相矛盾

```markdown
Line 15: "SOP 运行状态 → artifacts/sop-status/SOP_STATUS_<module>.json → 作为流程门禁依据"
Line 17: "LangGraph 编排状态 → .graph_state/checkpoints.sqlite → 替代 SOP_STATUS JSON"

问题: 第 15 行说 SOP_STATUS JSON 是门禁依据, 第 17 行说 SQLite 替代了 JSON。
      实际代码两处都写, 但格式不兼容, 且没有同步机制。
```

---

## C. 状态漂移风险

### C1. 已验证的漂移实例

| 模块 | 症状 | 根因 |
|------|------|------|
| **tank** | `"status":"completed"` 但 `"completed_phases":[]` | exit_node 写入时 `completed_phases` 来自 state, 可能为空列表 (因为 CANONICAL_PHASES 过滤导致) |
| **equipment** | 同上: `"status":"completed"` + `"completed_phases":[]` | 同上 |
| **system-management** | Phase 名称为 `"Phase 0 (Project Init)"` 格式, 不符合任何 CANONICAL_PHASES 定义 | 旧格式, 手动写入或旧版 exit_node 写入 |
| **lab** | 同上: 旧格式 Phase 名称, 包含 `"Phase 1.5"` 等小数 Phase | 旧格式 |
| **production** | `"completed_phases"` 包含 `"Test Design (4/5 pages:...)"` 等复合字符串 | 非标准格式, 无法被 resume 模式解析 |
| **warehouse** | `"completed_phases"` 跳过了 Phase 1, 1.5, 2, 2.5 — 直接跳到 Phase 3-4 | 绕过 SOP 顺序 |
| **warehouse** | `"sop_version":"10-phase"` 字段存在但无其他文件使用此字段 | 孤立的元数据 |

### C2. resume 模式无法正确恢复

```python
# sop_graph.py preflight_node line 149-150:
saved_completed = status_data.get("completed_phases", [])
completed_phases = [p for p in saved_completed if p in CANONICAL_PHASES]
```

由于 `CANONICAL_PHASES = ["Project Init", "Requirement", ...]` (state.py)，而旧格式 SOP_STATUS 使用 `"Phase 0 (Project Init)"` 等名称，**过滤结果必然为空列表**。即 resume 模式在 6 个模块中有 4 个 (`tank`, `equipment`, `system-management`, `lab`, `production`) 无法正确恢复进度。

### C3. 漂移传播路径

```
SOP_STATUS JSON (旧格式) → preflight 过滤 → completed_phases=[] → 重跑已完成 Phase
                                                                       ↓
                                                                 重复生成产物
                                                                       ↓
                                                              AgentLoop perceive()
                                                              检测到产物已存在
                                                              设置 skip_candidate
                                                                       ↓
                                                              ★ Agent 静默跳过
                                                              ★ 但 Phase 状态机认为未完成
                                                              ★ 门禁检查仍然报缺失
```

---

## D. 无效 Phase

### D1. 定义层冗余

| Phase | 出现位置 | 问题 |
|-------|---------|------|
| **"Preflight"** | `sop_validator.py` CANONICAL_PHASES, `agent-definitions.yaml` | `state.py` 的 CANONICAL_PHASES 中**不包含** Preflight — 它是隐式的, 不在 Phase 遍历中 |
| **"Data Sanitization"** | `state.py` CANONICAL_PHASES | `sop_validator.py` 和 `agent-definitions.yaml` 中**均不包含** — 其他系统不知道这个 Phase 存在 |
| **Phase 1.5 (Risk Modeling)** | `sop-summary.md`, SOP_STATUS 文件中 | 不是独立 Agent, 已合并到 test-design-agent 的 `risk-modeling` Skill |
| **Phase 2.5 (Test Cases)** | `sop-summary.md` | 同上, 已合并到 test-design-agent 的 `testcase-design` Skill |
| **Phase 3.5 (Auto Strategy)** | `sop-summary.md` | 同上, 已合并到 automation-agent 的 `auto-strategy` Skill |
| **Phase 5 (自动化失败分析)** | `sop-summary.md` | 与 Phase 4.5 (Bug Analysis) 重复, `sop-summary.md` 自身有 18 个 Phase 定义 |
| **Phase 6 (接口测试)** | `sop-summary.md` | 在任何 Agent 定义中均无对应, 无执行路径 |
| **Phase 7 (CI 分析)** | `sop-summary.md` | 同上 |

### D2. 代码层死路径

| 位置 | 死代码 | 说明 |
|------|--------|------|
| `agent_runner.py:1063` | `code-consistency-checker` → `_act_mechanical_consistency_check()` | **永远走 mechanical 模式**, Skill 文档定义的 `review` (LLM 对抗性审查) 模式**从未被调用** |
| `agent_runner.py:892-897` | `code-consistency-checker` 失败 → 强制 continue | 重试被禁用是合理的, 但**失败不会阻塞后续 Phase** — 违规代码可以流入下一阶段 |
| `sop_graph.py:704` | `use_subgraphs=False` 分支 | fallback 到 pass-through 节点, 但所有 Agent 节点都使用 `make_agent_loop_node` |
| `sop_validator.py:266-274` | Bug Analysis ↔ Report 互斥规则 | 与 `sop_graph.py:665` 逻辑矛盾 — 实际代码中 Report 总是在 Bug Analysis 之后执行 (或跳过 Bug Analysis), 两者不是互斥的 |
| `state.py:252-253` | `current_skill`, `completed_skills` 顶层字段 | 标注 `@deprecated`, 但未被移除, 仍有代码写入 |

### D3. 未连接的 Skill

| Skill | 注册位置 | 问题 |
|-------|---------|------|
| `test-design/api-testing` | skill-registry.yaml, test-design-agent | `sop_graph.py` 的 test_design_agent 调用 `make_agent_loop_node("test-design-agent")` 但未限制 skill_subset — 理论上 `api-testing` 和 `miniapp-testing` 可选但 Phase 6/7 不存在 |
| `test-design/miniapp-testing` | 同上 | 同上 |
| `execution/excel-exporter` | report-agent skills | 在 `agent-definitions.yaml` 中注册但 `execution_graph.py` 的 `build_report_subgraph` 中标记为 "当前图中未使用" |
| `diagnosis/jenkinsfile-generator` | bug-analysis-agent | 在任何 SOP 图中无调用点 |

---

## E. 缺失自动化同步点

### E1. 关键同步缺失

| 缺失项 | 影响 | 严重度 |
|--------|------|--------|
| **SOP_STATUS ↔ LangGraph checkpoint** | 两个"权威"状态源从未同步; resume 模式只能读 JSON, 而 JSON 格式不兼容 | 🔴 高 |
| **sop-summary.md ↔ 实际代码** | `sop-summary.md` 定义 18 个 Phase, 实际代码只有 9 个; 模型分配 (Opus/Sonnet/Haiku) 与实际 `model_tiering` 配置不一致 | 🔴 高 |
| **Preflight cache 无失效机制** | `_preflight_cache` (模块级全局变量) 在产物变更后不会失效 — 可能导致过期推荐 | 🟡 中 |
| **code-consistency-checker 输出未持久化** | 检查报告仅存在于 LLMResponse.content 中, 从未写入 artifacts/ — 下一 Phase 无法引用 | 🟡 中 |
| **agent-definitions.yaml → .claude/skills/ 同步** | `check_agent_drift.py` 存在但**不自动运行** — 无 CI hook, 无 pre-commit | 🟡 中 |
| **SOP_STATUS 格式迁移** | 6 个模块中有 4 个使用旧格式 — 无自动迁移脚本 | 🔴 高 |
| **Gate 验证结果未写入 SOP_STATUS** | `check_sop_gate.py` 的检查结果不会更新 SOP_STATUS JSON | 🟡 中 |
| **EventBus 事件无消费者** | `AgentCompleted` 和 `CycleEnd` 事件被发射但 `.events/` 目录中的文件仅被写入, 未被读取消费 | 🟢 低 |

### E2. Gate 执行链断裂点

```
                    ┌──────────────────────────┐
                    │  CLI: aitest graph run   │
                    │  ★ 不调用 check_sop_gate │  ← 断裂点 1
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  LangGraph preflight     │
                    │  ★ 文件存在性检查        │
                    │  ★ 但不验证 Phase 顺序   │  ← 断裂点 2
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  AgentLoop perceive()    │
                    │  ★ 幂等性检查 (skip)     │
                    │  ★ 但 skip 不更新状态机  │  ← 断裂点 3
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  AgentLoop observe()     │
                    │  ★ 产物存在性 + 红线检查 │
                    │  ★ 失败 → retry/skip     │
                    │  ★ skip 不阻塞 Phase     │  ← 断裂点 4
                    └──────────────────────────┘
```

### E3. CLAUDE.md 路径错误

```markdown
CLAUDE.md line: "python tools/check_sop_gate.py --module <m> --agent <a> --json"
实际路径: ZJSN_Test-master526/tools/check_sop_gate.py
```

但当前工作目录是 `d:\Desktop\WorkStudy`, 直接用 `tools/check_sop_gate.py` 找不到文件。

---

## F. 优化建议

### F1. 🔴 紧急 (状态一致性)

| # | 建议 | 涉及文件 |
|---|------|---------|
| 1 | **统一 Phase 名称定义** — 将 3 套 CANONICAL_PHASES 合并为 1 个 shared constant, 放在 `aitest/graphs/state.py` 中, `sop_validator.py` 从那里 import | `state.py`, `sop_validator.py`, `agent-definitions.yaml` |
| 2 | **SOP_STATUS 格式迁移** — 运行一次性脚本, 将 4 个旧格式文件 (`system-management`, `lab`, `production`, `warehouse`) 的 `completed_phases` 改写为规范 PhaseName | `artifacts/sop-status/*.json` |
| 3 | **修复 resume 模式** — `preflight_node` 在加载 SOP_STATUS 时同时尝试匹配旧格式名称 (如 `"Phase 0 (Project Init)"`) 和新格式 | `sop_graph.py:149-150` |
| 4 | **exit_node 写完整状态** — 除了 `completed_phases`, 还应写入 `per_page_results` 和 `agent_outputs` 摘要, 让 SOP_STATUS 真正可独立用于 resume | `sop_graph.py:329-338` |

### F2. 🟡 建议 (自动化同步)

| # | 建议 | 涉及文件 |
|---|------|---------|
| 5 | **SOP_STATUS ↔ Checkpoint 双向同步** — 在 `exit_node` 中同时确保 checkpoint 和 JSON 一致; 或在 `entry_node` 中以 checkpoint 为准 | `sop_graph.py` |
| 6 | **code-consistency-checker review 模式** — 在 `AgentLoop.plan()` 中添加逻辑: 当 `mechanical` 模式通过时, 可选触发 `review` 模式 (LLM 对抗性审查) | `agent_runner.py:1063` |
| 7 | **code-consistency-checker 输出持久化** — 将检查报告写入 `artifacts/code-review/<module>/` | `agent_runner.py:1177-1224` |
| 8 | **Preflight cache TTL** — 为 `_preflight_cache` 添加基于文件 mtime 的失效检查 | `sop_graph.py:58-61` |
| 9 | **check_agent_drift.py 集成 CI** — 在 Jenkinsfile 或 pre-commit hook 中运行 drift 检查 | `Jenkinsfile`, `.pre-commit-config.yaml` |

### F3. 🟢 优化 (清理)

| # | 建议 | 涉及文件 |
|---|------|---------|
| 10 | **删除/归档 `sop-summary.md`** — 它与实际代码严重不一致 (18 vs 9 Phase), 应替换为自动生成的文档 | `workflows/sop-summary.md` |
| 11 | **移除 `use_subgraphs=False` 分支** — 所有 Agent 节点已统一使用 `make_agent_loop_node`, pass-through 分支是死代码 | `sop_graph.py:704, 760-761` |
| 12 | **删除 deprecated 顶层状态字段** — `current_skill`, `completed_skills` (顶层), `trace_events` 标注 deprecated 但仍占用状态空间 | `state.py:252-253, 273` |
| 13 | **修复 CLAUDE.md 路径** — 将 `tools/check_sop_gate.py` 改为 `ZJSN_Test-master526/tools/check_sop_gate.py` 或提供完整路径 | `CLAUDE.md` |
| 14 | **sop_validator.py 移除 Bug/Report 互斥规则** — 该规则与 `sop_graph.py` 实际执行逻辑矛盾 | `sop_validator.py:266-274` |
| 15 | **移除未连接的 Skill** — `api-testing`, `miniapp-testing`, `jenkinsfile-generator` 如确无调用路径应标记为 experimental 或移除 | `skill-registry.yaml` |

### F4. 架构建议

| # | 建议 |
|---|------|
| 16 | **统一两条执行路径** — 目前 `full-sop.workflow.js` (Claude Code Skill) 和 `sop_graph.py` (LangGraph) 是两套独立的编排逻辑。建议: 让 Claude Code Skill 直接调用 `aitest graph run` CLI, 而非自己实现编排 |
| 17 | **Gate 检查前置到 CLI 入口** — 在 `aitest graph run` 命令中, 先调用 `check_sop_gate.py`, gate blocked 则拒绝执行并给出建议 |
| 18 | **状态文件单一化** — 选择 SOP_STATUS JSON 或 LangGraph checkpoint 作为唯一状态源, 另一个作为只读缓存。推荐以 checkpoint 为主 (支持时间旅行), JSON 为人类可读导出 |

---

## 附录: 文件索引

### 审计涉及的关键文件

| 文件 | 行数 | 角色 |
|------|------|------|
| [state.py](aitest/graphs/state.py) | 350 | Phase 名称 + 状态定义 (CANONICAL_PHASES) |
| [sop_graph.py](aitest/graphs/sop_graph.py) | ~800 | LangGraph 编排器主图 |
| [agent_runner.py](aitest/agent_runner.py) | 1815 | AgentLoop 执行引擎 |
| [agent-definitions.yaml](governance/agents/agent-definitions.yaml) | 298 | Agent 定义单一事实源 |
| [sop_validator.py](governance/validators/sop_validator.py) | 596 | SOP 校验器 (CANONICAL_PHASES #2) |
| [check_sop_gate.py](ZJSN_Test-master526/tools/check_sop_gate.py) | 458 | 门禁检查 CLI |
| [gate_checker.py](aitest/mcp/tools/gate_checker.py) | 83 | MCP 门禁封装 |
| [full-sop.workflow.js](governance/agents/full-sop.workflow.js) | ~200 | Claude Code Skill 编排 (并行路径) |
| [source-of-truth.md](governance/context/source-of-truth.md) | 28 | 事实源分工 (自相矛盾) |
| [skill-registry.yaml](governance/skills/skill-registry.yaml) | 233 | Skill 注册表 |
| [workflow-registry.yaml](governance/workflows/workflow-registry.yaml) | 208 | Workflow 注册表 |
| [sop-summary.md](governance/workflows/sop-summary.md) | 56 | 旧 SOP 摘要 (18 Phase) |
| [code-consistency-checker.md](governance/skills/automation/code-consistency-checker.md) | 95 | Skill 定义 (review 模式未使用) |
| [check_agent_drift.py](ZJSN_Test-master526/tools/check_agent_drift.py) | 313 | Agent drift 检测 (未自动运行) |

### SOP_STATUS 文件

| 文件 | status | completed_phases | 格式 |
|------|--------|-----------------|------|
| [SOP_STATUS_tank.json](governance/artifacts/sop-status/SOP_STATUS_tank.json) | completed | **[]** (空) | LangGraph 新格式但空 |
| [SOP_STATUS_equipment.json](governance/artifacts/sop-status/SOP_STATUS_equipment.json) | completed | **[]** (空) | LangGraph 新格式但空 |
| [SOP_STATUS_system-management.json](governance/artifacts/sop-status/SOP_STATUS_system-management.json) | completed | 8 phases (旧格式) | 旧格式 "Phase N (...)" |
| [SOP_STATUS_lab.json](governance/artifacts/sop-status/SOP_STATUS_lab.json) | completed | 11 phases (旧格式) | 旧格式 "Phase N (...)" |
| [SOP_STATUS_production.json](governance/artifacts/sop-status/SOP_STATUS_production.json) | in_progress | 7 phases (混合格式) | 混合格式 |
| [SOP_STATUS_warehouse.json](governance/artifacts/sop-status/SOP_STATUS_warehouse.json) | completed | 4 phases (旧格式, 跳 Phase) | 旧格式, 顺序异常 |

---

*审计工具: 静态代码分析, 未执行任何代码修改。*
*建议的修复应作为独立的变更进行, 并在实施后进行回归验证。*
