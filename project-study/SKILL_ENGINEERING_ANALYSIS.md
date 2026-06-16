# Skill 工程逆向拆解：24 个 Skill 的完整分析

> **写作目的**: 教学文档。以本项目为真实案例，逐 Skill 分析职责、拆分逻辑、单一职责、复用价值和分类体系。
> **读者假设**: 已了解 Prompt Engineering 基础，希望理解如何系统化地组织和管理大量 Prompt。

---

## 0. 先决知识：为什么 Prompt 需要 "工程化"

在 AI 辅助开发中，你很快会遇到这个问题：

```
第 1 天: "帮我分析这个页面" → 写了一个 Prompt → 效果不错
第 7 天: "帮我分析另一个页面" → 又写了一个 Prompt → 和上次不太一样
第 30 天: 积累了 50 个 Prompt → 格式混乱、重复内容、找不到需要的
```

Skill 工程解决的就是这个问题：**把 Prompt 当作代码一样管理**——版本化、模块化、可复用、可组合。

本项目的 Skill 体系经历了以下演化：

```
原始 Prompt 片段 (散落各处)
  → Prompt 库 (统一收集)
    → Skill 注册表 (结构化索引)
      → 分类体系 (7 分类)
        → 合并/归档 (去重减熵)
```

---

## 1. Skill 的 6 种类型

在逐一分析之前，先定义分类体系。本项目 24 个 Skill 归入 6 种类型：

| 类型 | 核心特征 | 输入→输出 | 是否需要 LLM | 示例 |
|------|---------|----------|:----------:|------|
| **Analysis** | 非结构化→结构化 | 原始材料→分析文档 | ✅ | page-analysis |
| **Generation** | 规范→产物 | 设计+规范→代码/文档 | ✅ | page-object-generator |
| **Strategy** | 多因素→决策 | 分析+约束→策略 | ✅ | auto-strategy |
| **Validation** | 产物→合规报告 | 代码/文档→检查结果 | ✅/❌ | code-consistency-checker |
| **Synthesis** | 多源→聚合 | 多个数据源→统一视图 | ✅ | report-generator |
| **Knowledge** | 实例→模式 | 具体经验→抽象知识 | ✅ | knowledge-manager |

### 关键洞察：不是所有 Skill 都需要 LLM

`code-consistency-checker` 的 **mechanical 模式**是零 Token 的——纯 grep + regex。这体现了 Skill 工程的一个重要原则：

> **如果规则可以写成代码，就不要让 LLM 来执行。**

---

## 2. 7 个分类 × 24 个 Skill = 逐一分析

对每个 Skill，从 7 个维度分析：

| # | 维度 | 问题 |
|---|------|------|
| 1 | 职责 | 这个 Skill 做什么 |
| 2 | 输入 | 消费什么 |
| 3 | 输出 | 产出什么 |
| 4 | 拆分理由 | 为什么独立为一个 Skill 而不是合并到其他 Skill |
| 5 | 单一职责 | 是否满足 SRP |
| 6 | 复用价值 | 能否在其他上下文中复用 |
| 7 | 类型 | 属于哪类 Skill |

---

### 分类 1: project/（项目级上下文管理）

#### Skill ①: project-context-manager

**类型**: Analysis + Generation

**职责**: 从零散的项目结构中提取完整项目上下文，生成 `PROJECT_CONTEXT.md`。

**输入**: 项目结构、代码目录、技术文档、README、Jenkinsfile
**输出**: PROJECT_CONTEXT.md（含模块树、角色权限、技术架构、风险矩阵、自动化优先级）

**拆分理由**: 这是整个 Skill 体系的 **地基**。所有其他 Skill 都直接或间接依赖 PROJECT_CONTEXT.md。如果没有这个 Skill，每个 Skill 都要自己探索项目结构——这是 Skills 之间最大的重复。

**单一职责**: ✅ 满足。职责边界非常明确——只负责 "项目全局上下文" 这一件事。

**复用价值**: ⭐⭐⭐⭐⭐（最高）。任何新模块、新页面、新 Agent 启动都需要它。

---

#### Skill ②: context-sync

**类型**: Synthesis + Knowledge

