# page-object-generator

## Goal
生成 Page Object 模式代码。

## Input
- PAGE_CONTEXT.md（选择器 + 元素类型）

## Output
- {Page}Page.py：Page Object 类

## Rules
1. 每个可测元素生成 1 个属性
2. 每个交互动作生成 1 个方法
3. 使用 BasePage 基类
4. 选择器使用类变量

## Done
- 生成的 .py 文件可直接 import
- 选择器与 PAGE_CONTEXT.md 一致
