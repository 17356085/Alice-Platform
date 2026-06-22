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
| `../shared-language.md` | 平台术语表、测试术语、被测系统业务术语、歧义消除 | 所有 Agent | ~350 |

## 按 Agent 加载策略

| Agent | 加载文件 | 合计 Token |
|-------|---------|-----------|
| **project-agent** | shared-language + project-profile + base-api-reference（审计时） | 850–2,350 |
| **requirement-agent** | shared-language + project-profile | 850 |
| **test-design-agent** | shared-language + project-profile | 850 |
| **automation-agent** | shared-language + base-api-reference + coding-standards + element-plus-pitfalls | 3,350 |
| **execution-agent** | shared-language + test-data-policy | 850 |
| **bug-analysis-agent** | shared-language + element-plus-pitfalls | 650 |
| **report-agent** | shared-language + project-profile | 850 |
| **knowledge-agent** | shared-language + element-plus-pitfalls | 650 |

> 平均每次 Agent 加载: **~1,250 tokens**（拆分前: ~4,500 tokens, 节省 **72%**）。shared-language.md 新增 ~350 tokens/Agent 增量，换取术语一致性。**注意**: 以上为完整列表；会话级按需加载，非每个 Agent 都加载全部。实际平均加载 ~900 tokens/Agent。

## 相关资源
- 环境信息：`governance/context/environments.yaml`
- CI 配置：`ZJSN_Test-master526/Jenkinsfile`
- 已知问题库：`governance/context/known-issues.yaml`
- 模块索引：`MODULE_INDEX.md`
- 存量模块上下文（逐步废弃）：`TestIntern_library/02-项目文档/contexts/`

## 维护范围
项目目标、技术边界、模块划分原则、协作约束。页面级细节、风险分析、测试设计、Bug 分析不在本文件维护范围。
<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: project-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 项目统计数据 (更新于 2026-06-18 10:54)

| 指标 | 数值 |
|------|:---:|
| 纳管模块 | 12 |
| 100% 完成模块 | 2 (tank, lab) |
| SOP completed | 10 |
| Pending/重置 | 1 |
| 测试文件总数 | 118 |
| Page Object 总数 | 85 |
| 治理文档总数 | 364 |
| 总体进度 | 83% |

> 此段由 sync_progress.py 自动更新。2026-06-18 10:54
<!-- ⚠️ AUTO-GENERATED SECTION END: project-stats -->