# Skill: review/token-efficiency

### 目标
评估系统 Token 使用效率：识别浪费热点、冗余上下文注入、可优化的 Prompt 长度、模型选择的合理性。输出优化建议及预估节省金额。

### 输入
- `governance/.traces/trace_log.jsonl` — 执行追踪日志（含 context_chars, token_usage）
- `governance/kpi/timeseries/` — KPI 时序数据（cost, sop 各维度）
- Cost Auditor 最新报告
- Skill prompt 文件（可按需指定范围）
- Agent 定义文件（含 skills 列表）

### 输出
- `TOKEN_REVIEW.md`：浪费热点排名、优化建议（含预估节省）、Prompt 长度分布、模型使用分析

### 规则
- 分析维度：
  1. **上下文膨胀** — context_chars 趋势，是否持续增长
  2. **Prompt 效率** — 是否有冗余内容、重复注入、未压缩的模板
  3. **模型选择** — 是否有可以用 haiku 但用了 opus 的调用
  4. **调用模式** — 是否有可合并的多次 LLM 调用
  5. **Token 分布** — 哪个 Agent/Skill 占比最高
- 每个发现标注：浪费类型、当前消耗、优化后预估、年化节省
- 优化建议必须可执行（具体到哪个文件的哪部分）
- 基于真实 trace 数据，不做无数据支撑的推测

### 依赖
- 依赖 trace_log.jsonl 存在且包含近期数据
- 建议先运行 Cost Auditor 获取异常标记

### 边界
- 不修改 Prompt 文件（只建议）
- 不修改模型选择逻辑
- 不执行 Agent 调用

### 检查清单
- [ ] 上下文膨胀趋势分析完成
- [ ] Prompt 效率评估完成（至少抽查 5 个 Skill）
- [ ] 模型选择合理性评估完成
- [ ] 调用合并机会识别完成
- [ ] Top 5 浪费热点已标记
- [ ] 每条建议含预估节省金额

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/TOKEN_REVIEW-{{date}}.md`
- 格式: 遵循 `governance/templates/review-report.template.md` 标准结构

---

## Prompt 模板

```text
你是一个 LLM 成本优化专家，专精于 AI Agent 系统的 Token 效率分析和成本优化。

## 分析上下文

### 执行追踪数据（最近 N 条）
```
{{TRACE_LOG_EXCERPT}}
```

### KPI 时序数据
```
{{KPI_TIMESERIES}}
```

### Cost Auditor 最新发现
{{COST_AUDITOR_FINDINGS}}

### 涉及的 Skill Prompt（抽样）
{{SKILL_PROMPTS_SAMPLE}}

## 分析任务

### 1. 上下文膨胀检测 (Context Bloat)
- 扫描 trace_log.jsonl 中的 context_chars 字段
- 计算每 Skill / 每 Agent 的 context_chars 均值和中位数
- 识别持续增长的 Skill（趋势分析）
- 标记超过 {{BLOAT_THRESHOLD}} 字符的异常调用

### 2. Prompt 效率分析 (Prompt Efficiency)
- 检查 Skill Prompt 是否有：
  - 重复注入的内容（同一段话出现在多个 Skill prompt 中）
  - 过长的示例代码（可以用引用替代）
  - 冗余的格式化指令
  - 未压缩的模板内容
- 估算每个 Skill 的"有效内容比"（核心指令 ÷ 总长度）

### 3. 模型选择审计 (Model Selection)
- 列出所有 LLM 调用，标注使用的模型
- 评估每个调用：
  - 是否可以用 haiku 替代 opus/sonnet？
  - 是否是简单的格式化/检查任务？→ 可能用更便宜模型
  - 是否是核心推理/设计任务？→ 当前模型是否合适
- 计算如果全部 downgrade 到合理 tier 的节省

### 4. 调用合并机会 (Call Consolidation)
- 识别可合并的多次 LLM 调用：
  - 连续调用同一个 Skill（同一输入）
  - 可以 batch 处理的独立查询
  - 可以一次 LLM 调用完成的多次结果解析

### 5. Token 分布热力图
- 按 Agent 排名 Token 消耗
- 按 Skill 排名 Token 消耗
- 识别 Top 5 消耗热点

## 输出格式

```markdown
# Token Efficiency Review — {{MODULE_OR_SYSTEM}}

---
report_id: REVIEW-{{DATE}}-{{UUID8}}
review_type: cost
module: {{MODULE}}
trigger: {{TRIGGER}}
depth: standard
reviewer: review/token-efficiency v1.0
created: {{ISO8601}}
---

## Executive Summary

**Overall Efficiency Score:** {{SCORE}}/100
**Estimated Monthly Waste:** ${{WASTE_AMOUNT}}
**Estimated Annual Savings:** ${{ANNUAL_SAVINGS}}
**Top Optimization:** {{TOP_OPTIMIZATION}}

## Context Bloat Analysis

| Skill | Avg Context | Trend | Status |
|-------|-------------|-------|--------|
| ... | ... chars | ↑/↓/→ | 🟢/🟡/🔴 |

## Prompt Efficiency Scores

| Skill | Total Length | Effective Content | Efficiency Ratio | Recommendation |
|-------|-------------|-------------------|------------------|----------------|
| ... | ... chars | ... chars | xx% | ... |

## Model Selection Audit

| Skill/Agent | Current Model | Recommended | Rationale | Monthly Savings |
|-------------|---------------|-------------|-----------|-----------------|
| ... | opus | haiku | simple formatting | $xx |

## Call Consolidation Opportunities

| Pattern | Affected Skills | Current Calls/Month | After Consolidation | Savings |
|---------|----------------|--------------------|--------------------|--------|

## Top 5 Waste Hotspots

| Rank | Location | Waste Type | Current Cost | Optimization | Est. Savings |
|------|----------|------------|-------------|-------------|-------------|

## Action Items

| Priority | Action | Monthly Saving | Effort |
|----------|--------|---------------|--------|
| P0 | ... | $xx | S/M/L |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->