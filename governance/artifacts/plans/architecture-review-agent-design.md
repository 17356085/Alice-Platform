# Architecture Review Agent — 架构设计分析

> 状态: 设计完成 | 版本: v1.0 | 日期: 2026-06-16
> 下一步: P0 — 建设 5 个 Review Skill, 验证价值后再升级为 Agent

---

## 当前系统结构速览

```
┌─────────────────────────────────────────────────────────┐
│                    AITest Platform                       │
├─────────────────────────────────────────────────────────┤
│  Test SOP (8 Agent)          Dev SOP (9 Agent)          │
│  ┌──────────────────┐       ┌──────────────────┐       │
│  │ full-sop         │       │ dev-full-sop     │       │
│  │ project→req→     │       │ pm→req→arch→     │       │
│  │ design→auto→     │       │ design→fe/be→    │       │
│  │ exec→bug→report  │       │ review→test→     │       │
│  │ →knowledge       │       │ debug→build      │       │
│  └──────┬───────────┘       └──────┬───────────┘       │
│         │                          │                    │
│         └──────────┬───────────────┘                    │
│                    ▼                                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Governance Layer                                 │  │
│  │ State Auditor │ SOP Auditor │ Cost Auditor       │  │
│  │ Regression Gate │ Event Bus │ Knowledge Agent    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  现有 review-agent: 代码审查 (战术层, Dev SOP Phase 4)   │
│  缺失: 架构审查 (战略层, 元治理)                         │
└─────────────────────────────────────────────────────────┘
```

**关键发现:** 现有 `review-agent` 是**代码审查 Agent** — 审查源码 bug/perf/security/consistency。作用域在 Dev SOP 内部，战术层。缺失的是**架构审查** — 审查系统本身的架构决策、治理覆盖、技术债务、生产就绪度。战略层，元治理。

---

# Part 1: Need Assessment

## 当前评审流程的问题

**问题1: 无标准化。** 每次架构评审依赖人工构造 Prompt。评审维度、深度、输出格式取决于提问者经验和当时上下文。两次评审间无法对比。

**问题2: 无持久化。** Prompt 评审结果存在于聊天记录。无法追溯"上周的架构决策为什么被推翻"。无法版本对比。

**问题3: 无治理集成。** 评审结果不进入 Event Bus。State Auditor/SOP Auditor/Cost Auditor 各自发现问题，但无人回答"这些审计结果加起来意味着什么架构风险"。

**问题4: 无自动化触发。** 评审只在人意识到"该评审了"时发生。无法在架构变更后自动触发。无法在成本异常后自动触发架构评审。

**问题5: 无交叉关联。** StateDrift + CostAnomaly + SOPViolation 同时出现可能意味着架构层面问题。当前无人做交叉分析。

**问题6: 评审疲劳。** 反复写类似评审 Prompt，评审深度逐渐衰减。评审变成"走过场"。

## Agent 化后的收益

| 维度 | Prompt 评审 | Agent 化评审 |
|------|------------|-------------|
| **标准化** | 每次不同 | Skill 版本化, 评审维度固定 |
| **持久化** | 聊天记录 | governance/artifacts/reviews/ |
| **可追溯** | 无 | 版本对比, 趋势分析 |
| **可触发** | 人工 | 事件驱动 / SOP 阶段 / 定时 |
| **可组合** | 一次一个维度 | Supervisor 编排多维度并行 |
| **可度量** | 无法 | KPI 采集, 评审质量评分 |
| **知识沉淀** | 无 | → Knowledge Agent |
| **与审计协同** | 无 | 审计发现问题 → 评审评估影响 |

## 是否值得长期维护

**值得。** 理由:

1. **评审已成为高频活动。** 开发→评审→优化→再次评审是固定模式。高频活动值得工具化。
2. **平台基础设施已就绪。** Agent Runner、Skill Registry、Event Bus、Knowledge Agent 都已存在。增量成本低。
3. **审计层发现的问题需要架构层解读。** StateDrift 告诉你文件不一致。SOPViolation 告诉你流程违规。CostAnomaly 告诉你花钱太多。但没人告诉你"这三个问题加起来说明你的 Agent 拆分粒度有问题"。这是架构评审的价值。
4. **随着 Agent 数量增长 (8+9=17)，系统复杂度在增加。** 没有元治理层，治理本身会失控。

