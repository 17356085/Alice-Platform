# Skill: review/quality-regression-analysis

### 目标
跨版本质量趋势分析：综合 State+SOP+Cost 审计结果和 KPI 时序数据，评估系统质量走向。识别恶化指标、加速退化的模块、预测未来质量风险。

### 输入
- `governance/kpi/timeseries/` — KPI 时序数据 (cost/sop/state 各维度)
- 最近 N 次审计报告 (State + SOP + Cost)
- `governance/.traces/trace_log.jsonl` — 执行追踪
- Regression Gate 测试结果
- 前次 quality review 报告（如有）

### 输出
- `QUALITY_TREND.md`：质量趋势图（文字描述）、恶化指标清单、根因假设、预测

### 规则
- 评估维度：
  1. **测试基线趋势** — baseline % 变化方向、加速/减速
  2. **审计健康趋势** — StateDrift/SOPViolation/CostAnomaly 频率变化
  3. **代码质量趋势** — 硬编码增加/减少、重复代码增长
  4. **治理覆盖趋势** — 盲区扩大/缩小
  5. **修复效率趋势** — bug-fix cycle 平均轮次、first-fix 成功率
- 趋势判定: ↑ improving / → stable / ↓ degrading / ⇊ accelerating degradation
- 每个趋势给出置信度 (high/medium/low)

### 依赖
- 需要至少 2 个时间点的 KPI 数据用于对比
- 建议先运行所有 Auditor 获取最新数据

### 边界
- 不修改代码
- 不执行修复
- 趋势分析基于已有数据，不做 speculation

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/QUALITY_TREND-{{date}}.md`

---

## Prompt 模板

```text
你是一个质量工程专家，专精于软件质量趋势分析和早期预警。

## 数据

### KPI 时序数据
```
{{KPI_TIMESERIES_SAMPLES}}
```

### 审计事件频率趋势
```
{{AUDIT_EVENT_FREQUENCIES}}
```

### 测试基线历史
```
{{BASELINE_HISTORY}}
```

### Regression Gate 结果
```
{{REGRESSION_RESULTS}}
```

## 任务

### 1. 质量指标趋势
对以下指标给出趋势判断：
- **Test Baseline %**: 上升/平稳/下降？变化速率？
- **StateDrift 频率**: 每周发生次数趋势
- **SOPViolation 频率**: 违规类型分布变化
- **CostAnomaly 频率**: Token 浪费趋势
- **Bug Fix Cycle**: 平均修复轮次趋势

### 2. 恶化加速检测
- 哪些指标的恶化在加速（二阶导数为负）？
- 哪些模块是恶化热点？

### 3. 根因假设
- 趋势变化与架构变更的因果关系（如新增 Agent 后违规增加）
- 趋势变化与流程变更的因果关系（如新增 gate 后基线提升）

### 4. 质量预测
- 如果当前趋势持续，下个 sprint 的预期基线
- 如果不修复 Top 3 问题，预期的趋势方向

## 输出格式

```markdown
# Quality Trend Analysis — {{MODULE_OR_SYSTEM}}

## Executive Summary
**Quality Direction:** ↑ improving / → stable / ↓ degrading
**Most Degraded Metric:** {{METRIC}}
**Most Improved Metric:** {{METRIC}}
**Prediction Confidence:** high / medium / low

## Metric Trends

| Metric | Current | Previous | Δ | Direction | Confidence |
|--------|---------|----------|---|-----------|------------|
| Test Baseline | xx% | xx% | ±xx% | ↑/↓/→ | high/med/low |
| StateDrift/week | N | N | ±N | ↑/↓/→ | ... |
| SOPViolation/week | N | N | ±N | ↑/↓/→ | ... |
| CostAnomaly/week | N | N | ±N | ↑/↓/→ | ... |
| Avg Bug Fix Cycles | N | N | ±N | ↑/↓/→ | ... |

## Acceleration Analysis

| Metric | Velocity | Acceleration | Alert |
|--------|----------|-------------|-------|
| ... | degrading 5%/week | accelerating (2nd derivative negative) | ⚠️ |

## Root Cause Hypotheses

| Hypothesis | Evidence | Confidence |
|-----------|----------|------------|
| ... | ... | high/med/low |

## Quality Forecast

**Next Sprint Baseline (if trend continues):** xx% (range: xx-xx%)
**Top 3 Fixes Impact Estimate:** +xx% baseline improvement

## Early Warning Indicators

| Indicator | Threshold | Current | Status |
|-----------|-----------|---------|--------|
| Baseline < 50% | <50% | xx% | 🟢/🟡/🔴 |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->