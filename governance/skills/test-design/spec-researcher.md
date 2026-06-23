# Skill: spec-researcher

## 目标
Spec Pipeline 阶段 2 — 基于收集的信息进行风险分析：识别高风险区域、边界条件、安全漏洞面、数据一致性风险、Element Plus 组件陷阱。

## 输入
- SPEC_GATHERER_REPORT.md（阶段 1 产出）
- MODULE_CONTEXT.md
- PAGE_CONTEXT.md (每页面)
- known-issues.yaml

## 输出
- RISK_ANALYSIS.md — 结构化风险分析报告
  - 高风险区域（Top 5，含风险等级 H/M/L）
  - 边界条件清单（每页面 ≥3 条）
  - 安全测试面（OWASP Top 10 映射）
  - Element Plus 组件风险点（el-dialog Teleport / el-cascader 动画 / el-table 虚拟滚动）
  - 数据流风险（CRUD 操作的原子性/并发）

## 规则
- 风险等级：H (Critical/HIGH) — 影响核心业务 | M (MEDIUM) — 影响用户体验 | L (LOW) — 边缘场景
- Element Plus 陷阱参考 element-plus-pitfalls.md
- 边界条件必须具体到输入值/操作步骤
- 安全测试面映射到具体页面/组件

## 依赖
- skills/test-design/spec-gatherer.md（阶段 1）
- governance/context/projects/web-automation/element-plus-pitfalls.md
- governance/context/known-issues.yaml

## 边界
- 本 Skill 不生成测试用例（那是 spec-writer 的职责）
- 本 Skill 不评价风险优先级（那是 spec-critic 的职责）
- 风险建模与 test-design/risk-modeling 互补不重复

---

## Prompt 模板

```text
你是一个资深质量风险分析专家。请基于收集的材料进行测试风险分析。

## 输入材料
- SPEC_GATHERER_REPORT.md：{{gatherer_summary}}
- Element Plus 已知陷阱：{{element_plus_pitfalls}}
- 历史缺陷：{{known_issues_summary}}

## 任务
1. 识别 5 个最高风险区域，标注 H/M/L
2. 每页面列出 ≥3 个边界条件（具体输入值）
3. 映射 OWASP Top 10 安全测试面到具体页面/组件
4. 标注 Element Plus 组件特定风险（Teleport/Dialog/Cascader/Table）
5. 分析 CRUD 数据流的原子性风险

## 输出
生成 RISK_ANALYSIS.md，包含：
- 风险矩阵（5 个高风险 + 等级 + 影响范围）
- 边界条件表（页面/组件/边界值/预期行为）
- 安全测试面映射（OWASP 类别 → 页面 → 测试点）
- Element Plus 组件风险清单
- 数据流风险分析
```