**风险:** 如果评审技能设计不当，可能变成"另一个走过场的 Agent"。关键在于评审技能是否有真正的判断力，还是只是模板填空。

---

# Part 2: Responsibility Boundary

## 核心区分

```
Auditor:     "这个文件不存在"            → 事实检测
Review Agent: "文件不存在说明你的架构边界模糊" → 判断评估
Agent:       "我来修复这个文件"            → 执行动作
```

**State Auditor** — 检测状态一致性。问"状态对吗?"。规则驱动。输出 StateDrift 事件。

**SOP Auditor** — 检测流程合规性。问"流程对吗?"。规则驱动。输出 SOPViolation 事件。

**Cost Auditor** — 检测成本异常。问"花钱对吗?"。统计驱动。输出 CostAnomaly 事件。

**Regression Gate** — 检测质量退化。问"输出变差了吗?"。对比驱动。输出 EvalRegressed 事件。

**Architecture Review Agent** — 评估架构决策。问"这样设计对吗?为什么?"。判断驱动。输出 ReviewReport。

**Knowledge Agent** — 沉淀可复用知识。消费所有事件。不主动发现问题。

**现有 review-agent (Dev)** — 审查代码质量。战术层。问"这段代码对吗?"。

## Responsibility Matrix

| | 发现问题 | 执行治理 | 修复问题 | 升级架构 |
|---|---|---|---|---|
| **State Auditor** | ✅ 状态不一致 | ❌ 仅报告 | ✅ 自动同步 | ❌ |
| **SOP Auditor** | ✅ 流程违规 | ❌ 仅报告 | ❌ | ❌ |
| **Cost Auditor** | ✅ 成本异常 | ❌ 仅报告 | ❌ | ❌ |
| **Regression Gate** | ✅ 质量退化 | ✅ 阻断发布 | ❌ | ❌ |
| **review-agent (Dev)** | ✅ 代码缺陷 | ✅ 代码标准 | ❌ 仅建议 | ❌ |
| **Architecture Review Agent** | ✅ 架构风险 | ✅ 架构标准 | ❌ 仅建议 | ✅ 架构决策 |
| **Knowledge Agent** | ❌ 消费事件 | ❌ | ❌ | ❌ |

**Architecture Review Agent 的独特价值:**
- 唯一能**跨审计维度做综合判断**的组件
- 唯一能**评估架构决策质量**的组件
- 唯一能**提出架构演进建议**的组件

---

# Part 3: Review Capability Model

## Review Skill 设计原则

1. **每个 Skill 一个评审维度** — 可独立执行, 可组合
2. **Skill 输出版本化** — 评审标准可演进
3. **评审深度可配置** — quick (checklist) / standard (analysis) / deep (adversarial)
4. **与现有 Auditor 数据对接** — 评审输入来自审计结果

## Review Skill Registry

### 战略层 (Architecture & Design)

| Skill Name | Purpose | Trigger Condition | Output |
|---|---|---|---|
| `review/architecture-assessment` | 评估系统架构: 组件边界、数据流、耦合度、扩展性 | 新模块上线 / 架构变更 / 定期 (每 sprint) | ARCH_REVIEW.md: 架构评分, 风险清单, 改进建议 |
| `review/tech-debt-inventory` | 盘点技术债务: 硬编码、绕过治理、过时模式 | 定期 (每月) / CostAnomaly 触发 | TECH_DEBT.md: 债务清单, 严重度, 偿还成本估算 |
| `review/component-cohesion` | 评估组件内聚性: Agent 职责边界、Skill 归属、模块划分 | Agent/Skill 新增 / 职责重叠检测 | COHESION_REVIEW.md: 内聚评分, 拆分/合并建议 |

### 治理层 (Governance & Quality)

| Skill Name | Purpose | Trigger Condition | Output |
|---|---|---|---|
| `review/governance-coverage` | 评估治理覆盖: 哪些模块/Agent/Skill 未被治理覆盖 | 定期 (每两周) / 新 Agent 上线 | GOV_COVERAGE.md: 覆盖热力图, 盲区清单 |
| `review/quality-regression-analysis` | 跨版本质量趋势: 综合 State+SOP+Cost 审计结果评估质量走向 | EvalRegressed 触发 / 定期 | QUALITY_TREND.md: 趋势图, 恶化指标, 根因假设 |
| `review/sop-effectiveness` | 评估 SOP 有效性: 流程是否真的提升了质量 | 每个 SOP 周期结束 | SOP_EFFECTIVENESS.md: 通过率, 返工率, 瓶颈识别 |

