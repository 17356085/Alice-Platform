# Prompt Library Index

> 索引文件，指向旧 `TestIntern_library/05-资源与参考/AI提示词库.md`。
> 该文件为 SOP Phase 编排的完整提示词集合，逐一映射到治理层 Skill / Template。

## 映射概览

| SOP Phase | 提示词 | 现有治理层覆盖 | 说明 |
| --- | --- | --- | --- |
| Phase 0 | P0-01 项目初始化 | `skills/project-context-manager.md` | 已有 Skill |
| Phase 0.5 | P0.5-01~02 模块建模 | `skills/module-modeling.md` | ✅ 已沉淀 |
| Phase 0.8 | P0.8-01 需求分析 | `skills/requirement-analysis.md` | ✅ 已沉淀 |
| Phase 1 | P1-01~02 页面分析 | `skills/page-analysis.md` | ✅ 已沉淀 |
| Phase 1.5 | P1.5-01 风险建模 | `skills/risk-modeling.md` | ✅ 已沉淀 |
| Phase 2 | P2-01 测试设计 | `skills/testcase-design.md` | 已有 Skill |
| Phase 2.5 | P2.5-01 测试用例表 | `skills/testcase-design.md` | 已有 Skill |
| Phase 3 | P3-01 技术分析 | `skills/tech-analysis.md` | ✅ 已沉淀 |
| Phase 3.5 | P3.5-01 自动化策略 | `skills/auto-strategy.md` | ✅ 已沉淀 |
| Phase 4 | P4-01~04 代码生成 | `skills/code-generation.md` | ✅ 已沉淀 |
| Phase 4.5 | P4.5-01 Bug 分析 | `skills/bug-analysis.md` | 已有 Skill |
| Phase 5 | P5-01 批量失败分析 | `skills/bug-analysis.md` | 已有 Skill（可扩展） |
| Phase 6 | P6-01 接口测试 | `skills/api-testing.md` | ✅ 已沉淀 |
| Phase 7 | P7-01 CI 分析 | `skills/ci-pipeline-analysis.md` | 已有 Skill |
| Phase 8 | P8-01 测试总结 | `skills/test-summary.md` | ✅ 已沉淀 |
| Phase 9 | P9-01 知识沉淀 | `skills/knowledge-precipitation.md` | ✅ 已沉淀 |

## 跨场景提示词映射

| 提示词 | 用途 | 现有治理层覆盖 | 说明 |
| --- | --- | --- | --- |
| S-01 上下文恢复 | 新会话开始时恢复上下文 | `skills/context-sync.md` | 已有 Skill |
| S-02 上下文同步 | 会话结束时更新上下文 | `skills/context-sync.md` | 已有 Skill |
| S-03 代码审查 | 审查测试脚本 | Claude Code 内置 `code-review` | 系统内置 |
| S-04 测试数据生成 | 为测试场景生成测试数据 | `skills/test-data-generation.md` | ✅ 已沉淀 |
| S-05 Element Plus 定位 | 复杂定位策略设计 | `skills/element-plus-locator.md` | ✅ 已沉淀 |
| S-06 小程序测试 | 微信小程序测试设计 | `skills/miniapp-testing.md` | ✅ 已沉淀 |
| S-07 测试进度报告 | 生成周报/进度报告 | `skills/progress-report.md` | ✅ 已沉淀 |
| S-08 模块完整性检查 | 检查 contexts 文档完整性 | `skills/completeness-check.md` | ✅ 已沉淀 |

## 与模板的关系

`templates/` 定义文档的 **输出格式**（如 PAGE_CONTEXT.md 应包含哪些字段），而提示词库定义 **如何引导 AI 生成这些文档**。两者互补。

## 参考

- 全量提示词：`TestIntern_library/05-资源与参考/AI提示词库.md`
- 编排 SOP：`TestIntern_library/02-项目文档/AI辅助测试开发_标准作业流程（SOP）.md`
