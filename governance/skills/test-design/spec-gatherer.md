# Skill: spec-gatherer

## 目标
Spec Pipeline 阶段 1 — 收集测试需求相关的全部输入材料：需求文档、页面截图、API Schema、历史缺陷记录、已有测试用例。

## 输入
- 模块名称 + 页面列表
- MODULE_CONTEXT.md
- 业务需求描述（可选）
- 被测系统 URL

## 输出
- SPEC_GATHERER_REPORT.md — 综合信息收集报告
  - 需求摘要（业务目标、功能范围、非功能需求）
  - 页面清单（URL + 截图引用 + Element Plus 组件清单）
  - API 接口列表（如有）
  - 历史缺陷摘要（从 known-issues.yaml 提取）
  - 现有测试覆盖（从 SOP_STATUS 读取）

## 规则
- 先读 MODULE_CONTEXT.md → 再读 PAGE_CONTEXT.md (每页面) → 最后查 known-issues.yaml
- 不分析、不评价——仅收集和整理原始信息
- 缺失的信息标注 `[MISSING]` 而非跳过
- 截图路径使用相对路径（governance/artifacts/screenshots/）

## 依赖
- templates/module-context.template.md
- governance/context/known-issues.yaml
- governance/artifacts/sop-status/SOP_STATUS_{{module}}.json

## 边界
- 本 Skill 不分析风险（那是 spec-researcher 的职责）
- 本 Skill 不设计测试用例（那是 spec-writer 的职责）
- 本 Skill 不做质量评审（那是 spec-critic 的职责）

---

## Prompt 模板

```text
你是一个资深测试需求分析师。请为以下模块收集测试设计所需的全部输入材料。

## 模块信息
- 模块名称：{{module_name}}
- 页面列表：{{page_list}}
- 被测系统：{{target_url}}

## 任务
1. 读取 MODULE_CONTEXT.md，提取模块功能范围
2. 读取每个页面的 PAGE_CONTEXT.md，记录 Element Plus 组件清单
3. 查询 known-issues.yaml，提取该模块的历史缺陷
4. 读取 SOP_STATUS，了解当前测试覆盖状态

## 输出
生成 SPEC_GATHERER_REPORT.md，包含：
- 需求摘要
- 页面组件清单（每页面一个表格）
- API 接口列表（如有）
- 历史缺陷 TOP 5
- 现有覆盖缺口（页面未测试/组件未覆盖）
- 信息缺失项 [MISSING]

**重要**: 只收集，不分析。缺失信息标注 [MISSING]，不编造。
```
