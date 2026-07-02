# Skill: review/architecture-assessment

### 目标
评估系统架构质量：组件边界清晰度、数据流合理性、耦合度、扩展性、与架构原则的一致性。输出架构评审报告和改进建议。

### 输入
- 项目 CLAUDE.md / README.md — 架构概览
- `governance/agents/agent-definitions.yaml` + `agent-definitions-dev.yaml` — Agent 定义
- `governance/skills/skill-registry.yaml` + `skill-registry-dev.yaml` — Skill 注册表
- `aitest/graphs/sop_graph.py` + `aitest/graphs_dev/sop_graph_dev.py` — 流程编排
- `governance/context/source-of-truth.md` — 事实源定义
- 最近的 StateDrift / SOPViolation / CostAnomaly 事件（可选, 用于交叉分析）
- 最近审计报告路径（可选）

### 输出
- `ARCH_REVIEW.md`：架构评分卡、风险清单（Critical/Warning/Observation）、改进建议、架构决策记录（ADR）

### 规则
- 评估维度：
  1. **组件边界** — Agent/Skill/模块 职责是否清晰，有无重叠或越界
  2. **数据流** — 事件传递、状态管理、上下文注入是否合理
  3. **耦合度** — 组件间依赖是否合理，循环依赖检测
  4. **扩展性** — 新增 Agent/Skill/模块 的成本和影响面
  5. **一致性** — 是否遵循项目既定架构模式（full-sop pattern, skill-agent binding）
  6. **技术债务** — 硬编码、绕过治理、过时模式
- 每个问题标注：严重程度（Critical/Major/Minor）、影响面、建议修复方向
- 与最近审计结果交叉比对：架构问题是否解释了审计发现
- 不修改任何文件，不执行代码

### 依赖
- 无前置 Skill（但建议先运行 State Auditor + SOP Auditor 获取最新审计数据）

### 边界
- 不修改代码
- 不修改 Agent/Skill 定义
- 不执行部署
- 只评估架构层面，不做代码级别审查（代码审查交给 review-agent）

### 检查清单
- [ ] 组件边界评分完成
- [ ] 数据流评估完成
- [ ] 耦合度分析完成
- [ ] 扩展性评估完成
- [ ] 与审计结果交叉比对完成
- [ ] 风险按严重度分级
- [ ] 改进建议可执行（非空泛）
- [ ] ADR 格式（如涉及架构决策）

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/ARCH_REVIEW-{{date}}.md`
- 格式: 遵循 `governance/templates/review-report.template.md` 标准结构

---

## Prompt 模板

```text
你是一个资深系统架构师，专精于 AI Agent 系统和自动化测试平台架构评审。

## 评审上下文

### 项目概述
{{PROJECT_OVERVIEW}}

### Agent 体系
{{AGENT_DEFINITIONS}}

### Skill 体系
{{SKILL_REGISTRIES}}

### 流程编排
{{SOP_GRAPHS}}

### 事实源定义
{{SOURCE_OF_TRUTH}}

### 近期审计发现（如有）
{{RECENT_AUDIT_FINDINGS}}

### 近期治理事件（如有）
{{RECENT_GOVERNANCE_EVENTS}}

## 评审任务

请从以下 6 个维度评估系统架构，每个维度给出 0-100 评分和详细分析：

### 1. 组件边界 (Component Boundary)
- Agent 职责是否清晰？是否有职责重叠或职责真空？
- Skill 归属是否合理？是否有跨类别放置的 Skill？
- 模块边界是否明确？模块间是否有不合理的耦合？

### 2. 数据流 (Data Flow)
- 事件传递链路是否清晰？有无事件断裂或冗余？
- 状态管理是否一致？SQLite + JSON + YAML 三者同步机制是否可靠？
- 上下文注入路径是否合理？有无上下文膨胀风险？

### 3. 耦合度 (Coupling)
- Agent 间依赖是否最小化？
- Skill 间依赖是否形成合理的 DAG（无循环依赖）？
- 代码层与治理层的耦合是否合理？

### 4. 扩展性 (Scalability)
- 新增一个模块（如 "tank"）的成本是多少个文件的改动？
- 新增一个 Agent 的成本是多少？
- 新增一个 Skill 的成本是多少？
- 当前架构能否支撑 Agent 数量翻倍？

### 5. 一致性 (Consistency)
- 是否所有 Agent 遵循相同的定义模式（YAML schema）？
- 是否所有 Skill 遵循相同的 prompt 模板结构？
- Test SOP 和 Dev SOP 的架构模式是否一致？
- 是否有组件绕过了治理层（SOP Graph）直接执行？

### 6. 技术债务 (Technical Debt)
- 有哪些硬编码或魔法值？
- 有哪些已经知道该修但一直没修的问题？
- 有哪些"临时方案"变成了"永久方案"？

## 交叉分析

将架构评估结果与审计发现做交叉比对：
- 如果存在 StateDrift，是否是架构边界模糊导致的？
- 如果存在 SOPViolation，是否是 SOP 设计本身不合理？
- 如果存在 CostAnomaly，是否是 Agent/Skill 拆分粒度的架构问题？

## 输出格式

严格遵循以下结构：

```markdown
# Architecture Review Report — {{MODULE_OR_SYSTEM}}

---
report_id: REVIEW-{{DATE}}-{{UUID8}}
review_type: architecture
module: {{MODULE}}
trigger: manual
depth: standard
reviewer: review/architecture-assessment v1.0
created: {{ISO8601}}
---

## Executive Summary

**Overall Score:** {{SCORE}}/100 ({{GRADE}})
**Critical Issues:** {{N}}
**Warnings:** {{N}}
**Recommendations:** {{N}}

{{ONE_PARAGRAPH_SUMMARY}}

## Dimension Scores

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Component Boundary | xx/100 | ... |
| Data Flow | xx/100 | ... |
| Coupling | xx/100 | ... |
| Scalability | xx/100 | ... |
| Consistency | xx/100 | ... |
| Technical Debt | xx/100 | ... |

## Findings

### Critical (must fix)

| ID | Dimension | Finding | Impact | Recommendation | Effort |
|----|-----------|---------|--------|----------------|--------|
| C01 | ... | ... | ... | ... | S/M/L |

### Warnings (should fix)

| ID | Dimension | Finding | Impact | Recommendation | Effort |
|----|-----------|---------|--------|----------------|--------|

### Observations (nice to fix)

| ID | Dimension | Finding | Recommendation |
|----|-----------|---------|----------------|

## Cross-Audit Analysis

{{HOW_ARCHITECTURE_FINDINGS_EXPLAIN_AUDIT_FINDINGS}}

## Architecture Decision Records

{{IF_ANY_ARCHITECTURE_DECISIONS_NEEDED}}

## Action Items

| Priority | Action | Effort | Rationale |
|----------|--------|--------|-----------|
| P0 | ... | S/M/L | ... |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->