### 成本与效率层 (Cost & Efficiency)

| Skill Name | Purpose | Trigger Condition | Output |
|---|---|---|---|
| `review/token-efficiency` | 评估 Token 使用效率: 浪费、冗余上下文、可优化 prompt | CostAnomaly 触发 / 定期 | TOKEN_REVIEW.md: 浪费热点, 优化建议, 预估节省 |
| `review/prompt-engineering` | 评审 Prompt 质量: Skill prompt 是否有效、改进空间 | PromptChanged 事件 / 定期 | PROMPT_REVIEW.md: Prompt 评分, 改进建议 |
| `review/model-selection` | 评估模型选择: 合适模型 tier, 降级空间 | 定期 (每月) | MODEL_REVIEW.md: 模型使用分析, 降级建议 |

### 生产就绪层 (Production Readiness)

| Skill Name | Purpose | Trigger Condition | Output |
|---|---|---|---|
| `review/production-readiness` | 评估生产就绪度: 错误处理、可观测性、回滚能力、SLA | 发布前 / 定期 | PROD_READY.md: 就绪度评分, 阻断项, 警告项 |
| `review/observability-gap` | 评估可观测性: 日志、指标、追踪覆盖 | 生产事件后 / 定期 | OBSERVABILITY_REVIEW.md: 盲区, 缺失指标 |
| `review/security-posture` | 评估安全态势: 认证、授权、数据保护、密钥管理 | 定期 (每月) | SECURITY_REVIEW.md: 风险评分, 漏洞清单 |

### 元层 (Meta)

| Skill Name | Purpose | Trigger Condition | Output |
|---|---|---|---|
| `review/skill-health` | 评估 Skill 健康度: 使用频率、成功率、Token 效率、是否该废弃 | 定期 (每月) | SKILL_HEALTH.md: 健康评分, 废弃/合并建议 |
| `review/agent-health` | 评估 Agent 健康度: 执行成功率、平均耗时、Token 消耗趋势 | 定期 (每月) | AGENT_HEALTH.md: 健康评分, 优化建议 |
| `review/memory-quality` | 评估 Memory 质量: 是否过期、矛盾、冗余 | 定期 (每两周) | MEMORY_REVIEW.md: 过期/矛盾/冗余清单 |

**共计 14 个 Review Skill，4 个层级。**

---

# Part 4: Agent Architecture Design

## 单 Agent vs Supervisor + Skills

| | 单 Agent | Supervisor + Skills |
|---|---|---|
| **实现复杂度** | 低 | 中 |
| **评审深度** | 浅 (一次 pass, 上下文限制) | 深 (每个 skill 专注一个维度) |
| **可组合性** | 差 (改评审维度 = 改写整个 prompt) | 好 (增删 skill 即可) |
| **并行性** | 无 | 多个 skill 并行评审 |
| **可复用性** | 差 | 好 (skill 可独立调用) |
| **与现有架构一致性** | 不一致 | 一致 (full-sop 模式) |

**结论: Supervisor + Review Skills。** 理由:

1. 与现有 `full-sop` orchestrator 模式一致 — 降低认知负担
2. 评审维度需要深度 — 每个维度一个 skill 可以更专注
3. 不同触发条件需要不同 skill 组合 — 可组合
4. Skill 可独立版本化、独立测试、独立改进

## Review Workflow (Review Graph)

```
                        ┌─────────────────┐
                        │  Trigger Event  │
                        │  (manual/event/ │
                        │   schedule)     │
                        └───────┬─────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │  Review Context │  ← 收集审计数据、事件、KPI
                        │  Collection     │
                        └───────┬─────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │  Scope Decision │  ← 决定评审范围和深度
                        │  (Supervisor)   │
                        └───────┬─────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │Arch      │    │Governance│    │Cost &    │
        │Review    │    │Review    │    │Efficiency│
        │Skills    │    │Skills    │    │Review    │
        │(并行)    │    │(并行)    │    │Skills    │
        └────┬─────┘    └────┬─────┘    └────┬─────┘
             │               │               │
             └───────────────┼───────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Cross-Review   │  ← 交叉分析: 架构问题是否导致了成本问题?
                    │  Synthesis      │
                    └───────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Risk Assessment│  ← 风险评分 + 优先级排序
                    │  & Prioritization│
                    └───────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Report         │  ← 统一 REVIEW_REPORT.md
                    │  Generation     │
                    └───────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Event Emit &   │  ← → Event Bus
                    │  Knowledge Sync │  ← → Knowledge Agent
                    └─────────────────┘
```

