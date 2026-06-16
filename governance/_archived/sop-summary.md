# SOP Summary — AI 辅助测试开发标准作业流程

> 摘要映射。全量内容见：
> `TestIntern_library/02-项目文档/AI辅助测试开发_标准作业流程（SOP）.md`

## 流程结构

SOP 定义了 **10 个 Phase + 1 个上下文同步阶段**，覆盖从项目初始化到知识沉淀的全生命周期：

| Phase | 名称 | 模型 | 核心产出 | 治理层覆盖 |
| --- | --- | --- | --- | --- |
| Phase 0 | 项目初始化 | Opus | PROJECT_CONTEXT.md | `workflows/project-takeover.md` |
| Phase 0.5 | 模块建模 | Sonnet | MODULE_CONTEXT.md | 已独立建模 |
| Phase 0.8 | 需求分析 | Sonnet | 需求分析文档 | ⏳ |
| Phase 1 | 页面分析 | Sonnet | PAGE_CONTEXT.md | 模板就绪 |
| Phase 1.5 | 风险建模 | Sonnet | RISK_MODEL.md | 模板就绪 |
| Phase 2 | 测试设计 | Sonnet | TEST_DESIGN.md | `workflows/module-test-design.md` |
| Phase 2.5 | 测试执行表 | Haiku | TEST_CASES.md | `workflows/module-test-design.md` |
| Phase 3 | 技术实现分析 | Sonnet | TECH_ANALYSIS.md + PAGE_ELEMENT_POSITION.md | 模板就绪 |
| Phase 3.5 | 自动化策略 | Sonnet | AUTO_STRATEGY.md | ⏳ |
| Phase 4 | 自动化代码 | Sonnet | Page Object + test_*.py | ⏳ |
| Phase 4.5 | Bug 分析 | Sonnet | BUG_ANALYSIS.md | `workflows/automation-failure-closure.md` |
| Phase 5 | 自动化失败分析 | Sonnet | FAIL_ANALYSIS.md | `workflows/automation-failure-closure.md` |
| Phase 6 | 接口测试 | Sonnet | API_TEST_DESIGN.md | ⏳ |
| Phase 7 | 持续集成分析 | Sonnet | CI 分析报告 | `skills/ci-pipeline-analysis.md` |
| Phase 8 | 测试总结 | Haiku | TEST_SUMMARY.md | 模板就绪 |
| Phase 9 | 知识沉淀 | Sonnet | PROJECT_CONTEXT.md 更新 | `skills/context-sync.md` |
| — | 上下文同步 | Sonnet | 上下文文档更新 | `workflows/session-sync.md` |

> 强制说明：上下文同步不是可选收尾动作，而是 Phase 成功条件的一部分。未同步完成的 Phase 视为未完成，不能推进到下一阶段。

## 会话管理规则

| 规则 | 说明 |
| --- | --- |
| 项目级会话 | 仅执行一次，输出 PROJECT_CONTEXT.md |
| 模块级会话 | 每个模块独立会话，禁止多模块混入 |
| 自动化会话 | 与测试设计分离，独立会话 |
| Bug 会话 | 一个 Bug 一个会话 |
| 上下文传递 | 通过文档传递（PROJECT_CONTEXT → MODULE_CONTEXT → PAGE_CONTEXT） |
| 最大会话长度 | 不超过 100 轮 |

## 核心原则

1. **模块级管理优于超长会话**
2. **文档传递上下文优于上下文记忆**
3. **先分析后编码**
4. **先设计后自动化**
5. **知识沉淀比单次测试更重要**
6. **AI 辅助决策，人负责最终判断**

## 参考

- 全量 SOP：`TestIntern_library/02-项目文档/AI辅助测试开发_标准作业流程（SOP）.md`
- 提示词库：`TestIntern_library/05-资源与参考/AI提示词库.md` | `skills/prompt-library-index.md`
