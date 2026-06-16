# Context Governance

## 设计原则
- 先按测试项目划分
- 再按模块划分
- 页面作为最小业务分析单元
- 项目级文件只保留稳定共性
- 详细模块事实尽量沉到模块树中

## 结构约定
- `projects/<project>/PROJECT_CONTEXT.md`
- `projects/<project>/MODULE_INDEX.md`
- `projects/<project>/modules/<module>/MODULE_CONTEXT.md`
- `projects/<project>/modules/<module>/pages/<page>/PAGE_CONTEXT.md`
- `projects/<project>/summaries/TEST_SUMMARY.md`

## SOP Phase vs 文档产出 vs 存放位置

下表是依据旧 `contexts/` 体系及治理层约定梳理的完整文档映射：

| Phase | 文档 | governance 存放位置 | 层级 | 模板 |
| --- | --- | --- | --- | --- |
| **Phase 0** | `PROJECT_CONTEXT.md` | `context/projects/<project>/` | 项目级 | — |
| **Phase 0.5** | `MODULE_CONTEXT.md` | `context/projects/<project>/modules/<module>/` | 模块级 | `templates/module-context.template.md` |
| **Phase 1** | `PAGE_CONTEXT.md` | `context/projects/<project>/modules/<module>/pages/<page>/` | 页面级 | `templates/page-context.template.md` |
| **Phase 1.5** | `RISK_MODEL.md` | 同页面目录 | 页面级 | `templates/risk-model.template.md` |
| **Phase 2** | `TEST_DESIGN.md` | 同页面目录 | 页面级 | `templates/test-design.template.md` |
| **Phase 2.5** | `TEST_CASES.md` | 同页面目录 | 页面级 | `templates/test-cases.template.md` |
| **Phase 3** | `TECH_ANALYSIS.md` | 同页面目录 | 页面级 | `templates/tech-analysis.template.md` |
| **Phase 3** | `PAGE_ELEMENT_POSITION.md` | 同页面目录 | 页面级 | — |
| **Phase 3.5** | `AUTO_STRATEGY.md` | 同页面目录 | 页面级 | `templates/auto-strategy.template.md` |
| **Phase 4** | 自动化代码 | 自动化工程 | 代码 | — |
| **Phase 4.5** | `BUG_ANALYSIS.md` | `artifacts/` 或测试报告目录 | 报告 | `templates/bug-analysis.template.md` |
| **Phase 5** | `FAIL_ANALYSIS.md` | `artifacts/` | 报告 | — |
| **Phase 8** | `TEST_SUMMARY.md` | `context/projects/<project>/summaries/` | 报告 | `templates/test-summary.template.md` |
| **Phase 9** | `PROJECT_CONTEXT.md`（更新） | 同 Phase 0 | 项目级 | — |

### 文档归属规则

```text
项目级 → context/projects/<project>/        PROJECT_CONTEXT, MODULE_INDEX
模块级 → context/projects/<project>/modules/<module>/  MODULE_CONTEXT
页面级 → 同模块 pages/<page>/              PAGE_CONTEXT, RISK_MODEL, TEST_DESIGN,
                                           TEST_CASES, TECH_ANALYSIS,
                                           PAGE_ELEMENT_POSITION, AUTO_STRATEGY
模板   → templates/                        所有 *.template.md
产物   → artifacts/                        一次性分析/报告结果
流程   → workflows/                        流程规则与工作流
能力   → skills/                           可复用的 prompt 与 skill
```

## 与现有资产关系
现有 `TestIntern_library\02-项目文档\contexts\` 为存量主资产。
本治理层先做：
1. 索引
2. 规则
3. 映射
4. 渐进迁移

## 更新规则
- 稳定事实更新到 `context/`
- 流程规则更新到 `workflows/`
- 可复用能力更新到 `skills/`
- 一次性输出或分析结果进入 `artifacts/`

## 新建模块
1. 在 `context/projects/<project>/modules/` 下创建 `<module>/` 目录
2. 复制 `templates/module-context.template.md` → `<module>/MODULE_CONTEXT.md`
3. 创建 `pages/` 子目录，按页面逐个补充
4. 按 SOP Phase 顺序产出各级文档

## 新建页面
1. 在 `context/<project>/modules/<module>/pages/` 下创建 `<page>/` 目录
2. 复制 `templates/page-context.template.md` → `<page>/PAGE_CONTEXT.md`
3. 依次产出：`RISK_MODEL` → `TEST_DESIGN` → `TEST_CASES` → `TECH_ANALYSIS` → `PAGE_ELEMENT_POSITION` → `AUTO_STRATEGY`

## AI 会话上下文传递

```text
会话开始前：读取 PROJECT_CONTEXT → MODULE_CONTEXT → PAGE_CONTEXT（逐级加载）
会话结束后：更新对应 Phase 的文档，同步回 context/ 模块树
```
