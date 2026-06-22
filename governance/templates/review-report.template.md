# REVIEW_REPORT Template

> 使用方式: 复制本模板 → 替换所有 `{{ }}` 占位符为实际内容 → 删除 `<!-- -->` 注释。
> 适用: architecture | governance | quality | cost | production | comprehensive 六种评审类型。

## 元信息

---
report_id: REVIEW-{{DATE}}-{{UUID8}}
review_type: <!-- architecture | governance | quality | cost | production | comprehensive -->
module: <!-- module_name | platform-wide -->
trigger: <!-- manual | scheduled | event:EventType -->
depth: <!-- quick | standard | deep -->
reviewer: <!-- review/skill-name v1.0 -->
created: {{ISO8601}}
---

## Executive Summary

**Overall Score:** {{SCORE}}/100 ({{GRADE}})
<!-- GRADE: A(90+) B(75-89) C(60-74) D(40-59) F(<40) -->
**Critical Issues:** {{N}}
**Warnings:** {{N}}
**Recommendations:** {{N}}

<!-- One-paragraph summary of key findings. 3-5 sentences. -->

## Scope & Context

- **Review Scope:** <!-- what was reviewed — module, component, or entire system -->
- **Review Depth:** <!-- quick | standard | deep -->
- **Data Sources:** <!-- audit reports, event logs, KPI timeseries, code paths used -->
- **Baseline:** <!-- previous review report_id or "initial review" -->

## Dimension Scores

<!-- Customize dimensions per review_type -->
| Dimension | Score | Trend | Previous |
|-----------|-------|-------|----------|
| <!-- Dimension 1 --> | xx/100 | ↑/↓/→ | xx |
| <!-- Dimension 2 --> | xx/100 | ↑/↓/→ | N/A |

## Findings

### Critical (must fix)

| ID | Category | Finding | Impact | Recommendation | Effort |
|----|----------|---------|--------|----------------|--------|
| C01 | <!-- category --> | <!-- finding --> | <!-- impact --> | <!-- recommendation --> | S/M/L |

### Warnings (should fix)

| ID | Category | Finding | Impact | Recommendation | Effort |
|----|----------|---------|--------|----------------|--------|

### Observations (nice to fix)

| ID | Category | Finding | Recommendation |
|----|----------|---------|----------------|

## Cross-Dimension Analysis

<!-- Causal chain: how findings in one dimension affect others.
     Example: "Architecture boundary blur (Architecture C01) → modules bypass SOP Graph → SOPViolation spike → CostAnomaly from redundant executions" -->

## Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation |
|------|-----------|--------|----------|------------|
| <!-- risk description --> | H/M/L | H/M/L | P0/P1/P2 | <!-- mitigation --> |

## Action Items

| Priority | Action | Owner | Deadline | Effort |
|----------|--------|-------|----------|--------|
| P0 | <!-- action --> | <!-- owner --> | {{DATE}} | S/M/L |
| P1 | <!-- action --> | <!-- owner --> | {{DATE}} | S/M/L |

## Trend Analysis

<!-- Comparison with previous reviews, trend direction, acceleration/deceleration.
     Only applicable when baseline exists. -->

## Appendix

- **Audit Reports Referenced:** <!-- links to audit reports -->
- **Events Analyzed:** {{N}} events from {{DATE_RANGE}}
- **Skills Executed:** <!-- list of review skills used -->
- **Raw Findings:** <!-- link to detailed findings file if exists -->










<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: template-meta -->
> last_verified: 2026-06-18 10:54 | sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: template-meta -->