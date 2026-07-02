# excel-exporter

## Goal
导出测试用例为 Excel 文件。

## Input
- TEST_CASES.md
- 页面名称

## Output
- {module}/{page}-testcases-{timestamp}.xlsx

## Rules
1. 每个用例一行
2. 列：ID、标题、优先级、前置条件、步骤、预期结果、状态
3. P0 用例标红
4. 自动列宽

## Done
- Excel 文件可打开
- 用例数量与 TEST_CASES.md 一致
