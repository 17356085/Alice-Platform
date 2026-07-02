# risk-modeling

## Goal
评估页面测试风险等级。

## Input
- PAGE_CONTEXT.md
- TEST_CASES.md

## Output
- RISK_MODEL.md：风险矩阵

## Rules
1. 按业务影响 × 技术复杂度评分
2. P0：核心流程 + 高复杂度
3. P1：常规功能
4. P2：边缘场景

## Done
- 每个测试用例标注风险等级
- 输出 P0/P1/P2 数量统计
