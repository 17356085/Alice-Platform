# code-consistency-checker

## Goal
检查自动化代码一致性。

## Input
- 已生成的 Page Object + 测试脚本
- 项目代码规范

## Output
- 一致性检查报告

## Rules
1. 检查选择器是否与 PAGE_CONTEXT.md 一致
2. 检查命名是否符合项目规范
3. 检查是否有遗漏的测试用例
4. 检查是否有重复代码

## Done
- 输出不一致项清单
- 每项标注修复建议