**职责**: 在会话结束后同步上下文——判断哪些是 "稳定事实"（应进入 context/）、哪些是 "过程产物"（应进入 artifacts/）、生成 CURRENT_TASK.md 供下次会话恢复。

**输入**: 会话记录、新增/修改文件、Phase 进展、关键决策、遗留问题
**输出**: CURRENT_TASK.md、更新的进度追踪、MODULE_CONTEXT.md 状态标记更新

**拆分理由**: 上下文同步与上下文创建是两个不同的关注点。project-context-manager 是 "从零创建"，context-sync 是 "增量同步"。两者解决的问题不同：
- project-context-manager: "这个项目是什么样的？"
- context-sync: "上次做到哪了？现在应该从哪里继续？"

**单一职责**: ✅ 满足。只做 "本次会话内容→下次会话可恢复" 这一件事。

**复用价值**: ⭐⭐⭐⭐⭐。每个 Agent、每个模块、每次会话都需要它。

---

### 分类 2: requirements/（需求分析与模块建模）

#### Skill ③: module-modeling

**类型**: Analysis

**职责**: 为单个模块建立模块级上下文文档（MODULE_CONTEXT.md），包括子页面清单、业务流程图、数据对象、权限矩阵、模块级风险点。

**输入**: PROJECT_CONTEXT.md、模块名称、模块入口 URL
**输出**: MODULE_CONTEXT.md

**拆分理由**: 模块级上下文与项目级上下文有本质区别：
- PROJECT_CONTEXT.md: 全项目视角（所有模块、宏观架构）
- MODULE_CONTEXT.md: 单模块视角（子页面、页面关系、模块内业务流程）

如果合并，PROJECT_CONTEXT.md 会膨胀到数千行，且每增加一个模块就要修改全局文档——违反开闭原则。

**单一职责**: ✅ 满足。只做 "一个模块的上下文建模"。

**复用价值**: ⭐⭐⭐⭐。每个模块都需要，是下游 test-design/automation 的强制前置依赖。

---

#### Skill ④: requirement-analysis

**类型**: Analysis

**职责**: 从 PRD、原型图或产品说明出发，进行测试视角的需求分析——提取业务规则、界定测试范围、识别需求风险、制定测试策略。

**输入**: PRD/原型图/产品说明、MODULE_CONTEXT.md
**输出**: REQUIREMENT_ANALYSIS.md（需求理解摘要、业务规则清单、测试范围、风险点、测试策略）

**拆分理由**: 需求分析与模块建模是两种不同的分析：
- module-modeling: "这个模块有什么？"（结构分析）
- requirement-analysis: "这个需求要什么？"（意图分析）

结构分析基于代码/目录，意图分析基于 PRD/文档。输入来源完全不同，合并会导致一个 Skill 处理两种异质的输入。

**单一职责**: ⚠️ 部分满足。这个 Skill 产出较多（需求理解+规则提取+范围界定+风险评估+策略建议），但这些都是围绕同一个目标——"理解需求对测试的影响"。如果进一步拆分，可以考虑 "需求风险分析" 独立，但当前粒度合理。

**复用价值**: ⭐⭐⭐。每个功能需求都需要，但不是每个模块都有 PRD。

---

### 分类 3: test-design/（测试分析与设计）

#### Skill ⑤: page-analysis

**类型**: Analysis

**职责**: 通过页面截图或 HTML 源码分析页面结构、元素清单和元素定位器。产出 PAGE_CONTEXT.md 和 PAGE_ELEMENT_POSITION.md。

**输入**: 页面截图（1-3 张）或 HTML 源码、页面名称/URL、MODULE_CONTEXT.md
**输出**: PAGE_CONTEXT.md + PAGE_ELEMENT_POSITION.md + PAGE_INTERFACE.yaml（P1-2 新增自动后处理）

**拆分理由**: 页面分析是测试设计的 **第一步和最具依赖性的步骤**。所有后续的 risk-modeling、testcase-design、tech-analysis 都依赖 PAGE_CONTEXT.md。如果和分析合并，就无法独立重用页面分析结果。

P1-2 合并 page-interface-generator 的决策值得分析：PAGE_INTERFACE.yaml 是 page-analysis 的自然产物（从 PAGE_CONTEXT.md 自动提取），不是独立任务，合并是正确的。

