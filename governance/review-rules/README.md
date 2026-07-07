# Review Rules — 代码审查规则配置

## 概述

借鉴 [Open Code Review (OCR)](https://github.com/alibaba/open-code-review) 的规则设计理念:
- **规则 = glob 模式 → 自然语言指令** 的映射
- 规则不是模式匹配引擎，而是告诉 LLM "在这些文件中找什么"
- 4 层优先级链: CLI > 项目 > 全局 > 系统默认

## 规则文件格式

```json
{
  "rules": [
    {
      "path": "**/*.vue",
      "rule": "检查 v-html XSS 防护、props 类型校验"
    },
    {
      "path": "src/api/**/*.py",
      "rule": "docs/api-rules.md",
      "merge_system_rule": true
    }
  ],
  "include": ["src/**"],
  "exclude": ["**/test/**"]
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `path` | ✅ | glob 模式，支持 `**`、`*`、`{a,b}` |
| `rule` | ✅ | 自然语言指令，或 `.md/.txt` 文件路径 |
| `merge_system_rule` | ❌ | `true` 时与系统默认规则合并 |

### `rule` 字段解析

- **多行内容** → 直接作为指令
- **单行 `.md/.txt/.markdown` 结尾** → 视为文件路径，读取内容
- **其他** → 直接作为指令

## 4 层优先级

| 优先级 | 来源 | 路径 |
|--------|------|------|
| 1 (最高) | CLI 参数 | `--rule` 指定 |
| 2 | 项目规则 | `governance/review-rules/rule.json` (本文件) |
| 3 | 全局规则 | `~/.alice/review-rules/rule.json` |
| 4 (最低) | 系统默认 | 内嵌在 `rule_config.py` 中 |

首次匹配生效。高优先级规则可设置 `merge_system_rule: true` 来合并系统规则。

## include/exclude

- `include`: 只审查匹配的文件 (空 = 审查所有)
- `exclude`: 排除匹配的文件 (优先于 include)
- 内置排除: `__pycache__`、`node_modules`、`.pyc`、`dist`、`build`、`.venv`

## 编写指南

1. **具体 > 抽象**: "检查 v-html 是否有 XSS 防护" 比 "检查安全性" 更有效
2. **检查清单格式**: 用数字编号列出具体检查项
3. **针对项目**: 项目特有的规则放在本文件，通用规则放系统默认
4. **避免重复**: 系统默认已覆盖常见的 Vue/Python/TS 检查
