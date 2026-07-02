# testcase-design

## Goal
设计页面级测试用例。

## Input
- PAGE_CONTEXT.md
- RISK_MODEL.md

## Output
- TEST_CASES.md：结构化测试用例

## Rules
1. 每个可测元素至少 1 个正向 + 1 个反向用例
2. 用例格式：ID、标题、前置条件、步骤、预期结果、优先级
3. P0 用例必须覆盖核心 CRUD 流程

## Done
- TEST_CASES.md 包含 ≥5 个用例
- 每个用例有明确的预期结果