**单一职责**: ✅ 满足。只做 "这个页面上有什么元素" 这一件事。

**复用价值**: ⭐⭐⭐⭐⭐。一个页面分析可供 risk-modeling、testcase-design、tech-analysis 三个下游 Skill 消费。

---

#### Skill ⑥: risk-modeling

**类型**: Analysis

**职责**: 从页面上下文出发，从 6 个维度（业务/权限/数据/接口/UI-UX/性能）识别风险，输出风险模型。

**输入**: PAGE_CONTEXT.md、MODULE_CONTEXT.md、历史缺陷记录、权限矩阵
**输出**: RISK_MODEL.md（含风险 ID、等级 P0/P1/P2、缓解措施）

**拆分理由**: 风险建模是测试设计中的 **独立子任务**。它需要不同的思维模式——不是 "页面上有什么"，而是 "什么会出错"。而且它的输出（风险模型）直接影响 testcase-design 的优先级分配。

**单一职责**: ✅ 满足。只做 "识别风险" 这一件事。

**复用价值**: ⭐⭐⭐。风险分析和测试设计强关联，但在安全测试、架构评审等场景也可复用。

---

#### Skill ⑦: testcase-design

**类型**: Generation（基于分析的设计）

**职责**: 从页面上下文和风险模型出发，输出完整测试设计和详细测试用例表。

**输入**: PAGE_CONTEXT.md、RISK_MODEL.md、MODULE_CONTEXT.md、需求说明
**输出**: TEST_DESIGN.md + TEST_CASES.md + 自动化优先级建议

**拆分理由**: 这是 "测什么" 的核心 Skill。拆分出来是因为：
1. 它消费两个上游 Skill（page-analysis + risk-modeling）的产出
2. 它产出两个文档（TEST_DESIGN + TEST_CASES），体量很大
3. 测试设计本身是一项专业技能，需要专门的 Prompt 工程

**单一职责**: ⚠️ 工作量较大但逻辑内聚。同时产出 TEST_DESIGN.md 和 TEST_CASES.md，可以考虑拆分为 test-design（测试策略）和 test-case-generation（用例表），但当前 TEST_DESIGN → TEST_CASES 是自然的级联关系，拆分反而增加编排复杂度。

**复用价值**: ⭐⭐⭐⭐。每个页面都需要。

---

#### Skill ⑧: test-data-generation

**类型**: Generation

**职责**: 为测试场景生成可执行的测试数据，覆盖合法数据、边界数据、异常数据。

**输入**: TEST_CASES.md（测试数据列）、数据约束规则
**输出**: 格式化测试数据表 + Python 测试数据模块（可选）

**拆分理由**: 测试数据生成是一个 **专业化任务**。它需要理解数据约束（长度、格式、唯一性、依赖关系），覆盖三类数据（合法/边界/异常），这在测试工程中是独立技能。如果合并到 testcase-design，会导致 testcase-design 的 Prompt 过长。

**单一职责**: ✅ 满足。只做 "生成测试数据"。

**复用价值**: ⭐⭐⭐。不仅测试设计需要，手动测试、数据迁移测试也可复用。

---

#### Skill ⑨: api-testing

**类型**: Analysis + Generation

**职责**: 从 API 文档或 Network 抓包出发，设计接口测试方案（5 维覆盖：参数边界、Token 校验、权限校验、异常测试、安全测试）。

**输入**: API 文档/Network 抓包、PAGE_CONTEXT.md
**输出**: API_TEST_DESIGN.md + 接口测试脚本（可选）

**拆分理由**: API 测试与 UI 测试的思维模式完全不同。UI 测试关心 "用户看到什么"，API 测试关心 "数据如何流转"。合并到一个 Skill 会导致 Prompt 膨胀和关注点混乱。

**单一职责**: ✅ 满足。只做 "API 层面的测试设计"。

**复用价值**: ⭐⭐⭐。有 API 的模块都需要，但纯前端项目不需要。

---

#### Skill ⑩: miniapp-testing

**类型**: Analysis + Generation

**职责**: 为微信小程序设计测试用例，关注小程序特有维度（登录态、网络切换、前后台切换、授权弹窗、分享）。

**输入**: 小程序页面截图、用户操作手册
**输出**: 小程序测试用例 + 小程序特有风险点清单

