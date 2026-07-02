# requirement-analysis

## Goal
分析业务需求，确定测试范围和优先级。

## Input
- MODULE_CONTEXT.md: 模块上下文
- PAGE_CONTEXT.md: 页面上下文

## Output
- TEST_CASES.md: 测试用例清单

## Rules
1. 从页面上下文提取业务场景
2. 按 P0/P1/P2 分级
3. 每个用例包含：标题、前置条件、步骤、预期结果

## Boundaries
- 不生成自动化代码
- 不执行测试
