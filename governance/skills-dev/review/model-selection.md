# Skill: review/model-selection

### 目标
评估 LLM 模型选择的合理性：每个 Agent/Skill 的模型 tier 是否合适？是否有降级（downgrade）空间？产出模型使用优化建议及成本影响。

### 输入
- Trace log (`governance/.traces/trace_log.jsonl`) — 包含 model、token_usage 字段
- KPI 成本时序数据
- Agent 定义文件（了解每个 Skill 的复杂度）
- Token Efficiency Review（如有）

### 输出
- `MODEL_REVIEW.md`：模型使用分布、降级建议（含节省估算）、风险评估

### 规则
- 评估维度：
  1. **模型使用分布** — 每个 model 的调用次数和 token 占比
  2. **降级候选** — 哪些调用可以用 cheaper model 而不显著降低质量
  3. **升级需求** — 哪些调用因为用了 cheap model 导致质量不足（高 retry 率）
  4. **路由策略** — 是否应根据任务复杂度动态路由到不同 model
  5. **成本效益** — 每个 model 的 cost-per-successful-call
- 降级建议标注：当前 model → 建议 model → 预估节省 → 风险等级
- 风险等级: low（简单格式化）/ medium（标准分析）/ high（核心推理）

### 依赖
- 需要 trace_log.jsonl 包含 model 字段
- 建议先运行 token-efficiency review

### 边界
- 不修改模型配置
- 不执行模型切换
- 评估基于执行数据，不做纯推测

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/MODEL_REVIEW-{{date}}.md`

---

## Prompt 模板

```text
你是一个 LLM 成本优化和模型选择专家。

## 数据

### 模型使用统计
```
{{MODEL_USAGE_STATS}}
```

### 每 Skill 的 Token 消耗和成功率
```
{{SKILL_TOKEN_STATS}}
```

### 参考模型 Tier 和定价
- Tier 1 (cheapest): haiku — 简单格式化、分类、提取
- Tier 2 (balanced): sonnet — 标准分析、代码审查
- Tier 3 (expensive): opus — 复杂架构设计、核心推理
- Current default: deepseek-v4-flash

## 任务

### 1. 模型使用分布
分析每个 model 的使用占比和成本占比

### 2. 降级候选识别
对每个 Skill/Agent 调用，评估：
- 任务复杂度是否匹配当前 model tier？
- 是否可以降级到 cheaper model 而不显著影响质量？
- 降级的预估节省

### 3. 升级需求识别
- 是否有 cheap model 调用导致高 retry 率？
- 是否有因为 model 能力不足导致的已知质量问题？

### 4. 路由策略建议
- 是否应该根据任务类型动态选择 model？
- 建议的路由规则

## 输出格式

```markdown
# Model Selection Review — {{MODULE_OR_SYSTEM}}

## Executive Summary
**Estimated Monthly Savings from Optimization:** $xx
**Safe Downgrades:** {{N}} | **Required Upgrades:** {{N}} | **Model Routing Suggestions:** {{N}}

## Model Usage Distribution

| Model | Calls | Input Tokens | Output Tokens | Cost | % of Total |
|-------|-------|-------------|---------------|------|-----------|
| deepseek-v4-flash | N | N | N | $xx | xx% |

## Downgrade Candidates

| Skill/Agent | Current Model | Suggested | Rationale | Monthly Savings | Risk |
|-------------|---------------|-----------|-----------|----------------|------|
| ... | opus | haiku | simple formatting task | $xx | low |

## Upgrade Requirements

| Skill/Agent | Current Model | Suggested | Rationale | Cost Increase |
|-------------|---------------|-----------|-----------|---------------|
| ... | haiku | sonnet | high retry rate (xx%) | $xx |

## Model Routing Strategy

| Task Type | Complexity | Recommended Model | Rationale |
|-----------|-----------|------------------|-----------|
| Formatting/Extraction | simple | haiku | lowest cost |
| Code review | medium | sonnet | balanced |
| Architecture design | complex | opus | needs deep reasoning |

## Action Items

| Priority | Action | Monthly Saving | Effort |
|----------|--------|---------------|--------|
| P0 | ... | $xx | S |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->