**拆分理由**: 小程序测试和 Web 端测试有 40% 不同的关注点（微信登录态、授权、网络切换、页面栈、兼容性）。如果合并到 testcase-design，会导致 Web 端 Prompt 中混杂大量小程序特有内容。

**单一职责**: ✅ 满足。只做 "小程序特有的测试设计"。

**复用价值**: ⭐⭐。仅适用于小程序测试场景。

---

### 分类 4: automation/（自动化技术与代码生成）

#### Skill ⑪: tech-analysis

**类型**: Analysis

**职责**: 从页面 HTML 源码分析前端技术实现——Element Plus 组件识别、DOM 结构分析、定位器设计表（A/B/C 三级）、Vue 异步等待策略。

**输入**: 页面 HTML 源码、PAGE_CONTEXT.md
**输出**: TECH_ANALYSIS.md（含组件识别、DOM 分析、定位器设计表、等待策略）

**拆分理由**: 技术分析与页面分析（page-analysis）的关键区别：

| | page-analysis | tech-analysis |
|---|-------------|--------------|
| 关注 | 页面上有什么元素 | 如何定位这些元素 |
| 输入 | 截图（视觉） | HTML 源码（技术） |
| 产出 | 元素清单 | 定位器设计表 + 等待策略 |
| 消费方 | 测试设计 | 代码生成 |

合并会导致一个 Skill 同时处理 "业务视角" 和 "技术视角"——这是两种不同的专业技能。

P1-2 合并 element-plus-locator 的决策：深度定位能力（处理 Teleport、动态 class、级联选择器等）是 tech-analysis 的核心能力，独立 Skill 粒度太细，合并是正确的。

**单一职责**: ✅ 满足。只做 "技术实现分析 + 定位器设计"。

**复用价值**: ⭐⭐⭐⭐。每个页面的自动化都需要。

---

#### Skill ⑫: auto-strategy

**类型**: Strategy

**职责**: 从测试用例和技术分析出发，制定自动化覆盖策略——哪些用例自动化、哪些不自动化及原因、PageObject 拆分方案、ROI 分析。

**输入**: TEST_CASES.md、TECH_ANALYSIS.md、BasePage 能力清单
**输出**: AUTO_STRATEGY.md（自动化覆盖矩阵、PageObject 拆分方案、ROI 计算）

**拆分理由**: 策略制定是一个**决策任务**，与执行任务（代码生成）需要分开。策略回答 "应该怎么做"，代码生成回答 "具体怎么写"。而且策略是人可以 review 的——在代码生成之前确认策略可以避免大量返工。

**单一职责**: ✅ 满足。只做 "决定自动化策略"。

**复用价值**: ⭐⭐⭐⭐。每个页面自动化前都需要。

---

#### Skill ⑬: page-object-generator

**类型**: Generation

**职责**: 基于技术分析和自动化策略，生成符合项目规范的 Page Object Python 文件（8 条红线自检内置）。

**输入**: TECH_ANALYSIS.md（定位器设计表）、AUTO_STRATEGY.md（拆分方案）、PROJECT_CONTEXT.md（BasePage API + 编码规范）
**输出**: Page Object Python 文件（单文件）

**拆分理由**: Page Object 生成和测试脚本生成是两个不同的任务：
- Page Object: 封装页面操作（导航、搜索、填表、点击）
- 测试脚本: 编排 Page Object 操作 + 断言 + Allure 注解

两者复用不同的模板，遵循不同的编码规范，产出到不同的目录。拆分后每个 Skill 的 Prompt 更聚焦。

**单一职责**: ✅ 满足。只做 "生成一个 Page Object 文件"。

**复用价值**: ⭐⭐⭐⭐⭐。每个页面的自动化都需要。

---

#### Skill ⑭: test-script-generator

**类型**: Generation

**职责**: 基于 Page Object 和 TEST_CASES，生成 pytest 测试脚本（含 Allure 注解、pytest marker、fixture 使用）。P1-2 合并了 conftest-generator。

**输入**: Page Object 类定义、TEST_CASES.md、conftest.py
**输出**: test_*.py 测试脚本 + conftest.py（附带）

**拆分理由**: 见 page-object-generator 的拆分理由。