**关键设计决策:**

1. **Review Context Collection** — 自动拉取: 最新审计报告、最近事件、KPI 趋势、变更记录。不依赖人工提供上下文。

2. **Scope Decision** — Supervisor 根据触发条件决定评审范围:
   - 手动触发 → 全维度 deep review
   - CostAnomaly 触发 → Cost + Token Efficiency review
   - EvalRegressed 触发 → Quality + Architecture review
   - 定期触发 → quick checklist review

3. **Cross-Review Synthesis** — 关键步骤。架构问题 → 导致治理盲区 → 导致成本异常。因果链只有交叉分析能发现。

4. **Risk Prioritization** — 按: 影响面 × 发生概率 × 修复成本 排序。

---

# Part 5: Governance Integration

## 与现有组件协同

```
┌────────────────────────────────────────────────────────────┐
│                     Event Bus                              │
│                                                            │
│  StateDrift ──→ Architecture Review Agent ──→              │
│  SOPViolation ─→  "这些审计结果加起来           │              │
│  CostAnomaly ──→   意味着什么?"                │              │
│  EvalRegressed→                                  │              │
│  PromptChanged→                                  │              │
│  AuditCompleted→                                 │              │
│                                                  ▼              │
│  ArchitectureRiskDetected ←── 新事件 ←── Architecture Review   │
│  GovernanceGapDetected    ←── 新事件 ←── Governance Review     │
│  TechnicalDebtDetected    ←── 新事件 ←── Tech Debt Review      │
│  ProductionRiskDetected   ←── 新事件 ←── Production Review     │
│  ReviewCompleted          ←── 新事件 ←── 评审完成              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 协同流程

### 1. 与 State Auditor 协同

- State Auditor 发现 StateDrift → 触发 `review/architecture-assessment` (检查是否是架构边界模糊导致)
- Architecture Review 发现架构问题 → 可能导致 StateDrift 频率变化 → 反馈到 State Auditor 基线

### 2. 与 SOP Auditor 协同

- SOP Auditor 发现 SOPViolation → 触发 `review/sop-effectiveness` (评估 SOP 本身是否合理)
- SOP 有效但被绕过 → 流程问题
- SOP 本身不合理 → 架构问题 → Architecture Review 介入

### 3. 与 Cost Auditor 协同

- Cost Auditor 发现 CostAnomaly → 触发 `review/token-efficiency` + `review/model-selection`
- 评审发现 → Prompt 问题? → `review/prompt-engineering`
- 评审发现 → 架构问题 (Agent 拆分太细)? → `review/architecture-assessment`

### 4. 与 Regression Gate 协同

- Regression Gate 发现 EvalRegressed → 触发 `review/quality-regression-analysis`
- 评审判定 → 真退化还是基线过时 → 决定阻断还是更新基线
- **关键:** Architecture Review Agent 可 override Regression Gate 阻断决策 (如果判断退化是可接受的架构演进代价)

### 5. 与 Prompt Versioning 协同

- PromptChanged 事件 → 触发 `review/prompt-engineering` (验证新版本是否确实更好)
- Architecture Review 可建议 Prompt 版本回滚

### 6. 与 Knowledge Agent 协同

- Architecture Review 输出 → Knowledge Agent 消费 → 沉淀为架构决策记录 (ADR)
- 形成: 问题 → 评审 → 决策 → 结果 → 知识 的闭环

## 新事件定义

```yaml
ArchitectureRiskDetected:
  fields: [module, risk_type, severity, description, recommendation]
  triggered_by: review/architecture-assessment, review/component-cohesion
  subscribers: [Knowledge Agent, SOP Auditor (重新评估流程)]

GovernanceGapDetected:
  fields: [gap_type, affected_modules, risk_level, recommendation]
  triggered_by: review/governance-coverage
  subscribers: [Knowledge Agent, 人工审核]

