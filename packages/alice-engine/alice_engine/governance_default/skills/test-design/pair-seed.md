# pair-seed

## Goal
生成配对测试数据种子。

## Input
- TEST_CASES.md
- PAGE_CONTEXT.md

## Output
- 测试数据种子文件

## Rules
1. 为每个 P0 用例生成 1 组有效数据
2. 为每个边界条件生成 1 组无效数据
3. 数据格式与页面表单字段匹配

## Done
- 每个 P0 用例有对应测试数据
- 数据可直接用于自动化脚本
