# Workflow: Test Cycle Closure

## 目标
在测试周期结束时汇总执行情况、沉淀经验、更新项目知识。

## 适用对象
- 模块级测试周期结束
- 项目级迭代/版本发布结束

## 输入
- 测试执行报告（多份）
- Bug 统计（按严重程度 + 按模块）
- 自动化执行结果
- 本周期新增的测试用例和自动化用例统计
- 踩坑经验记录
- 当前测试进度追踪

## 阶段
1. 数据汇总 — 用例执行统计、Bug 分布、自动化覆盖
2. 生成测试总结报告 — TEST_SUMMARY.md
3. 知识沉淀 — 更新 PROJECT_CONTEXT.md、测试进度追踪
4. 更新模块上下文状态标记
5. 产出下一周期建议

## 产物
- context/projects/*/summaries/TEST_SUMMARY.md
- PROJECT_CONTEXT.md（更新）
- 测试进度追踪（更新）
- 各模块 MODULE_CONTEXT.md 状态标记（更新）

## 依赖 Skill
- test-summary
- knowledge-precipitation
- progress-report
- allure-report-analyzer（新增：自动解析 Allure JSON 生成摘要）
- knowledge-extractor（新增：周期内 Bug → 坑位批量沉淀）
- excel-exporter（新增：执行结果 → .xlsx 工作成果）

## 完成标准
- 测试结论明确（建议上线 / 有条件上线 / 不建议上线）
- 高频 Bug 和踩坑经验已沉淀
- 下一周期任务清单已产出
- ✅ Excel 工作成果已生成（提交给业务方）

## 上下文同步（必须执行）

> ⚠️ 周期结束后，**必须**执行以下同步。

| 动作 | 目标文件 | 具体操作 |
|------|----------|----------|
| 1. 生成测试摘要 | `TEST_SUMMARY.md` | 调用 `allure-report-analyzer` 解析 Allure JSON |
| 2. 坑位批量沉淀 | `PROJECT_CONTEXT.md` | 调用 `knowledge-extractor` 批量提取周期内 Bug 的通用坑位 |
| 3. 生成 Excel 成果 | `governance/kpi/reports/{模块}/测试报告-{模块}-{页面}.xlsx` | 调用 `excel_renderer.render_page_report()`（v2.1 统一引擎），按页面输出，覆盖式 |
| 4. 更新模块状态 | 各 `MODULE_CONTEXT.md` | 根据执行结果刷新页面/模块状态（✅/🔄/⏳） |
| 5. 更新进度追踪 | `测试进度追踪.md` | 更新所有模块的自动化覆盖数、用例数、Bug 数 |
| 6. 产出下一周期计划 | `测试进度追踪.md` | 标记下一周期重点模块和建议 |

**执行方式**：`allure-report-analyzer` → `excel-exporter`（场景 C）→ `knowledge-extractor` → `context-sync`。










<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: workflow-check -->
## Dependency Check (2026-06-18 10:54)

- [OK] No deprecated skill references
- [OK] Validated 2026-06-18 10:54

> sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: workflow-check -->