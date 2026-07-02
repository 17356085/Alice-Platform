# hygiene-check

## Goal
检查项目治理文档完整性。

## Input
- governance/context/projects/{id}/

## Output
- 检查报告：缺失文件列表 + 建议

## Rules
1. 检查 project.yaml 是否存在
2. 检查每个模块是否有 MODULE_CONTEXT.md
3. 检查每个页面是否有 PAGE_CONTEXT.md
4. 输出缺失清单

## Done
- 列出所有缺失文档
- 按优先级排序（P0 模块优先）