P1-2 合并 conftest-generator 的决策分析：
- conftest.py 是测试脚本的 **基础设施**——它和 test_*.py 共享模块上下文
- 单独拆分 Skill 粒度过细（conftest.py 通常只有 20-40 行）
- 合并后减少了 Agent 编排的复杂度

**单一职责**: ✅ 满足。只做 "生成测试脚本 + 配套 conftest"。

**复用价值**: ⭐⭐⭐⭐⭐。每个页面的自动化都需要。

---

#### Skill ⑮: code-consistency-checker

**类型**: Validation（双模式：mechanical + review）

**职责**: 检查 Page Object 和测试脚本是否遵循编码强制规范（8 条红线 + PageObject 规范 8 项 + 测试脚本规范 6 项 + 禁止模式 6 项）。

**输入**: Page Object .py 或测试脚本 .py、coding-standards.md
**输出**: 合规检查表（✅/❌/⚠️）、违规位置（文件名:行号）、修复建议、合规度评分

**拆分理由**: 代码检查应该独立于代码生成。原因：
1. 检查逻辑是确定性的——不需要和生成逻辑耦合
2. 可以被不同 Agent 复用（automation-agent 自检、bug-analysis-agent 检查修复后的代码、CI 检查）
3. mechanical 模式零 Token，独立 Skill 可以独立执行

双模式设计（P2-7）是 Skill 工程的高级实践——同一个 Skill 有两种执行方式，由调用方选择。

**单一职责**: ✅ 满足。只做 "代码合规检查"。

**复用价值**: ⭐⭐⭐⭐⭐。CI、pre-commit、Agent 自检、Bug 修复验证都需要。

---

#### Skill ⑯: conftest-generator (DEPRECATED → 合并到 test-script-generator)

**归档原因**: 粒度过细。conftest.py 是测试脚本基础设施的一部分，单独作为 Skill 增加了编排复杂度。

**教训**: 当一个 Skill 的产出只有 20-40 行代码，且总是和另一个 Skill 一起使用时，它应该被合并。

---

### 分类 5: execution/（执行与报告）

#### Skill ⑰: allure-report-analyzer

**类型**: Analysis（纯文本解析，不依赖 LLM 视觉）

**职责**: 解析 Allure 原始 JSON 结果文件，生成结构化测试摘要——通过率、失败分布、耗时趋势、不稳定用例、与上次构建对比。

