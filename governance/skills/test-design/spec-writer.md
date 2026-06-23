# Skill: spec-writer

## 目标
Spec Pipeline 阶段 3 — 基于风险分析产出完整的测试用例规格：步骤、预期结果、优先级、测试数据、标签、场景 ID 映射。

## 输入
- RISK_ANALYSIS.md（阶段 2 产出）
- SPEC_GATHERER_REPORT.md（阶段 1 产出）
- PAGE_CONTEXT.md (每页面)
- 现有 TEST_CASES.md（如有，增量模式）

## 输出
- TEST_SPEC.md — 结构化测试用例规格
  - 测试策略概述（Smoke/Regression/Boundary/Negative/Security 五类覆盖）
  - 测试用例表（每页面一个表格）
  - 场景 ID 映射（BS-XXX-NNN → 用例 ID）
  - 优先级分布（P0/P1/P2 统计）
  - 测试数据依赖（账号/前置数据/清理脚本）

## 规则
- 用例格式: ID | 页面 | 场景类型 | 优先级 | 前置条件 | 步骤 | 预期结果 | 测试数据 | 标签
- 优先级: P0(核心业务/冒烟) | P1(主要功能/回归) | P2(边缘/负向)
- 场景类型: Smoke / Regression / Boundary / Negative / Security
- 每页面最少覆盖: 2 Smoke + 3 Regression + 2 Boundary + 2 Negative + 1 Security
- 标签: @smoke @regression @boundary @negative @security @{module} @{page}
- 参考现有 TEST_CASES.md 的 source 字段标注惯例

## 依赖
- skills/test-design/spec-researcher.md（阶段 2）
- governance/templates/test-cases.template.md
- governance/context/projects/web-automation/test-data-policy.md

## 边界
- 本 Skill 不评审用例质量（那是 spec-critic 的职责）
- 本 Skill 不生成自动化代码（那是 Automation Developer 的职责）
- 增量模式不覆盖已有用例，仅补充缺口

---

## Prompt 模板

```text
你是一个资深测试用例设计师。请基于风险分析产出完整的测试用例规格。

## 输入
- RISK_ANALYSIS.md：{{risk_summary}}
- 页面列表：{{page_list}}
- 测试数据策略：{{test_data_policy}}

## 任务
1. 写测试策略概述（Smoke/Regression/Boundary/Negative/Security 五类各 1 段）
2. 每页面生成用例表（10+ 用例，覆盖五类场景）
3. 标注场景 ID 映射（BS-XXX-NNN → TC-XXX）
4. 标注优先级 + 标签
5. 列出测试数据依赖

## 用例格式
| ID | 页面 | 场景类型 | 优先级 | 前置条件 | 步骤 | 预期结果 | 测试数据 | 标签 |

## 输出
生成 TEST_SPEC.md。确保每页面 ≥10 用例，五类场景全覆盖。
```