TechnicalDebtDetected:
  fields: [debt_type, location, severity, estimated_cost, recommendation]
  triggered_by: review/tech-debt-inventory
  subscribers: [Knowledge Agent, PM Agent (纳入 sprint 计划)]

ProductionRiskDetected:
  fields: [risk_type, severity, is_blocker, recommendation]
  triggered_by: review/production-readiness, review/security-posture
  subscribers: [Knowledge Agent, Regression Gate (可能阻断发布)]

ReviewCompleted:
  fields: [review_type, module, overall_score, critical_count, warning_count, report_path]
  triggered_by: 任何 review skill 完成
  subscribers: [Knowledge Agent, KPI Collector]
```

---

# Part 6: Output Standard

## REVIEW_REPORT.md 标准结构

```markdown
# Review Report: {review_type}

---
report_id: REVIEW-{timestamp}-{uuid8}
review_type: architecture | governance | quality | cost | production | comprehensive
module: {module_name} | platform-wide
trigger: manual | scheduled | event:{event_type}
depth: quick | standard | deep
reviewer: architecture-review-agent v{version}
created: {ISO8601}
---

## Executive Summary

**Overall Score:** {score}/100 ({grade})
**Critical Issues:** {count}
**Warnings:** {count}
**Recommendations:** {count}

{one-paragraph summary of key findings}

## Scope & Context

- **Review Scope:** {what was reviewed}
- **Review Depth:** {quick|standard|deep}
- **Data Sources:** {audit reports, events, KPIs used}
- **Baseline:** {previous review ID or "initial review"}

## Findings

### Critical (must fix)

| ID | Category | Finding | Impact | Recommendation | Effort |
|----|----------|---------|--------|----------------|--------|
| C01 | {category} | {finding} | {impact} | {recommendation} | {S/M/L} |

### Warnings (should fix)

| ID | Category | Finding | Impact | Recommendation | Effort |
|----|----------|---------|--------|----------------|--------|

### Observations (nice to fix)

| ID | Category | Finding | Recommendation |
|----|----------|---------|----------------|

## Dimension Scores

| Dimension | Score | Trend | Previous |
|-----------|-------|-------|----------|
| Architecture | 72/100 | ↓ | 78 |
| Governance | 85/100 | → | 85 |
| Cost Efficiency | 60/100 | ↓ | 68 |
| Quality | 75/100 | ↑ | 70 |
| Production Readiness | 68/100 | → | 68 |

## Cross-Dimension Analysis

{causal chain analysis: how findings in one dimension affect others}

## Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation |
|------|-----------|--------|----------|------------|
| {risk} | {H/M/L} | {H/M/L} | {P0/P1/P2} | {mitigation} |

## Action Items

| Priority | Action | Owner | Deadline | Effort |
|----------|--------|-------|----------|--------|
| P0 | {action} | {owner} | {date} | {S/M/L} |

## Trend Analysis

{comparison with previous reviews, trend direction, acceleration/deceleration}

## Appendix