**输入**: allure-results/*-result.json、历史对比基线
**输出**: TEST_SUMMARY.md（通过率、失败分组、模块分布、不稳定用例清单、趋势对比）

**拆分理由**: Allure JSON 解析是一个**纯数据处理**任务，不涉及 LLM 决策。独立 Skill 可以：
1. 在 execution-agent 运行后自动执行
2. 在 report-agent 的 report-generator 中被复用
3. 在 CI pipeline 中作为独立步骤

**单一职责**: ✅ 满足。只做 "解析 Allure JSON → 结构化摘要"。

**复用价值**: ⭐⭐⭐⭐。每次执行后都需要。

---

#### Skill ⑱: excel-exporter

**类型**: Synthesis（数据→格式化文件）

**职责**: 将 TEST_CASES.md 与 Allure JSON 合并为带格式的中文 Excel 文件——SOP 最终交付物。

**输入**: TEST_CASES.md + allure-results/*-result.json
**输出**: 测试报告-{模块}-{日期}.xlsx（三场景：仅用例表/仅执行结果/综合报告）

**拆分理由**: Excel 导出是独特的技能——需要 openpyxl 格式化（字体、颜色、边框、冻结、合并单元格），这些与 report-generator 的文字报告生成是完全不同的技能。独立 Skill 可以：
1. 被 report-agent 作为核心 Skill
2. 被手动调用（"导出 XX 模块的 Excel"）
3. 在 CI 中作为构建后步骤

**单一职责**: ✅ 满足。只做 "生成格式化 Excel 文件"。

**复用价值**: ⭐⭐⭐。Excel 导出是高频需求，但主要限于测试报告场景。

---

### 分类 6: diagnosis/（Bug 诊断与 CI 分析）

#### Skill ⑲: bug-analysis

**类型**: Analysis（L0 RAG 自动匹配 + L1 深度分析）

**职责**: 将失败现象转化为标准化 Bug 分析结论。L0 强制 RAG 已知问题匹配，L1 执行 5 层递进排查（定位器→等待→数据→环境→产品 Bug）。

**输入**: 失败日志、截图、复现步骤、代码上下文、CI 结果
**输出**: BUG_ANALYSIS.md（现象描述、根因分类、修复建议、回归影响范围）

**拆分理由**: Bug 分析是一个**高复杂度的诊断任务**，必须独立：
1. 有自己的强制执行流程（L0 RAG → 降级规则 → L1 深度分析）
2. 有自己的专业知识（5 层递进排查法）
3. 支持 single 和 batch 两种模式
4. 有自己的输出模板（BUG_ANALYSIS.md）

**单一职责**: ✅ 满足。只做 "分析失败根因"。

**复用价值**: ⭐⭐⭐⭐⭐。每次测试失败都需要。

---

#### Skill ⑳: ci-pipeline-analysis

**类型**: Analysis

**职责**: 分析 Jenkins/CI 流水线的阶段问题、失败模式和改进点——定位失败阶段、区分环境/配置/脚本/产品问题、给出优化建议。

**输入**: Jenkinsfile、构建日志、测试报告、环境参数
**输出**: 阶段问题定位、失败归类、优化建议

**拆分理由**: CI 诊断和 Bug 诊断是不同的：
- bug-analysis: 聚焦单个测试用例为什么失败
- ci-pipeline-analysis: 聚焦 CI 流水线本身的健康度

CI 分析需要理解 Jenkins stage 结构、并行/串行分组、超时配置、产物归档——这些是 DevOps 技能而非测试技能。

**单一职责**: ✅ 满足。只做 "CI 流水线健康分析"。

**复用价值**: ⭐⭐。CI 配置变更时才需要，但分析结果长期有效。

---

#### Skill ㉑: jenkinsfile-generator

**类型**: Generation

**职责**: 根据模块测试脚本自动生成或更新 Jenkinsfile 中的 pytest 执行配置——自动扫描 marker 区分安全/破坏性用例，生成并行/串行 stage。

**输入**: 现有 Jenkinsfile、模块测试脚本目录、pytest marker 信息
**输出**: 更新后的 Jenkinsfile 片段（含正确的 stage 分组）

**拆分理由**: Jenkinsfile 生成是 CI 特有的代码生成任务。它的知识域是 Groovy + Jenkins Pipeline DSL + pytest marker 约定，与 Page Object 生成或测试脚本生成完全不同。

**单一职责**: ✅ 满足。只做 "生成/更新 Jenkinsfile"。

**复用价值**: ⭐⭐。新增模块或 CI 配置变更时才需要。

---

### 分类 7: knowledge/（知识管理）

#### Skill ㉒: knowledge-manager

**类型**: Knowledge

**职责**: 知识全生命周期管理，支持三种模式：
- **extract**: Bug → 坑位提取 → known-issues.yaml 更新
- **precipitate**: 测试周期结束 → 批量知识沉淀 → 多文件同步
- **event-driven**: Event Bus 事件 → 自动触发知识动作

**输入**: BUG_ANALYSIS.md / 周期汇总数据 / Event Bus 事件
**输出**: known-issues.yaml 更新、PROJECT_CONTEXT.md 坑位清单同步、进度追踪更新

**拆分理由**: 知识管理是整个系统唯一的 **横向贯穿** Skill。它不能合并到任何 Agent 的 Skill 链中，因为：
1. 它是唯一有跨 Agent 写入权限的 Skill
2. 它需要维护去重优先级规则
3. 它的三种模式覆盖了完全不同的触发场景

这是 Skill 工程中的 **唯一写入原则** 在 Skill 层面的体现。

**单一职责**: ✅ 满足。只做 "知识管理"（提取、沉淀、去重、同步）。

**复用价值**: ⭐⭐⭐⭐⭐。横向贯穿所有 Agent。

---

#### Skill ㉓: completeness-check

**类型**: Validation

**职责**: 检查模块/页面的文档完整性——按 SOP Phase 标准检查每个 Phase 的产物是否存在，标注缺失优先级（P0/P1/P2）。

**输入**: context/projects/*/modules/ 目录结构
**输出**: 文档完整性报告 + 缺失文档清单 + 补充建议

