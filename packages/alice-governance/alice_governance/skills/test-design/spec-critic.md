# Skill: spec-critic

## 目标
Spec Pipeline 阶段 4 — 对测试用例规格进行独立质量评审：重复检测、覆盖率缺口分析、可执行性验证、优先级合理性检查。借鉴 Aperant code review QA 循环模式。

## 输入
- TEST_SPEC.md（阶段 3 产出）
- RISK_ANALYSIS.md（阶段 2 产出）
- SPEC_GATHERER_REPORT.md（阶段 1 产出）
- 现有 TEST_CASES.md（如有，用于重复检测）

## 输出
- CRITIC_REVIEW.md — 评审报告
  - 总体评分（0-100）
  - 重复用例检测（与现有用例的相似度 >80%）
  - 覆盖率缺口（页面/组件/场景类型三维矩阵）
  - 可执行性问题（定位器缺失/数据依赖不可达/步骤不可操作）
  - 优先级合理性（P0 过多/过少、安全用例缺失优先级标注）
  - 改进建议（具体到用例 ID + 修改内容）

## 规则
- 评分 ≤60 → 打回阶段 3 (spec-writer) 重做
- 评分 60-80 → 标注问题后通过
- 评分 ≥80 → 直接通过
- 重复检测: 比较步骤序列 + 预期结果 + 测试数据的 Levenshtein 相似度
- 覆盖率缺口: 页面×场景类型矩阵空缺检测
- 可执行性: 检查定位器是否在 PAGE_CONTEXT.md 中定义

## 依赖
- skills/test-design/spec-writer.md（阶段 3）
- governance/artifacts/sop-status/SOP_STATUS_{{module}}.json
- governance/context/projects/web-automation/element-plus-pitfalls.md

## 边界
- 本 Skill 不修改 TEST_SPEC.md（仅评审+建议）
- 本 Skill 不补充缺失用例（打回 spec-writer 重做）
- 评分标准独立于 Automation Developer 的代码评审
- 质量门禁：4 阶段全部通过 TEST_SPEC 才进入阶段 4（自动化开发）

---

## Prompt 模板

```text
你是一个资深测试质量评审专家（独立评审角色，不参与用例设计）。请对以下测试用例规格进行独立评审。

## 评审材料
- TEST_SPEC.md：{{test_spec}}
- RISK_ANALYSIS.md：{{risk_analysis}}
- 现有 TEST_CASES.md：{{existing_cases}}

## 评审维度
1. **重复检测**: 逐条比对步骤序列+预期+数据，标注相似度 >80% 的重复用例
2. **覆盖率缺口**: 检查页面×场景类型（Smoke/Regression/Boundary/Negative/Security）矩阵空缺
3. **可执行性**: 验证每个用例的定位器在 PAGE_CONTEXT.md 中可找到、测试数据可构造
4. **优先级合理性**: 检查 P0 占比是否在 20-40%、安全用例是否标注优先级
5. **边界完整性**: 边界条件是否完全覆盖（参考 RISK_ANALYSIS.md 的边界清单）

## 评分标准
- 90-100: 无缺口，可直接进入自动化开发
- 60-80: 存在缺口但可后续补充，标注问题后通过
- <60: 严重缺口，打回 spec-writer 重做

## 输出
生成 CRITIC_REVIEW.md，包含：
- 总体评分 + 各维度评分
- 重复用例列表（ID 对 + 相似度）
- 覆盖率缺口矩阵
- 可执行性问题清单
- 优先级调整建议
- 是否需要打回（score <60 → REJECT）
```
