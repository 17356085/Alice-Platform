# Skill: review/sop-effectiveness

### 目标
评估 SOP 流程有效性：SOP 是否真的提升了质量？通过率、返工率、瓶颈识别。回答"这个流程值得继续吗"而非"流程合规吗"。

### 输入
- SOP Auditor 报告（G-Check 门禁通过率、L-Check 循环统计）
- `governance/.traces/trace_log.jsonl` — 执行追踪
- KPI 时序数据
- Bug fix 统计数据

### 输出
- `SOP_EFFECTIVENESS.md`：SOP 有效性评分、瓶颈识别、流程改进建议

### 规则
- 评估维度：
  1. **门禁有效性** — gate pass 后下游失败率。如果 gate 形同虚设，SOP 无效
  2. **循环效率** — bug fix 每轮通过率、平均修复到通过的轮次
  3. **瓶颈识别** — 哪个 phase 耗时最长？哪个 phase 返工最多？
  4. **跳过率合理性** — skip 后的 phase 是否真的不需要？skip 后失败率是否更高？
  5. **对比有效性** — 有 SOP 的阶段 vs 无 SOP 的阶段，质量指标差异
- 有效性 ≠ 合规性。一个合规的 SOP 可能完全无效

### 依赖
- 需要 SOP Auditor 的最新报告
- 需要足够的执行数据（至少 3 个完整 SOP 周期）

### 边界
- 不修改 SOP 流程
- 不做合规检查（那是 SOP Auditor 的职责）
- 只评估是否有效，不评估是否合理

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/SOP_EFFECTIVENESS-{{date}}.md`

---

## Prompt 模板

```text
你是一个流程工程专家，专精于评估开发流程的有效性（而非合规性）。

## 数据

### SOP 统计
{{SOP_STATISTICS}}

### Gate 通过率 vs 下游失败率
{{GATE_DATA}}

### Bug Fix 循环统计
{{BUG_FIX_STATS}}

### Phase 耗时分布
{{PHASE_DURATION_DATA}}

## 任务

### 1. 门禁有效性
- 每个 gate 的通过率 vs 下游 phase 的失败率
- 高通过率 + 高下游失败率 = gate 无效
- 低通过率 + 低下游失败率 = gate 可能过严

### 2. 流程瓶颈
- 哪个 phase 是瓶颈（耗时最长 / 返工最多）？
- 瓶颈是 phase 设计问题还是资源问题？

### 3. 循环效率
- Bug fix 平均几轮修好？首次修复成功率？
- 循环次数趋势：在变好还是变差？

### 4. 跳过合理性
- skip 的阶段在整体流程中是否真的非必需？
- skip 后的下游失败率 vs 不 skip 时的失败率

### 5. 流程 ROI
- 对比：有 SOP 阶段的产出质量 vs 无 SOP 阶段
- SOP 的开销（额外时间/Token）是否值得？

## 输出格式

```markdown
# SOP Effectiveness Review — {{MODULE}}

## Executive Summary
**SOP Effectiveness Score:** {{SCORE}}/100
**Is SOP Worth It?:** Yes / Conditional / No
**Biggest Bottleneck:** {{PHASE_NAME}}
**Most Ineffective Gate:** {{GATE_NAME}}

## Gate Effectiveness

| Gate | Pass Rate | Downstream Fail Rate | Effective? |
|------|-----------|---------------------|------------|
| ... | xx% | xx% | ✅/🟡/❌ |

## Bottleneck Analysis

| Phase | Avg Duration | Rework Rate | Bottleneck Score |
|-------|-------------|------------|-----------------|
| ... | xx min | xx% | xx/100 |

## Bug Fix Cycle Health

| Metric | Current | Trend | Assessment |
|--------|---------|-------|------------|
| Avg Cycles to Fix | x.x | ↑/↓/→ | ... |
| First-Fix Rate | xx% | ... | ... |
| Exhaustion Rate | xx% | ... | ... |

## SOP ROI Assessment

| Aspect | With SOP | Without SOP | Δ |
|--------|----------|------------|---|
| Quality | ... | ... | ... |
| Speed | ... | ... | ... |
| Cost | ... | ... | ... |

## Recommendations

| Priority | Change | Expected Impact |
|----------|--------|----------------|
| P0 | Remove ineffective gate X | -xx% overhead, no quality loss |
| P1 | Fix bottleneck Y | +xx% throughput |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->