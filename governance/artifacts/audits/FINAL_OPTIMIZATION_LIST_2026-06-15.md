# 最终优化单 — AITest Platform SOP 体系

> 综合 SOP 体系审计 + Context Cost 审计 | 2026-06-15

---

## 一、必做项 (6 条)

### 1. 统一 Phase 名称定义

**问题**: [state.py](aitest/graphs/state.py#L145) 定义 `"Requirement"`, [sop_validator.py](governance/validators/sop_validator.py#L23) 定义 `"Module Modeling"`, [agent-definitions.yaml](governance/agents/agent-definitions.yaml#L268) 用 `"Module Modeling"` — 三个文件三套名字。`resume` 模式因名称不匹配**完全失效**。

**做法**: 以 `state.py` 为唯一源。`sop_validator.py` 改为 `from aitest.graphs.state import CANONICAL_PHASES`。`agent-definitions.yaml` 的 full-sop.phases 使用相同的 PhaseName 字面量。同步删除 `sop-summary.md` 中 18 个 Phase 的旧定义。

```
涉及: state.py, sop_validator.py, agent-definitions.yaml, sop-summary.md
```

### 2. 修复 resume 模式 + 迁移 6 个 SOP_STATUS 文件

**问题**: 全部 6 个 SOP_STATUS JSON 文件格式不一致:
- `tank`, `equipment`: `completed_phases: []` 但 `status: "completed"` (自相矛盾)
- `system-management`, `lab`, `production`, `warehouse`: 使用旧格式 `"Phase 0 (Project Init)"` 而非 `"Project Init"`

`preflight_node` 第 149 行 `completed_phases = [p for p in saved if p in CANONICAL_PHASES]` 将旧格式名称**全部过滤为空**。

**做法**:
- [preflight_node](aitest/graphs/sop_graph.py#L149) 添加旧→新名称映射表: `"Phase 0 (Project Init)" → "Project Init"`, `"Phase 0.5 (Module Modeling)" → "Requirement"`, 等
- 运行一次性脚本将 6 个 JSON 文件标准化
- `exit_node` 写入时补充 `per_page_results` 摘要

```
涉及: sop_graph.py, artifacts/sop-status/*.json
```

### 3. PAGE_INTERFACE.yaml: 修复生成规则

**问题**: [CONTEXT_COST_AUDIT](CONTEXT_COST_AUDIT_2026-06-15.md) 实测数据 — 57 个 PAGE_INTERFACE.yaml 平均 2,223 tokens，比对应的 PAGE_CONTEXT.md 大 3-10 倍。但 [source-of-truth.md](governance/context/source-of-truth.md#L16) 声称它为"下游 Agent 减少 Token 消耗 (~200 tokens)"。**优化变成了膨胀**。

**做法**: 修改 [page-interface-generator](governance/skills/test-design/page-interface-generator.md) 的提取规则:
- elements 最多 5 个关键交互元素
- test_scenarios 最多 5 个核心场景
- **不得重复** PAGE_CONTEXT.md 已有的定位器信息
- 目标: 每个 YAML ≤ 600 chars (≈200 tokens)

或直接废弃 PAGE_INTERFACE.yaml，让 automation-agent 读 PAGE_CONTEXT.md（Cost 审计建议方向）。

```
涉及: skills/test-design/page-interface-generator.md (或 page-analysis.md 后处理段)
```

### 4. 删除 4 对 active/_deprecated 的重复文件

**问题**: 4 个 Skill 文件在 active 和 `_deprecated/` 目录下**完全相同** (bit-for-bit)。`skill-registry.yaml` 已标记为 replaced，但 active 目录下的文件未删除。

| 文件 | 大小 | 位置 |
|------|------|------|
| knowledge-extractor.md | 4,426 chars | `skills/knowledge/` + `skills/_deprecated/` |
| knowledge-precipitation.md | 2,180 chars | `skills/knowledge/` + `skills/_deprecated/` |
| progress-report.md | 1,692 chars | `skills/reporting/` + `skills/_deprecated/` |
| test-summary.md | 2,006 chars | `skills/reporting/` + `skills/_deprecated/` |

**做法**: 从 active 目录删除这 4 个文件。它们已被 `knowledge-manager` 和 `report-generator` 替代。

```
涉及: skills/knowledge/ (2 files), skills/reporting/ (2 files)
```

### 5. 修正 source-of-truth.md 自相矛盾

**问题**: 第 15 行说 SOP_STATUS JSON 是门禁依据，第 17 行说 LangGraph checkpoint SQLite 替代了 JSON。两者并存、格式不兼容、无同步。

**做法**: 明确 checkpoint SQLite 为权威状态源，JSON 为人类可读导出。删除第 17 行的"替代"措辞，改为"JSON 为 SQLite 的导出快照，人类可读。程序以 SQLite 为准。"

```
涉及: governance/context/source-of-truth.md
```

### 6. SOP_STATUS 位置去重

**问题**: `SOP_STATUS_<module>.json` 同时存在于 `artifacts/sop-status/` 和 `context/projects/web-automation/modules/<module>/`。

**做法**: 仅保留 `artifacts/sop-status/`。

```
涉及: context/projects/web-automation/modules/equipment/SOP_STATUS_equipment.json
      context/projects/web-automation/modules/tank/SOP_STATUS_tank.json
      (及 system 目录下的 SOP_STATUS_system.json)
```

---

## 二、建议做 (5 条)

### 7. Agent pipeline 文档自动生成

**问题**: 同一套 Phase→Agent→Skill 映射维护在 4 个地方: `agent-definitions.yaml`, `agents/README.md`, `project-index.yaml`, `full-sop SKILL.md`。约 8,300 tokens 等效信息重复维护。

**做法**: `agents/README.md` 和 `project-index.yaml` 的 Agent 段改为从 `agent-definitions.yaml` 自动生成（脚本或 CI hook）。

```
涉及: agents/README.md, context/project-index.yaml, 新增生成脚本
```

### 8. code-consistency-checker 补齐 LLM 审查 + 报告持久化

**问题**: [agent_runner.py:1063](aitest/agent_runner.py#L1063) 硬编码走 `_act_mechanical_consistency_check()` (grep)。Skill 文档定义的 `review` 模式 (LLM 对抗性审查) **从未被调用**。且检查结果不写文件。

**做法**:
- `AgentLoop.plan()` 中添加: mechanical 通过后，可选触发 review 模式
- 检查报告写入 `artifacts/code-review/<module>/<page>/`
- 失败时在 SOP_STATUS 中记录 warning (不阻塞但可追溯)

```
涉及: agent_runner.py
```

### 9. Gate 检查前置到 CLI 入口

**问题**: `aitest graph run` 不调用 `check_sop_gate.py`。preflight 检查文件存在性但不验证 Phase 顺序。AgentLoop 的 skip 不更新状态机。共 5 个断裂点。

**做法**: `aitest graph run` 启动时先跑 `check_sop_gate.py --module <m> --agent <a> --json`，blocked → 拒绝启动并给出建议。

```
涉及: aitest/cli/ (graph run 命令), check_sop_gate.py
```

### 10. 统一两条执行路径

**问题**: `full-sop.workflow.js` (Claude Code Skill) 和 `sop_graph.py` (LangGraph) 各自独立编排。共享 Agent 定义但逻辑不同。JS 路径无 checkpoint/HITL；Python 路径无法从 Claude Code 直接触发。

**做法**: 二选一:
- **推荐**: JS workflow 改为薄 wrapper，调用 `aitest graph run` CLI
- 备选: 保留 JS workflow，补齐 checkpoint 和 HITL 能力

```
涉及: full-sop.workflow.js, .claude/skills/full-sop/SKILL.md
```

### 11. check_agent_drift.py 集成 CI

**问题**: `check_agent_drift.py` 存在且完整，但无 CI hook、无 pre-commit，从未自动运行。

**做法**: 添加到 Jenkinsfile pipeline 或 `.pre-commit-config.yaml`。

```
涉及: Jenkinsfile, .pre-commit-config.yaml (新建)
```

---

## 三、可选清理 (5 条)

### 12. 移除 `sop_validator.py` 的 Bug/Report 互斥规则

[sop_validator.py:266-274](governance/validators/sop_validator.py#L266) 规定 Bug Analysis 和 Report 互斥——但 [sop_graph.py:665](aitest/graphs/sop_graph.py#L665) 实际逻辑中 Report 总是在 Bug Analysis 后执行。规则与代码矛盾。

### 13. 删除 `state.py` 中的 deprecated 字段

`current_skill`, `completed_skills` (顶层), `trace_events` 三个字段标注 `@deprecated` 但仍占用状态空间。P2-4 重构后实际使用 `agent_outputs[agent_name]` 下的 `AgentResult`。

### 14. 移除 `sop_graph.py` 的 `use_subgraphs=False` 分支

所有 Agent 已统一用 `make_agent_loop_node`。第 704/760-761 行的 pass-through fallback 是死代码。

### 15. 标记未连接的 Skill

`test-design/api-testing`, `test-design/miniapp-testing`, `diagnosis/jenkinsfile-generator` 在 `skill-registry.yaml` 中为 active，但在任何 SOP 图中无调用路径。标记为 `status: experimental`。

### 16. 存档 `sop-summary.md`

18 个 Phase 定义与实际 9 个 Phase 代码严重不一致。模型分配 (Opus/Sonnet/Haiku) 与实际 `model_tiering` 配置不符。移至 `_archived/`，替换为从 `agent-definitions.yaml` 自动生成的摘要。

---

## 执行顺序

```
第 1 步 (止损，无风险):  4 → 5 → 6 → 12 → 13 → 14
                        删重复文件 + 修正文档 + 删死代码

第 2 步 (根因修复):      1 → 2
                        统一 Phase 定义 + 修复 resume + 迁移 JSON

第 3 步 (Token 优化):    3
                        PAGE_INTERFACE 修复或废弃 ← 需决策

第 4 步 (架构):          7 → 8 → 9 → 10 → 11
                        自动生成 + 补齐 code reviewer + Gate 前置 + 路径统一 + CI

第 5 步 (收尾):          15 → 16
                        标记未连接 Skill + 归档旧文档
```

---

## 量化目标

| 指标 | 当前 | 目标 |
|------|------|------|
| CANONICAL_PHASES 定义 | 3 套 | 1 套 |
| SOP_STATUS 可用模块 | 0/6 | 6/6 |
| resume 模式 | 失效 | 正常工作 |
| 状态存储源 | 6 个 | 2 个 (SQLite 主 + JSON 导出) |
| 每页面接口读取 token | ~2,223 (PAGE_INTERFACE) | ~200 或直接读 PAGE_CONTEXT |
| 死代码路径 | 5 个 | 0 |
| Agent pipeline 维护副本 | 4 份 | 1 份 + 2 自动生成 |
| 纯冗余文件 | 4 对 (active+_deprecated) | 0 |
| 执行编排路径 | 2 条 (JS + Python) | 1 条 |
