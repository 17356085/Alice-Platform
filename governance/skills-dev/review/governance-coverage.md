# Skill: review/governance-coverage

### 目标
评估治理体系的覆盖完整性：哪些模块/Agent/Skill/流程未被现有治理机制覆盖。输出覆盖热力图、盲区清单、补全建议。

### 输入
- `governance/agents/agent-definitions.yaml` + `agent-definitions-dev.yaml` — 所有 Agent 定义
- `governance/skills/skill-registry.yaml` + `skill-registry-dev.yaml` — 所有 Skill 定义
- `aitest/graphs/sop_graph.py` — SOP 流程定义
- `aitest/state_auditor.py` — State Auditor 检查维度
- `aitest/sop_auditor.py` — SOP Auditor 检查维度
- `aitest/cost_auditor.py` — Cost Auditor 检查维度
- `aitest/regression.py` — Regression Gate 覆盖范围
- `governance/workflows/workflow-registry.yaml` — 工作流门禁规则
- `governance/context/source-of-truth.md` — 事实源定义
- 所有 SOP_STATUS_*.json 文件 — 模块运行状态

### 输出
- `GOV_COVERAGE.md`：覆盖矩阵（模块 × 治理维度）、盲区清单（含风险等级）、治理补全路线图

### 规则
- 治理维度（每维度单独打分）:
  1. **状态治理覆盖** — State Auditor 是否覆盖所有模块？哪些模块无 SOP_STATUS？
  2. **流程治理覆盖** — SOP Auditor 是否覆盖所有 Agent？哪些 Agent 可绕过 SOP Graph？
  3. **成本治理覆盖** — Cost Auditor 是否追踪所有 Skill？哪些 Skill 无 token 追踪？
  4. **质量治理覆盖** — Regression Gate 是否覆盖所有 Skill？哪些 Skill 无回归测试？
  5. **知识治理覆盖** — Knowledge Agent 是否消费所有事件类型？哪些事件无人消费？
  6. **门禁覆盖** — 每个模块是否有明确的门禁规则？哪些模块无 workflow gate？
- 盲区 = 模块/Agent/Skill 在某个治理维度上完全没有检查
- 薄弱区 = 有检查但检查深度不够（如只有 quick check 没有 deep check）
- 每个盲区标注风险等级（Critical/Major/Minor）

### 依赖
- 依赖所有 Auditor 定义文件和 SOP_STATUS 文件
- 无前置 Skill

### 边界
- 不修改治理配置
- 不添加审计规则
- 只评估覆盖，不评估治理本身的有效性（有效性评估由 sop-effectiveness 负责）

### 检查清单
- [ ] 模块 × 状态治理 矩阵完成
- [ ] 模块 × 流程治理 矩阵完成
- [ ] Skill × 成本治理 矩阵完成
- [ ] Skill × 质量治理 矩阵完成
- [ ] 事件 × 知识治理 矩阵完成
- [ ] 盲区按风险等级排序
- [ ] 补全建议可执行

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/GOV_COVERAGE-{{date}}.md`
- 格式: 遵循 `governance/templates/review-report.template.md` 标准结构

---

## Prompt 模板

```text
你是一个治理架构师，专精于 AI Agent 系统的治理体系设计和覆盖完整性评估。

## 治理上下文

### Agent 清单
{{AGENT_LIST_WITH_PHASES}}

### Skill 清单
{{SKILL_LIST_WITH_STATUS}}

### Auditor 定义
- State Auditor 检查维度：S/R/O/C/Q/T/Orphan (7 checks)
- SOP Auditor 检查维度：P/S/G/H/B/L/X (7 checks)
- Cost Auditor 检查维度：Spike/Bloat/Trend/Model (4 checks)
- Regression Gate：{{N}} 个 golden test cases

### Event Bus 事件类型（已有）
{{EVENT_TYPES}}

### 模块 SOP 状态
{{SOP_STATUS_SUMMARY}}

### 工作流门禁规则
{{WORKFLOW_GATE_RULES}}

## 评估任务

### 1. 模块 × 治理维度 覆盖矩阵

对每个模块，评估以下治理维度的覆盖状态：

| 模块 | State Audit | SOP Audit | Cost Audit | Regression | Knowledge | Gate | 综合 |
|------|-------------|-----------|------------|------------|-----------|------|------|
| equipment | ✅/🟡/❌ | ✅/🟡/❌ | ... | ... | ... | ... | xx% |

✅ = 完整覆盖  🟡 = 部分覆盖（有薄弱）  ❌ = 完全未覆盖

### 2. Agent × 治理维度 覆盖矩阵

对每个 Agent (17个)，评估：
- 是否在 SOP Graph 的必经路径上？
- 是否有直接调用（绕过 SOP）的可能？
- 其输出是否被任何 Auditor 检查？
- 其 Skill 是否被 Regression Gate 覆盖？

### 3. Skill × 治理维度 覆盖矩阵

对每个 Skill (24+32=56个)，评估：
- 是否有 token 追踪？
- 是否有回归测试用例？
- Prompt 是否有版本管理？
- 是否有明确的 deprecated/experimental 标记？

### 4. 事件 × 消费 覆盖矩阵

| 事件类型 | Knowledge Agent | 人工 | 其他订阅者 | 覆盖状态 |
|----------|----------------|------|-----------|---------|
| StateDrift | ✅ | - | - | ✅ |
| ... | | | | |

### 5. 盲区清单

按风险等级排列：
- **Critical**: 核心模块/Agent/Skill 完全缺失某个治理维度
- **Major**: 有检查但深度不够
- **Minor**: 非核心组件，暂时可接受

## 输出格式

```markdown
# Governance Coverage Review — {{MODULE_OR_SYSTEM}}

---
report_id: REVIEW-{{DATE}}-{{UUID8}}
review_type: governance
module: {{MODULE}}
trigger: {{TRIGGER}}
depth: standard
reviewer: review/governance-coverage v1.0
created: {{ISO8601}}
---

## Executive Summary

**Overall Coverage Score:** {{SCORE}}/100
**Blind Spots (Critical):** {{N}}
**Weak Areas:** {{N}}
**Full Coverage:** {{PERCENTAGE}}%

## Coverage Heatmap

### Module × Governance Dimension

{{HEATMAP_TABLE}}

### Agent × Governance Dimension

{{HEATMAP_TABLE}}

### Skill × Governance Dimension

{{SKILL_COVERAGE_SUMMARY}}

### Event × Consumer

{{EVENT_CONSUMER_MATRIX}}

## Blind Spots

### Critical (must fix)

| ID | Target | Missing Dimension | Risk | Recommendation |
|----|--------|------------------|------|----------------|
| C01 | ... | ... | ... | ... |

### Major (should fix)

| ID | Target | Missing Dimension | Risk | Recommendation |
|----|--------|------------------|------|----------------|

## Governance Gap Analysis

{{ANALYSIS_OF_WHY_GAPS_EXIST_AND_SYSTEMIC_PATTERNS}}

## Coverage Completion Roadmap

| Phase | Actions | Blind Spots Closed | Effort |
|-------|---------|-------------------|--------|
| P0 (this sprint) | ... | N | S/M/L |
| P1 (next sprint) | ... | N | S/M/L |
| P2 (this month) | ... | N | S/M/L |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->