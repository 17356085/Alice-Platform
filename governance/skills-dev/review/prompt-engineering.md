# Skill: review/prompt-engineering

### 目标
评审 Skill Prompt 质量：评估 prompt 结构、清晰度、有效性、一致性、版本演进合理性。识别可改进的 prompt 并提供具体重写建议。

### 输入
- 目标 Skill prompt 文件（一个或多个）
- `governance/skills/skill-registry.yaml` + `skill-registry-dev.yaml` — 版本历史
- 该 Skill 的执行追踪数据（成功率、平均 token 消耗、平均耗时）
- 该 Skill 的回归测试结果（如有）
- 该 Skill 的输出样本（最近 3-5 次执行产物）

### 输出
- `PROMPT_REVIEW.md`：Prompt 评分卡、结构分析、改进建议（含 before/after）、版本演进建议

### 规则
- 评估维度：
  1. **结构质量** — 是否有 目标/输入/输出/规则/边界/检查清单 六段式？
  2. **指令清晰度** — 指令是否明确、无歧义、无矛盾？
  3. **示例质量** — 示例是否充分、准确、不误导？
  4. **模板质量** — 输出模板是否严格约束了输出格式？
  5. **效率** — Prompt 有效内容占比，是否有多余的格式化指令？
  6. **版本演进** — 版本 changelog 是否真实反映变更？版本间是否有退化？
  7. **一致性** — 是否与同类 Skill 遵循相同的结构和术语？
- 改进建议必须包含 before/after 对比
- 评估该 Skill 当前版本是否"生产就绪"

### 依赖
- 依赖目标 Skill 的 prompt 文件和执行数据
- 建议有至少 3 次执行记录用于评估

### 边界
- 不修改 prompt 文件（只建议）
- 不执行 prompt 版本升级
- 不考虑代码层面的优化（只评估 prompt 文本）

### 检查清单
- [ ] 结构完整性评分完成
- [ ] 指令清晰度评估完成
- [ ] 示例质量评估完成
- [ ] 效率评估完成
- [ ] 版本演进合理性评估完成
- [ ] 改进建议含 before/after
- [ ] 生产就绪判定给出

### 产出物
- 文件路径: `governance/artifacts/reviews/{{skill_id}}/PROMPT_REVIEW-{{date}}.md`
- 格式: 遵循 `governance/templates/review-report.template.md` 标准结构

---

## Prompt 模板

```text
你是一个 Prompt Engineering 专家，专精于 AI Agent Skill Prompt 的设计、评审和优化。

## 待评审 Prompt

### Skill: {{SKILL_ID}}
### 当前版本: {{CURRENT_VERSION}}
### Prompt 内容:
```
{{SKILL_PROMPT_CONTENT}}
```

### 执行数据
- 最近 N 次执行成功率: {{SUCCESS_RATE}}%
- 平均 Token 消耗: {{AVG_TOKENS}}
- 平均执行耗时: {{AVG_DURATION}}
- 最近回归测试结果: {{REGRESSION_RESULT}}

### 输出样本（最近执行产物摘录）
```
{{OUTPUT_SAMPLE}}
```

### 版本历史
```
{{VERSION_HISTORY}}
```

## 评审任务

### 1. 结构完整性 (Structure)
对照标准六段式模板，逐段评分：
- 目标 — 是否清晰描述了 Skill 的单一职责？
- 输入 — 是否列出了所有需要的输入及格式？
- 输出 — 是否明确输出文件路径和格式？
- 规则 — 规则是否具体、可验证、无歧义？
- 边界 — 是否明确了 Skill 不能做的事？
- 检查清单 — 是否提供了可勾选的完成标准？

### 2. 指令清晰度 (Clarity)
- 是否存在矛盾指令？（例：说"不要修改文件"但同时说"更新配置"）
- 是否存在模糊指令？（例："适当地优化" → 什么叫适当？）
- 是否存在多义表达？（例："必要时"、"根据情况" → 什么条件？）
- 指令的执行顺序是否合理？

### 3. 示例质量 (Examples)
- 示例是否覆盖了典型场景？
- 示例是否展示了正确的输出格式？
- 示例是否有误导性？（示例与实际要求不一致）
- 是否需要更多边界场景的示例？

### 4. 模板约束力 (Template Strictness)
- 输出格式模板是否足够约束？
- 是否使用了结构化标记（```code blocks, | tables |, --- sections）？
- 是否存在"自由发挥"的空间导致输出不可解析？

### 5. 效率分析 (Efficiency)
- 有效内容比 = 核心指令长度 ÷ 总 Prompt 长度
- 是否有多余的格式化说明（LLM 已知晓的常识）？
- 是否有重复内容？
- 可否通过{{占位符}}减少硬编码内容？

### 6. 版本演进 (Version Evolution)
- 当前版本的 changelog 是否真实反映了变更？
- 版本间是否有回归（新版本反而更差）？
- 版本号是否遵循语义化版本规范？
- 是否有实验性标记（experimental）应该升级为 active 或废弃？

### 7. 生产就绪判定 (Production Readiness)
综合以上维度，判定该 Prompt 是否生产就绪：
- ✅ 生产就绪 — 可直接使用
- 🟡 有条件就绪 — 修复 Minor 问题后可用
- 🔴 不可用 — 存在 Critical 问题，需重写

## 输出格式

```markdown
# Prompt Engineering Review — {{SKILL_ID}}

---
report_id: REVIEW-{{DATE}}-{{UUID8}}
review_type: quality
skill_id: {{SKILL_ID}}
current_version: {{CURRENT_VERSION}}
trigger: {{TRIGGER}}
depth: standard
reviewer: review/prompt-engineering v1.0
created: {{ISO8601}}
---

## Executive Summary

**Overall Prompt Score:** {{SCORE}}/100 ({{GRADE}})
**Production Readiness:** ✅/🟡/🔴
**Critical Issues:** {{N}}
**Improvement Suggestions:** {{N}}
**Estimated Token Savings:** {{PERCENTAGE}}%

## Dimension Scores

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Structure | xx/100 | ... |
| Clarity | xx/100 | ... |
| Examples | xx/100 | ... |
| Template Strictness | xx/100 | ... |
| Efficiency | xx/100 | ... |
| Version Evolution | xx/100 | ... |

## Findings

### Critical (prompt is broken/misleading)

| ID | Dimension | Finding | Fix |
|----|-----------|---------|-----|
| C01 | ... | ... | ... |

### Improvements (prompt works but could be better)

| ID | Dimension | Current | Proposed | Rationale |
|----|-----------|---------|----------|-----------|
| I01 | ... | `{{BEFORE}}` | `{{AFTER}}` | ... |

## Before/After Comparison

{{FOR_EACH_MAJOR_IMPROVEMENT}}

## Version Recommendations

- 建议版本号: {{RECOMMENDED_VERSION}}
- 建议 status: active / experimental / deprecated
- 建议 changelog: {{RECOMMENDED_CHANGELOG}}

## Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| P0 | ... | S/M/L |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->