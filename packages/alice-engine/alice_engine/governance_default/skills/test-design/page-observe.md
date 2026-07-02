# page-observe

## Goal
观察页面 DOM 结构，提取可测元素。

## Input
- 页面 URL
- 登录凭证

## Output
- PAGE_CONTEXT.md：页面结构描述

## Rules
1. 打开页面，等待渲染完成
2. 提取表单字段、表格列、按钮、链接
3. 记录选择器（CSS / XPath）
4. 标注元素类型和交互方式

## Done
- PAGE_CONTEXT.md 包含 ≥3 个可测元素
- 每个元素有可用选择器
