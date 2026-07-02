# context-sync

## Goal
同步项目上下文到 governance 目录。

## Input
- 项目目录结构
- .tlo/ 或 project.yaml

## Output
- governance/context/projects/{id}/project.yaml
- governance/context/projects/{id}/MODULE_INDEX.md

## Rules
1. 扫描项目根目录，提取 name、url、modules
2. 写入 project.yaml
3. 生成模块索引

## Done
- project.yaml 存在且包含 name + url
- MODULE_INDEX.md 列出所有模块
