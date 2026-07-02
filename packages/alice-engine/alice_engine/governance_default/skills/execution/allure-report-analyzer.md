# allure-report-analyzer

## Goal
分析测试执行结果。

## Input
- Allure 报告数据
- 测试用例清单

## Output
- 执行结果摘要
- 失败用例列表

## Rules
1. 解析 Allure 报告
2. 统计通过/失败/跳过
3. 提取失败用例的错误信息

## Boundaries
- 不修复失败用例
- 不修改测试代码
