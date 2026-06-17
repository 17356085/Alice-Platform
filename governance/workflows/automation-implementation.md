# Workflow: Automation Implementation

## 目标
从技术分析到自动化代码实现的端到端流程：技术分析 → 自动化策略 → 代码生成。

## 适用对象
- 已有 PAGE_CONTEXT 和 TEST_DESIGN 的页面
- 需新增或补充自动化覆盖的模块

## 输入
- PAGE_CONTEXT.md / TECH_ANALYSIS.md（如有）
- 页面 HTML 源码
- TEST_CASES.md
- 已有 BasePage.py 与 ElementPlusHelper
- 已有模块参考代码（Page Object、conftest）

## 阶段
1. 技术实现分析 — 组件识别、DOM 分析、定位器设计
2. 自动化策略设计 — 覆盖矩阵、PageObject 拆分、ROI
3. PageObject 代码生成 — 按一个文件一次的粒度
4. 测试脚本生成 — test_*.py + conftest.py
5. （可选）疑难定位器排查 — 针对 Element Plus 特殊组件

## 产物
- context/projects/*/modules/*/pages/*/TECH_ANALYSIS.md
- context/projects/*/modules/*/pages/*/AUTO_STRATEGY.md
- 自动化工程中对应的 Page Object、test_*.py、conftest.py

## 依赖 Skill
- tech-analysis
- auto-strategy
- page-object-generator（替代原 code-generation Step 1）
- test-script-generator（替代原 code-generation Step 2）
- test-script-generator（替代原 code-generation Step 2+3 — 含 conftest 生成）
- code-consistency-checker（新增：代码生成后必须检查）
- tech-analysis（替代原 element-plus-locator — 已合并 Element Plus 定位器诊断）

## 完成标准
- 自动化脚本可通过 pytest 执行
- P0 用例全部覆盖
- 定位器稳定性评级明确
- **代码通过 code-consistency-checker 合规检查**

## 上下文同步（必须执行）

> ⚠️ 代码生成后，**必须**执行以下同步。

| 动作 | 目标文件 | 具体操作 |
|------|----------|----------|
| 1. 更新测试用例状态 | `TEST_CASES.md` | 将已自动化的用例标记为 ✅，标注对应的 test_xxx 方法名 |
| 2. 更新模块上下文 | `MODULE_CONTEXT.md` | 标记该页面 Phase 3 / 3.5 / 4 完成，记录 Page Object 文件路径 |
| 3. 更新进度追踪 | `测试进度追踪.md` | 标记自动化覆盖进度 |
| 4. 合规检查 | — | 调用 `code-consistency-checker` 检查新生成的代码 |
| 5. CI 更新（如需） | `Jenkinsfile` | 若为全新模块，调用 `jenkinsfile-generator` 更新 CI Pipeline |

**执行方式**：调用 `context-sync` Skill → 调用 `code-consistency-checker` Skill。

## 执行完成后（模块完结步骤）

> ⚠️ 代码生成并提交后，**执行自动化测试**，然后完成以下步骤。

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1. 执行自动化 | `pytest script/<module>/ -v --alluredir=allure-results` | 确保所有用例通过 |
| 2. 生成测试摘要 | 调用 `allure-report-analyzer` | 解析 Allure JSON → `TEST_SUMMARY.md` |
| 3. 导出 Excel 成果 | 调用 `excel-exporter`（场景 C） | Allure JSON + TEST_CASES.md → `governance/kpi/reports/{模块}/测试报告-{模块}.xlsx`（覆盖式） |
| 4. 更新模块状态 | `MODULE_CONTEXT.md` | 标记该模块 Phase 全部完成 ✅ |

> **何时导出 Excel？**
> - 单个模块先完成 → 立即导出 Excel（场景 C），作为模块的工作成果提交
> - 整个版本周期结束 → `test-cycle-closure` Workflow 统一导出所有模块的 Excel




<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: workflow-check -->
## Dependency Check (2026-06-17 16:53)

- [WARN] Deprecated skill refs: element-plus-locator
- [OK] Validated 2026-06-17 16:53

> sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: workflow-check -->