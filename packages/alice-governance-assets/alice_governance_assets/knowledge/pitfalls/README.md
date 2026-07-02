# 踩坑经验库 (Pitfalls)

> 从 known-issues.yaml 中沉淀的结构化踩坑经验。
> 每个文件一条踩坑记录，包含：现象 / 根因 / 解决方案 / 预防措施。

## 目录

| 目录 | 内容 |
|------|------|
| [element-plus/](element-plus/) | Element Plus 组件踩坑 |
| [selenium/](selenium/) | Selenium 通用踩坑 |
| project-specific/ | 本系统特有坑位 (待创建 — tank UI 框架差异, contractor nest-menu 导航等) |

## 格式规范

每份 `.md` 文件包含：
```markdown
# <标题>

| 属性 | 值 |
|------|-----|
| 关联ID | known-issues.yaml 中的 ID |
| 严重度 | high / medium / low |
| 复现率 | 0-100% |
| 首次发现 | YYYY-MM-DD |
| 最近出现 | YYYY-MM-DD |

## 现象
## 根因
## 解决方案
## 预防措施
## 受影响模块
```

## 相关

- [known-issues.yaml](../../context/known-issues.yaml) — 已知问题结构化清单
- [PROJECT_CONTEXT.md](../../context/projects/web-automation/PROJECT_CONTEXT.md) — § Element Plus 已知坑位清单
