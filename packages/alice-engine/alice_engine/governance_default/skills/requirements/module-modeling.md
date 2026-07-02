# module-modeling

## Goal
建模模块的页面结构和路由关系。

## Input
- MODULE_CONTEXT.md
- 项目源码（路由配置）

## Output
- 模型：页面列表 + 路由映射 + 页面层级

## Rules
1. 解析路由配置文件
2. 提取页面路径和组件映射
3. 构建页面树（父页面 → 子页面）

## Done
- 输出 pages 列表（slug + path + component）
- 输出路由映射表
