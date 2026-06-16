# Web Automation Project Context — 索引入口

> **版本**: 2.1 | **最后更新**: 2026-06-15 | **维护者**: Project Agent
> **下游依赖**: MODULE_CONTEXT → PAGE_CONTEXT → TEST_DESIGN → TECH_ANALYSIS → 自动化代码

本文件是项目上下文的**索引入口**。具体内容已拆分到 5 个子文件，各 Agent 按需加载。

## 子文件索引

| 文件 | 内容 | 加载者 | 估算 Token |
|------|------|--------|-----------|
| `project-profile.md` | 项目目标、技术栈、UI 框架差异、上下文入口 | 所有 Agent | ~500 |
| `base-api-reference.md` | BasePage/BaseDriver/ElementPlusHelper/SidebarNavigator API | automation-agent, project-agent | ~1,500 |
| `coding-standards.md` | 8 条代码红线、PageObject/测试脚本规范、禁止模式、自检命令 | automation-agent | ~1,200 |
| `element-plus-pitfalls.md` | EP-001~EP-011 快速索引（事实源: known-issues.yaml） | automation-agent, bug-analysis-agent, knowledge-agent | ~300 |
| `test-data-policy.md` | 数据管理规范、CleanupTracker、清理策略、命名规范 | automation-agent, execution-agent | ~500 |

## 按 Agent 加载策略

| Agent | 加载文件 | 合计 Token |
|-------|---------|-----------|
| **project-agent** | project-profile + base-api-reference（审计时） | 500–2,000 |
| **requirement-agent** | project-profile | 500 |
| **test-design-agent** | project-profile | 500 |
| **automation-agent** | base-api-reference + coding-standards + element-plus-pitfalls | 3,000 |
| **execution-agent** | test-data-policy | 500 |
| **bug-analysis-agent** | element-plus-pitfalls | 300 |
| **report-agent** | project-profile | 500 |
| **knowledge-agent** | element-plus-pitfalls | 300 |

> 平均每次 Agent 加载: **~900 tokens**（拆分前: ~4,500 tokens, 节省 **80%**）

## 相关资源
- 环境信息：`governance/context/environments.yaml`
- CI 配置：`ZJSN_Test-master526/Jenkinsfile`
- 已知问题库：`governance/context/known-issues.yaml`
- 模块索引：`MODULE_INDEX.md`
- 存量模块上下文（逐步废弃）：`TestIntern_library/02-项目文档/contexts/`

## 维护范围
项目目标、技术边界、模块划分原则、协作约束。页面级细节、风险分析、测试设计、Bug 分析不在本文件维护范围。
