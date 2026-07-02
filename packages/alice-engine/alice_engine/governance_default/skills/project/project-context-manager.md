# project-context-manager

## Goal
初始化项目上下文。发现模块、页面、路由结构。

## Input
- module: 模块名称
- pages: 页面列表（可选）

## Output
- MODULE_CONTEXT.md: 模块级上下文
- PAGE_CONTEXT.md: 页面级上下文

## Rules
1. 扫描项目目录，发现可用模块
2. 为每个模块生成上下文文档
3. 记录路由、组件、API 端点

## Boundaries
- 不执行测试
- 不生成代码