**拆分理由**: 完整性检查是**元级别的验证**——它不检查内容质量（那是各 Skill 自己的职责），只检查 "文档是否存在"。它被两个 Agent 使用（Project Agent 作为 Primary Owner + Knowledge Agent 作为 Secondary Owner），必须独立。

**单一职责**: ✅ 满足。只做 "检查文档是否存在"。

**复用价值**: ⭐⭐⭐⭐。preflight 检查、周期结束审计、Agent 门禁都需要。

---

### 分类 8: reporting/（进度与报告）

#### Skill ㉔: report-generator

**类型**: Synthesis

**职责**: 统一报告生成引擎，三种模式：
- **test-summary**: 测试周期总结 → TEST_SUMMARY.md（含上线建议）
- **progress**: 周度进度报告 + 进度追踪更新
- **excel**: 调用 excel-exporter 导出 Excel

**输入**: 测试执行数据 + Bug 统计 + 进度追踪
**输出**: TEST_SUMMARY.md / 进度报告 / Excel 文件

**拆分理由**: 报告生成是 SOP 最后一步（Phase 8），需要**聚合所有上游 Agent 的产出**。它是一个 Synthesis Skill——消费多源数据，产出统一视图。与单个 Analysis Skill 的本质区别在于它不分析新事物，而是**重新组织和呈现已有信息**。

**单一职责**: ✅ 满足。只做 "生成报告"。

**复用价值**: ⭐⭐⭐⭐。每次测试周期结束都需要。

---

## 3. Skill 设计模式提炼

从以上分析可以提炼出 5 个 Skill 设计模式：

### 模式 1: 管道模式 (Pipeline Pattern)

上游 Skill 产出文档 → 下游 Skill 消费文档：

```
module-modeling → page-analysis → risk-modeling → testcase-design → test-data-generation
                                          ↓
                                    tech-analysis → auto-strategy → page-object-generator → test-script-generator → code-consistency-checker
```

**关键约束**: 下游 Skill 的 `depends_on` 字段显式声明依赖，Agent 的 L2 门禁检查前置产物是否存在。

### 模式 2: 多模式 Skill (Multi-Mode Pattern)

一个 Skill 支持多种执行模式，由调用方通过 `mode` 参数选择：

| Skill | 模式 | 选择方式 |
|-------|------|---------|
| knowledge-manager | extract / precipitate / event-driven | 调用方传入 mode |
| report-generator | test-summary / progress / excel | 调用方传入 mode |
| code-consistency-checker | mechanical / review | AgentLoop 默认 mechanical，编排层可选 review |

**设计理由**: 多模式避免了 Skill 数量膨胀。如果每种模式都独立一个 Skill，Skill 注册表会从 24 个膨胀到 35+ 个。

### 模式 3: 机械化降级 (Mechanical Fallback Pattern)

`code-consistency-checker` 的 mechanical 模式是零 Token 的 grep 扫描。这体现了：

> **能用确定性代码完成的检查，不要用概率性 LLM 完成。**

应用到其他 Skill 的判断标准：
- 规则可以用正则/code 表达？→ 优先机械模式
- 需要理解语义/上下文？→ 使用 LLM

### 模式 4: Primary Owner 模式

跨 Agent 共享的 Skill 有明确的 Primary Owner：

| Skill | Primary Owner | Secondary Owner |
|-------|--------------|-----------------|
| completeness-check | project-agent | knowledge-agent |
| report-generator | report-agent | — |
| knowledge-manager | knowledge-agent | — |

**设计理由**: 每个 Skill 有唯一负责人，负责其 Prompt 模板的维护和优化。

### 模式 5: 归档合并模式 (Deprecation & Merge Pattern)

Skill 体系的熵增管理——6 个 Skill 被归档/合并：

| 废弃 Skill | 归宿 | 原因 |
|-----------|------|------|
| code-generation | → page-object-generator + test-script-generator | 职责过宽 |
| element-plus-locator | → tech-analysis | 粒度太细 |
| knowledge-extractor | → knowledge-manager (mode: extract) | 多模式统一 |
| knowledge-precipitation | → knowledge-manager (mode: precipitate) | 多模式统一 |
| test-summary | → report-generator (mode: test-summary) | 多模式统一 |
| progress-report | → report-generator (mode: progress) | 多模式统一 |
| conftest-generator | → test-script-generator (附带产出) | 粒度过细 |
| page-interface-generator | → page-analysis (后处理) | 自然附属 |