- **Audit Reports Referenced:** {links}
- **Events Analyzed:** {count} events from {date_range}
- **Skills Executed:** {list of review skills used}
- **Raw Findings:** {link to detailed findings file}
```

---

# Part 7: Evolution Roadmap

## 评估: 当前项目最适合的阶段

**当前状态判断:**
- 测试基线 62.4% (还在修 bug)
- 8+9=17 Agent 已定义
- 治理层 (3 Auditor + Regression Gate + Event Bus) 已就绪
- Governance validation sprint 发现 16 个真实治理问题
- 项目在从"建设期"向"稳定期"过渡

## P0: Review Skills (现在) ← 推荐立即启动

**内容:** 将评审能力以 Skill 形式落地。不建 Agent。人工通过 Prompt 调用。

**具体:**
1. 选 5 个最痛的评审维度先做 Skill prompt
2. 定义每个 Skill 的评审标准、输出格式
3. 人工在需要时调用: `AgentLoop('arch-agent', module='x').run_skill('review/architecture-assessment')`
4. 收集使用反馈, 迭代 Skill prompt

**优先建设的 5 个 Skill:**
1. `review/architecture-assessment` — 最核心
2. `review/token-efficiency` — 成本直接可见
3. `review/governance-coverage` — 治理盲区是已知痛点
4. `review/prompt-engineering` — Prompt 质量直接影响所有 Agent
5. `review/production-readiness` — 发布前必需

**优点:** 零新增基础设施。立即可用。可验证评审是否真的有价值。

**缺点:** 无自动化触发。无交叉分析。每次评审需人工判断用哪个 skill。

## P1: Architecture Review Agent (P0 验证后, 预计 2-4 周)

**前提:** P0 的 5 个 Skill 已验证有效, 评审确实产生可行动的发现。

**内容:**
1. 定义 `architecture-review-agent` 到 `agent-definitions-dev.yaml`
2. 建设 Review Graph (Supervisor + Skill composition)
3. 接入 Event Bus (事件触发评审)
4. 建设交叉分析能力 (Cross-Review Synthesis)
5. 接入 Knowledge Agent (ADR 沉淀)
6. 扩展至全部 14 个 Review Skill

**标志:** 从"人决定评审什么"到"系统建议评审什么"。

## P2: Meta Governance System (P1 稳定后, 预计 1-2 月)

**前提:** P1 Agent 稳定运行, 评审覆盖足够模块和维度。

**内容:**
1. 评审结果自动驱动架构演进决策
2. 自动检测架构腐化并建议重构
3. 评审标准自我进化 (评审 Agent 评审自己的评审标准)
4. 与外部系统集成 (CI/CD, 监控, 告警)

**标志:** 从"系统建议评审什么"到"系统自主治理架构质量"。

## 推荐路径

```
Now ──────→ 2-4 weeks ──────→ 1-2 months ──────→ 3+ months
P0: Skills    P0→P1: Agent     P1→P2: Meta       P2: Self-evolving
5 review      Supervisor +     Cross-module      Auto-governance
skills        14 skills        pattern detection architecture
```

**当前立即做 P0。** 原因:

1. 项目治理基础 (Auditor + Event Bus) 刚建好, 需时间验证稳定性
2. P0 的 Skill 可直接验证"评审是否真的有价值" — 如果 Skill 评审产生不了可行动的发现, Agent 化也无意义
3. P0 的 Skill 可立即帮助当前问题 (Governance validation sprint 发现的 16 个问题)
4. 遵循项目演进模式: 先 Skill → 再 Agent → 再 System

---

# Final Verdict

## Architecture Review Agent 是否值得建设?

**值得。** 但正确顺序: **先建 Skill, 验证价值, 再升级为 Agent。**

理由:
1. **评审是高频活动** — 值得工具化
2. **基础设施已就绪** — 增量成本低
3. **审计层发现需要架构层解读** — 填补治理空白
4. **Agent 数量增长需要元治理** — 否则治理本身会失控

## 当前最小可行方案 (MVP)

**范围:** P0 — 5 个 Review Skill

**交付物:**
1. `governance/skills-dev/review/` 目录, 含 5 个 Skill prompt:
   - `architecture-assessment.md`
   - `token-efficiency.md`
   - `governance-coverage.md`
   - `prompt-engineering.md`
   - `production-readiness.md`
2. `governance/skills-dev/skill-registry-dev.yaml` 新增 review category
3. `REVIEW_REPORT.md` 模板
4. 4 个新事件类型注册到 `event_bus.py`

**不做的:**
- 不建 Architecture Review Agent 定义
- 不建 Review Graph
- 不做自动化触发
- 不做交叉分析

**验证标准:**
- 每个 Skill 至少产生 3 个可行动的发现
- 评审结果被实际用于决策
- 评审时间 < 人工评审时间的 50%

**验证通过后 → P1 Agent 化。**

---

## 在 AITest Platform 中的位置

```
┌──────────────────────────────────────────────────────────┐
│                   Meta Governance Layer                   │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Architecture Review Agent (P1)                    │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Review Skills (P0)                          │  │  │
│  │  │  architecture | governance | cost | quality  │  │  │
│  │  │  production | prompt | token | security      │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
│                         ↑↓                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Governance Layer (已有)                           │  │
│  │  State Auditor | SOP Auditor | Cost Auditor        │  │
│  │  Regression Gate | Event Bus | Knowledge Agent     │  │
│  └────────────────────────────────────────────────────┘  │
│                         ↑↓                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Execution Layer (已有)                            │  │
│  │  Test SOP (8 Agent) | Dev SOP (9 Agent)            │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

Architecture Review Agent 是 **Meta Governance Layer** — 治理之上的一层。不直接执行治理，评估治理的有效性。不直接写代码，评估代码的架构质量。是系统的"自我意识"。