**教训**: 
- **拆分过细** 和 **拆分不足** 是两个方向的错误
- 拆分过细的信号：两个 Skill 总是一起调用、产出物总是关联的
- 拆分不足的信号：Skill 的 Prompt 模板超过 200 行、输入类型多于 3 种

---

## 4. 单一职责审计

对每个 Skill 的 SRP 评估：

| Skill | SRP | 备注 |
|-------|:---:|------|
| project-context-manager | ✅ | 只做项目上下文 |
| context-sync | ✅ | 只做会话同步 |
| module-modeling | ✅ | 只做模块建模 |
| requirement-analysis | ⚠️ | 产出较多但逻辑内聚 |
| page-analysis | ✅ | 只做页面元素分析 |
| risk-modeling | ✅ | 只做风险识别 |
| testcase-design | ⚠️ | 同时产出 DESIGN + CASES，可接受的内聚 |
| test-data-generation | ✅ | 只做数据生成 |
| api-testing | ✅ | 只做 API 测试设计 |
| miniapp-testing | ✅ | 只做小程序测试设计 |
| tech-analysis | ✅ | 只做技术实现分析 |
| auto-strategy | ✅ | 只做自动化策略 |
| page-object-generator | ✅ | 只做 Page Object 生成 |
| test-script-generator | ✅ | 只做测试脚本 + conftest |
| code-consistency-checker | ✅ | 只做合规检查 |
| allure-report-analyzer | ✅ | 只做 Allure JSON 解析 |
| excel-exporter | ✅ | 只做 Excel 生成 |
| bug-analysis | ✅ | 只做失败根因分析 |
| ci-pipeline-analysis | ✅ | 只做 CI 分析 |
| jenkinsfile-generator | ✅ | 只做 Jenkinsfile 生成 |
| knowledge-manager | ✅ | 只做知识管理 |
| completeness-check | ✅ | 只做完整性检查 |
| report-generator | ✅ | 只做报告生成 |

**总体评价**: 24 个 Skill 中 22 个满足严格的单一职责，2 个（requirement-analysis、testcase-design）产出略多但逻辑高度内聚。这是一个相当健康的 Skill 体系。

---

## 5. Skill 依赖图

```
                    project-context-manager
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        module-modeling  context-sync  completeness-check
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
page-analysis  requirement-analysis  api-testing
    │                                 miniapp-testing
    ├──────────┐
    ▼          ▼
risk-modeling  (page-interface-generator → 已合并)
    │
    ▼
testcase-design
    │
    ├──────────┐
    ▼          ▼
test-data-generation  tech-analysis
                         │
                         ▼
                    auto-strategy
                         │
                    ┌────┴────┐
                    ▼         ▼
          page-object-generator  (conftest-generator → 已合并)
                    │
                    ▼
          test-script-generator
                    │
                    ▼
          code-consistency-checker

          ── 执行层（不参与依赖链）──
          allure-report-analyzer → report-generator → excel-exporter
          bug-analysis → knowledge-manager
          ci-pipeline-analysis → jenkinsfile-generator
```

---

## 6. Skill vs Agent vs Workflow 的关系

这是理解整个治理体系的关键：

```
Workflow:     定义 "流程" — 输入→步骤→输出→门禁（What should happen）
               例如: automation-implementation workflow 定义了 自动化实现的输入输出和门禁

Agent:        执行 "流程" — 决定何时调用哪个 Skill（When to do what）
               例如: automation-agent 按 tech-analysis → auto-strategy → page-object-generator → test-script-generator → code-consistency-checker 的顺序执行

Skill:        执行 "步骤" — 完成单个原子任务（How to do it）
               例如: page-object-generator Skill 知道如何从 TECH_ANALYSIS 生成 Page Object 代码
```

**类比**: Workflow = 菜谱 → Agent = 厨师 → Skill = 刀工/火候/调味

---

> **文档版本**: 2026-06-14 · 基于项目 Skill 体系 v2.0 (24 active + 8 deprecated) · 纯教学用途
