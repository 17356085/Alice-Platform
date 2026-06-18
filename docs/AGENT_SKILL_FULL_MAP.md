# Agent & Skill 全面全景图

> 生成时间: 2026-06-17
> 数据来源: `governance/agents/agent-definitions.yaml` + `agent-definitions-dev.yaml` + `governance/skills/*.md`
> 代码支撑: `aitest/graphs/` + `aitest/agents/`

---

## 一、项目顶层架构

```
WorkStudy/ (AI辅助测试开发工作站)
│
├── aitest/                    ← 核心引擎 (LangGraph + Agent Loop + RAG + MCP)
│   ├── graphs/                ← LangGraph 图定义 (sop_graph, execution_graph, state)
│   ├── agents/                ← Agent 执行循环 (AgentLoop, Skill Executor)
│   ├── llm/                   ← LLM 调用适配层 (Claude/OpenAI/Ollama)
│   ├── mcp/                   ← MCP 协议支持
│   ├── knowledge/             ← RAG 知识引擎
│   └── governance/            ← 治理状态审计
│
├── governance/                ← 治理定义层 (Agent/Skill/Workflow 定义)
│   ├── agents/                ← agent-definitions.yaml (单一事实源)
│   ├── skills/                ← 29 个 Skill Markdown 文件
│   └── context/               ← 项目上下文知识库
│
├── ZJSN_Test-master526/       ← 被测试的 Web 自动化项目 (Selenium + pytest)
│   ├── page/                  ← Page Object
│   └── script/                ← 测试脚本
│
└── docs/                      ← 项目文档
```

### 两套 SOP 体系

| 体系 | 用途 | Agent 数 | Skill 数 | 状态 |
|------|------|:---:|:---:|:---:|
| **Test SOP** | 自动化测试全流程 (测试用例设计→执行→报告) | 8 + 1 编排器 | 29 | ✅ 已落地 |
| **Dev SOP** | 软件开发生命周期 (需求→编码→测试→构建) | 11 + 1 编排器 | 45 (定义) + 0 (文件) | ⚠️ 仅定义 |

---

## 二、Test SOP — 测试自动化全流程

```
Preflight → Project Init → Requirement → Test Design → Automation
    → Execute & Debug → Bug Analysis → Data Sanitization → Report → Knowledge
```

### 2.1 project-agent | 项目 Agent

| 属性 | 值 |
|------|-----|
| **阶段** | Phase 0 (Project Init) |
| **角色** | 资深测试项目架构师 |
| **职责** | 项目初始化、上下文管理、文档审计、目录卫生 |
| **触发词** | 初始化项目 / 更新上下文 / 上次做到哪了 / 卫生检查 / 目录清理 |
| **边界** | 不执行测试 / 不生成自动化代码 / 不分析 Bug |

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `project/project-context-manager` | 项目上下文管理器 | 识别测试项目结构、模块上下文、事实源和迁移边界。从项目结构、SOP/Prompt/README/Jenkins 出发，输出项目索引、模块索引、事实源映射和缺失上下文清单。**规则**：优先引用不急于复制旧资产，模块是治理核心单元。 |
| `project/context-sync` | 上下文同步 | 协作结束后的知识同步：事实更新建议、产物归档建议、待办同步。输入本**轮会话记录和新增事实/文档/脚本，输出应更新的上下文文件、应归档的产物、下一步待办。**规则**：稳定事实→context/，过程产物→artifacts/，迁移→MIGRATION_MAP.md。 |
| `project/hygiene-check` | 目录卫生检查 | 扫描项目目录和治理文件，识别文件级卫生问题。六项检查：重复检测、废弃标记、大文件告警、孤儿引用、格式漂移、Token 预算。输出 PASS/FAIL/WARN 报告，Token 预算 TOP 10。与 `completeness-check` 互补——本 Skill 关注文件健康度而非内容质量。 |
| `knowledge/completeness-check` | 文档完整性检查 | 按 SOP Phase 标准检查模块/页面文档完整性。P0=阻塞测试执行（缺少 PAGE_CONTEXT / TEST_DESIGN），P1=影响质量（缺少 RISK_MODEL / TEST_CASES），P2=锦上添花。输出缺失文档清单+优先级+补充建议。 |

**产物**: 项目索引、模块索引、事实源映射、卫生报告、完整性报告

---

### 2.2 requirement-agent | 需求 Agent

| 属性 | 值 |
|------|-----|
| **阶段** | Phase 0.5~0.8 (Requirement) |
| **角色** | 资深需求分析师 + 测试架构师 |
| **职责** | 从代码反推需求——**无需 PRD**，直接从 Page Object + 测试脚本提取需求 |
| **触发词** | 分析XX模块 / 模块建模 / 需求分析 |
| **边界** | 不涉及页面细节 / 不生成自动化代码 / 不设计测试用例 |

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `requirements/module-modeling` | 模块建模 | 从 `page/<module>_page/` 和 `script/<module>/` 目录实际存在的文件反推 MODULE_CONTEXT.md。**核心规则**：禁止编造页面名（所有子页面需从实际 PO 文件推导）、禁止编造路由（不确定标注"待确认"）、页面状态 ✅/🔄/⏳ 标记。 |
| `requirements/requirement-analysis` | 需求分析 | 双模式：**无 PRD 模式**（默认）→ 从 Page Object 代码+测试脚本+可选 BrowserUse DOM 观测反推页面需求；**PRD 模式**（备用）→ 从 PRD/原型图识别需求风险。输出 PAGE_CONTEXT.md（页面元素清单+业务规则+测试范围）和 PAGE_INTERFACE.yaml。 |

**产物**: MODULE_CONTEXT.md、PAGE_CONTEXT.md、PAGE_INTERFACE.yaml

---

### 2.3 test-design-agent | 测试设计 Agent

| 属性 | 值 |
|------|-----|
| **阶段** | Phase 1~2.5 (Test Design) |
| **角色** | 资深测试分析师 + 质量风险专家 + 业务分析专家 |
| **职责** | 页面分析、风险建模、业务场景建模、测试用例设计（UI操作+业务场景双维度9维覆盖） |
| **触发词** | 看看.*页面.*元素 / 探索.*页面 / 设计测试用例 / 风险建模 / 测试设计 / 业务场景 |

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `test-design/page-analysis` | 页面分析 | 通过截图或 HTML 源码分析页面结构。表格呈现元素清单，定位器 A/B/C 三级优先级（A: data-testid/id/name > B: CSS Selector > C: XPath），识别 Element Plus 组件类型，标注 WebDriverWait 策略。输出 PAGE_CONTEXT.md + PAGE_ELEMENT_POSITION.md。 |
| `test-design/page-observe` | 页面自动探索 | BrowserUse AI Agent 自动探索页面，提取搜索字段/操作按钮/表格列/分页信息——无需人工诊断 DOM。作为 `page-analysis` 的 BrowserUse 驱动后处理。输入 Vue hash 路由（如 `#/warehouse/hazard/item`），输出结构化 PAGE_STRUCTURE.json。 |
| `test-design/risk-modeling` | 风险建模 | 从 6 个维度识别风险：业务、权限、数据、接口、UI/UX、性能。P0/P1/P2 三级，每个 P0 风险必须给出缓解措施。**P2-5 新增**：产出 BUSINESS_SCENARIOS.md（业务目标/角色旅程/工作流/业务规则/数据流），作为 testcase-design 的必选输入。 |
| `test-design/testcase-design` | 测试用例设计 | 从 MODULE_CONTEXT + PAGE_CONTEXT + BUSINESS_SCENARIOS 出发，输出 9 维测试用例（含业务场景验证维度）。**规则**：先场景后步骤，每条用例标注 BS-XXX-NNN 场景 ID 映射。输出 TEST_DESIGN.md + TEST_CASES.md + 自动化优先级建议。 |
| `test-design/test-data-generation` | 测试数据生成 | 为测试场景生成可执行数据。覆盖合法/边界/异常数据，满足所有约束规则，标注数据间依赖关系。输出格式化测试数据表（场景→输入数据→预期结果）。 |
| `test-design/api-testing` | 接口测试设计 | 从 API 文档/Network 抓包设计接口测试。覆盖 5 维度：参数边界、Token 校验、权限校验、异常测试、安全测试（SQL 注入、XSS）。输出 API_TEST_DESIGN.md + 可选 pytest 脚本。 |
| `test-design/miniapp-testing` | 小程序测试 | 微信小程序特有维度：登录态、网络切换（WiFi↔4G/5G）、前后台切换、授权弹窗（位置/相机/存储）、版本兼容性。输出小程序测试用例+特有风险点清单。 |

**产物**: PAGE_CONTEXT.md、PAGE_STRUCTURE.json、RISK_MODEL.md、BUSINESS_SCENARIOS.md、TEST_DESIGN.md、TEST_CASES.md、PAGE_INTERFACE.yaml

---

### 2.4 automation-agent | 自动化 Agent

| 属性 | 值 |
|------|-----|
| **阶段** | Phase 3~4 (Automation) |
| **角色** | 资深 Selenium + pytest 自动化开发专家 |
| **职责** | 技术分析→定位器设计→自动化策略→PageObject/测试脚本生成→合规检查→失败自动修复 |
| **触发词** | 这个按钮.*定位 / 生成.*PageObject / 写.*自动化.*脚本 / 修复.*自动化.*代码 |
| **核心规则** | 先分析后编码（TECH_ANALYSIS → AUTO_STRATEGY → 代码生成），定位器值必须来自真实 HTML，生成后必执行自检 |
| **模式** | `generate`（完整生成） / `fix`（增量修复定位器/等待/选择器/断言，不修改测试逻辑） |

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `automation/tech-analysis` | 技术分析 | 从 HTML 源码+截图分析前端技术实现。先识别 Element Plus 组件类型再设计定位器。定位器 A/B/C 三级评级，异步等待策略覆盖：页面加载、表格刷新、弹窗打开/关闭、loading 消失。输出 TECH_ANALYSIS.md + PAGE_ELEMENT_POSITION.md。 |
| `automation/auto-strategy` | 自动化策略 | 从 TEST_CASES+TECH_ANALYSIS 制定策略。P0 用例必须自动化，不稳定定位器标注风险，一次性操作不建议自动化。PageObject 拆分：一页面一类，复杂弹窗独立。必须给出 ROI 计算。 |
| `automation/page-object-generator` | PageObject 生成器 | 生成符合项目规范的 Page Object Python 文件。**规则**：继承 BasePage、Locator 为类属性元组、CSS Selector 优先、禁止绝对 XPath、不含 assert、不含 time.sleep(>=0.5s)、链式调用。 |
| `automation/test-script-generator` | 测试脚本生成器 | 基于 PageObject+TEST_CASES 生成 pytest 脚本。**规则**：@allure 注解完整、with allure.step() 标记关键步骤、@pytest.mark.smoke 标记冒烟用例、断言含描述信息、附带生成 conftest.py。 |
| `automation/code-consistency-checker` | 代码合规检查器 | **双模式**：`mechanical`（默认，grep 扫描 8 条红线，0 Token，CI/pre-commit 用）和 `review`（LLM 深度审查定位器稳定性/等待策略/断言充分性，~2K Token）。检查编码强制规范和禁止模式。 |

**产物**: TECH_ANALYSIS.md、AUTO_STRATEGY.md、PageObject .py、test_*.py、conftest.py

---

### 2.5 execution-agent | 执行 Agent

| 属性 | 值 |
|------|-----|
| **阶段** | Phase 4.5~7 (Execute & Debug) |
| **角色** | 资深测试执行工程师 |
| **职责** | 测试执行、Allure 报告收集 |
| **触发词** | 运行.*测试 / 执行.*模块 / 跑.*用例 |
| **边界** | 不修改代码 / 不分析失败原因 / 不生成报告 |

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `execution/allure-report-analyzer` | Allure 报告分析器 | 纯文本解析 Allure JSON（不读截图附件），按错误类型分组失败用例（TimeoutException/AssertionError/NoSuchElementException），自动标注不稳定用例（N 次执行状态不一致），与上次构建对比通过率变化/新增失败/修复用例。 |

**产物**: TEST_SUMMARY.md、失败用例分组

---

### 2.6 bug-analysis-agent | Bug 分析 Agent

| 属性 | 值 |
|------|-----|
| **阶段** | Phase 4.5~7 (Bug Analysis) |
| **角色** | 资深测试诊断专家 + CI 工程师 |
| **职责** | 失败根因分析、CI 诊断、批量失败分类 |
| **触发词** | 这个用例.*挂 / 失败.*分类 / Jenkins.*失败 / CI.*诊断 |
| **模式** | `single`（L1.0 反馈循环→L1 深度分析） / `batch`（批量分类可自动修复 vs 非代码问题） |

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `diagnosis/bug-analysis` | Bug 根因分析 | 🔴 MANDATORY 执行流程（不可跳过）：失败现象→标准化 Bug 分析。支持 RAG 自动匹配 known-issues.yaml 中的已知问题。输出根因分类、修复建议、回归建议。 |
| `diagnosis/ci-pipeline-analysis` | CI 流水线分析 | 分析 Jenkins/CI 阶段问题。区分环境/配置/脚本/产品问题，区分并行安全任务与串行破坏性任务。输出阶段问题定位+优化建议+可 Skill 化动作。 |
| `diagnosis/jenkinsfile-generator` | Jenkinsfile 生成器 | 自动识别 `@pytest.mark.destructive` → 串行执行组，无标记→并行执行组（`-n 3 --dist=loadfile`）。保留现有非 pytest 阶段。 |

**产物**: Bug 分析报告、CI 诊断报告、Jenkinsfile 片段

---

### 2.7 report-agent | 报告 Agent

| 属性 | 值 |
|------|-----|
| **阶段** | Phase 8~9 (Report) |
| **角色** | 资深测试报告分析师 |
| **职责** | 测试总结、进度报告、Excel 导出 |
| **触发词** | 生成.*报告 / 导出.*Excel / 测试总结 / 进度.*汇报 |

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `reporting/report-generator` | 统一报告引擎 | 三模式：A (test-summary) 测试周期总结、B (progress) 周度/阶段进度报告+进度追踪更新、C (excel) 测试用例/执行结果导出 .xlsx。 |
| `execution/excel-exporter` | Excel 导出器 | ★ **SOP Phase 9 最终交付物**。合并 TEST_CASES.md + Allure JSON → 综合 .xlsx。微软雅黑字体、蓝色表头(#4472C4)、冻结首行、优先级配色（P0=红/P1=黄/P2=绿）。输出到 `governance/kpi/reports/{模块}/`。 |

**产物**: TEST_SUMMARY.md、进度报告、测试报告-{模块}.xlsx

---

### 2.8 knowledge-agent | 知识 Agent

| 属性 | 值 |
|------|-----|
| **阶段** | 横向贯穿 (Knowledge) |
| **角色** | 资深测试知识管理专家 |
| **职责** | 知识提取、沉淀、审计——**唯一可跨 Agent 写入知识库的 Agent** |
| **触发词** | 沉淀经验 / Bug.*别人.*遇到 / 知识.*提取 / 知识.*审计 |

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `knowledge/knowledge-manager` | 知识全生命周期管理 | **三模式**：A (extract) Bug→知识提取，增量更新 known-issues.yaml；B (precipitate) 测试周期结束批量沉淀，更新 PROJECT_CONTEXT+known-issues+进度追踪；C (event-driven) 监听 Event Bus，自动触发知识沉淀，实现真正的"横向贯穿"。 |

**产物**: known-issues.yaml 更新、PROJECT_CONTEXT 更新、进度追踪更新

---

### 2.9 full-sop | 全流程编排器

| 属性 | 值 |
|------|-----|
| **类型** | 编排器（非独立 Agent） |
| **职责** | 端到端 SOP 编排，按规范 Phase 顺序自动串联 8 个 Agent |
| **模式** | `full` / `resume` / `status` / `from-requirement` / `from-test-design` / `from-automation` |

**Phase 流转表**:

| Phase | Agent | 条件 | 说明 |
|-------|-------|------|------|
| Preflight | — | 隐式 | 前置检查+断点恢复 |
| Project Init | project-agent | PROJECT_CONTEXT 缺失时 | 项目初始化 |
| Requirement | requirement-agent | — | 模块建模+需求分析 |
| Test Design | test-design-agent | per_page | P2-5: 产出 BUSINESS_SCENARIOS + 9 维 TEST_DESIGN |
| Testcase Quality Gate | — | BSC Score≥60 | **质量门禁**，score<60 打回 Test Design 重做（最多 2 轮） |
| Automation | automation-agent | per_page | 技术分析→策略→代码生成 |
| Execute & Debug | execution-agent | — | 失败→bug-analysis-agent→automation-agent(fix)，最多 3 轮 |
| Bug Analysis | bug-analysis-agent | execution_failed | 失败根因分析，最多 3 轮 |
| Data Sanitization | — | — | 离线扫描清理残留数据 |
| Report | report-agent | — | 生成综合 Excel |
| Knowledge | knowledge-agent | — | 知识提取+批量沉淀 |

---

## 三、Dev SOP — 软件开发生命周期

```
Plan → Requirements → Architecture → Component Design → Code(FE+BE) → Review → Test → Debug → Build
```

> ⚠️ **状态**: 11 个 Agent + 45 个 Skill 已在 `agent-definitions-dev.yaml` 中完整定义，但磁盘上 `governance/skills/plan/`、`frontend/`、`backend/` 等目录下**没有任何 .md 文件**——仅定义，未落地。

### 3.1 流程管控层 (5 Agent)

#### pm-agent | 项目管理 Agent (Phase 0)

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `plan/create-project-plan` | 创建项目计划 | 任务分解、里程碑规划 |
| `plan/progress-tracker` | 进度跟踪 | 进度追踪和状态更新 |
| `plan/risk-analyzer` | 风险分析 | 项目风险评估和缓解 |
| `plan/sprint-planner` | Sprint 规划 | 迭代计划分解 |

#### req-agent | 需求分析 Agent (Phase 0.5~1)

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `requirements-dev/feature-spec` | 功能规格 | 功能规格文档编写 |
| `requirements-dev/user-story-writer` | 用户故事 | 用户故事分解 |
| `requirements-dev/acceptance-criteria` | 验收标准 | 验收标准定义 |
| `requirements-dev/data-model-spec` | 数据模型 | 数据模型设计 |
| `automation/prompt-engineering-expert` | PE 优化 | Prompt 工程优化（dair-ai 分类法） |

### 3.2 代码生成层 (4 Agent)

#### arch-agent | 架构 Agent (Phase 1)

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `architecture/project-scanner` | 项目扫描 | 项目代码结构分析 |
| `architecture/tech-stack-decider` | 技术选型 | 技术栈决策 |
| `architecture/component-tree-designer` | 组件树设计 | 组件树结构设计 |
| `architecture/api-contract-designer` | API 契约设计 | API 接口契约定义 |

#### design-agent | 组件设计 Agent (Phase 2)

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `component-design/component-spec` | 组件规格 | 组件结构分析 |
| `component-design/props-interface` | Props 接口 | 组件 Props 定义 |
| `component-design/data-flow` | 数据流 | 数据流设计 |
| `component-design/layout-mockup` | 布局设计 | 页面布局原型 |

#### frontend-agent | 前端开发 Agent (Phase 3)

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `frontend/vue-component-generator` | Vue 组件生成 | Vue 3 + TS 组件代码生成 |
| `frontend/page-implementer` | 页面实现 | 页面级实现 |
| `frontend/vuex-pinia-store` | Pinia Store | 状态管理实现 |
| `frontend/router-config` | 路由配置 | Vue Router 配置 |
| `frontend/frontend-lint-checker` | Lint 检查 | 前端 ESLint+tsc 检查 |

#### backend-agent | 后端开发 Agent (Phase 3)

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `backend/fastapi-router-generator` | Router 生成 | FastAPI 路由生成 |
| `backend/pydantic-schema-generator` | Schema 生成 | Pydantic v2 模型生成 |
| `backend/sqlalchemy-model-generator` | Model 生成 | SQLAlchemy 2.0 模型生成 |
| `backend/crud-generator` | CRUD 生成 | 增删改查操作生成 |
| `backend/unit-test-generator` | 单元测试生成 | 后端 pytest 测试生成 |
| `backend/backend-consistency-checker` | 一致性检查 | 后端代码合规检查 |

### 3.3 质量保障层 (3 Agent)

#### review-agent | 代码审查 Agent (Phase 4)

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `code-review/source-code-reviewer` | 源码审查 | 代码质量审查 |
| `code-review/performance-analyzer` | 性能分析 | 性能瓶颈分析 |
| `code-review/security-scanner` | 安全扫描 | 安全漏洞扫描 |
| `code-review/consistency-enforcer` | 一致性检查 | 前后端一致性 |
| `automation/prompt-engineering-expert` | PE 优化 | Prompt 工程优化 |

#### dev-test-agent | 测试 Agent (Phase 4)

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `test-dev/unit-test-generator` | 单元测试 | 单元测试生成 |
| `test-dev/integration-test-generator` | 集成测试 | 集成测试生成 |
| `test-dev/coverage-checker` | 覆盖率 | 代码覆盖率检查 |

#### debug-agent | 调试 Agent (Phase 5)

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `debug/error-locator` | 错误定位 | 错误精确位置定位 |
| `debug/stack-trace-analyzer` | 堆栈分析 | 调用链分析 |
| `debug/fix-suggester` | 修复建议 | 代码修复方案建议（≤3 轮） |
| `debug/regression-verifier` | 回归验证 | 修复后回归确认 |
| `automation/prompt-engineering-expert` | PE 优化 | Prompt 工程优化 |

#### build-agent | 构建 Agent (Phase 5~6)

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `build/type-checker` | 类型检查 | TypeScript/MyPy 类型检查 |
| `build/lint-executor` | Lint 执行 | ESLint/Ruff 执行 |
| `build/test-runner` | 测试运行 | 测试套件执行 |
| `build/package-bundler` | 打包构建 | 生产构建打包 |

---

## 四、元治理层 — architecture-review-agent | 架构评审 Agent

> **定位**: 元治理——不执行治理，**评估治理的有效性**。
> **阶段**: meta（横向覆盖）

| Skill ID | 中文名 | 说明 |
|----------|--------|------|
| `review/architecture-assessment` | 架构评审 | 系统架构质量评估 |
| `review/tech-debt-inventory` | 技术债务盘点 | 技术债务识别和量化 |
| `review/component-cohesion` | 组件内聚 | 组件内聚性分析 |
| `review/token-efficiency` | Token 效率 | Token 消耗和成本评审 |
| `review/model-selection` | 模型选择 | LLM 模型选型评估 |
| `review/governance-coverage` | 治理覆盖 | 治理体系覆盖度评估 |
| `review/quality-regression-analysis` | 质量回归 | Agent 质量退化分析 |
| `review/sop-effectiveness` | SOP 效能 | 工作流效能评估 |
| `review/prompt-engineering` | Prompt 审查 | Prompt 质量审查 |
| `review/production-readiness` | 生产就绪 | 生产环境就绪度评估 |
| `review/observability-gap` | 可观测性缺口 | 监控和日志覆盖缺口 |
| `review/security-posture` | 安全态势 | 安全防护评估 |
| `review/skill-health` | Skill 健康 | Skill 定义健康检查 |
| `review/agent-health` | Agent 健康 | Agent 运行健康检查 |
| `review/memory-quality` | Memory 质量 | 记忆系统质量评估 |
| `automation/prompt-engineering-expert` | PE 优化 | Prompt 工程优化 |

**事件订阅**:
- `StateDrift` → architecture-assessment
- `SOPViolation` → governance-coverage
- `CostAnomaly` → token-efficiency
- `EvalRegressed` → architecture-assessment
- `PromptChanged` → prompt-engineering + PE Expert
- `AuditCompleted` → knowledge-manager (precipitate)

**评审模式**: `full` / `quick` / `architecture` / `governance` / `cost` / `production`

---

## 五、横向贯穿 Skill

### 5.1 productivity/caveman | 洞穴人模式

> 来源: mattpocock/skills | 适配: AITest Platform

| 属性 | 值 |
|------|-----|
| **功能** | 超压缩通信模式，削减 ~75% token 消耗，保留全部技术精度 |
| **持有者** | 所有 Agent |
| **触发** | 用户说 caveman/洞穴人/less tokens/be brief |
| **级别** | lite (~40% 削减，去礼貌用语) / full (~75%，默认) / ultra (~90%，仅技术关键词) |

### 5.2 automation/prompt-engineering-expert | PE 专家

| 属性 | 值 |
|------|-----|
| **功能** | 应用 dair-ai 分类法的 PE 技术，主动优化 Agent Skill Prompt |
| **持有者** | req-agent / review-agent / debug-agent / architecture-review-agent |
| **触发** | PromptChanged 事件 / Agent 自优化 / 手动调用 |
| **文件** | ❌ 磁盘上不存在（待创建） |

---

## 六、State 管理架构

### SOPState — 所有图的共享类型

```python
class SOPState(TypedDict):
    # ── 运行时标识 ──
    module: str                          # 模块名，覆盖
    pages: List[str]                     # 页面 slug 列表，覆盖
    mode: SOPMode                        # 运行模式，覆盖
    provider: str                        # claude | openai | ollama
    run_id: str                          # 运行 ID

    # ── Phase 状态机 ──
    current_phase: PhaseName             # 当前阶段，覆盖
    completed_phases: Annotated[..., _unique_list]  # 去重累积
    failed_phases: Annotated[..., _unique_list]     # 去重累积
    skip_phases: List[PhaseName]         # 模式决定的跳过列表

    # ── Per-page 迭代 ──
    current_page_index: int              # 0-based 页面游标
    bsc_retry_count: int                 # 质量门禁重试计数
    per_page_results: Annotated[..., operator.add]  # 累积

    # ── Agent 输出 ──
    agent_outputs: Annotated[..., _merge_agent_outputs]  # 深度合并
    artifact_map: Annotated[..., _merge_dict]            # 深度合并
    skill_observations: Annotated[..., _bounded_skill_obs]  # 最近100条

    # ── Bug 循环 + HITL ──
    bug_cycle_count: int
    fix_approved: Optional[bool]         # None=等待中
    auto_strategy_approved: Optional[bool]
    test_cases_approved: Optional[bool]

    # ── 门禁 + 错误 ──
    gate_results: Annotated[..., _bounded_gate_results]  # 最近50条
    fatal_error: Optional[str]
    status: str                          # running | completed | failed | paused
```

### Reducer 类型速查

| Reducer | 行为 | 适用字段 |
|---------|------|----------|
| **覆盖** | 最后写入者胜 | module, current_phase, current_page_index, status |
| `operator.add` | 列表追加 | per_page_results |
| `_unique_list` | 去重追加 | completed_phases, failed_phases |
| `_bounded_skill_obs` | 追加+截断(100条) | skill_observations |
| `_bounded_gate_results` | 追加+截断(50条) | gate_results |
| `_merge_agent_outputs` | 深度合并字典 | agent_outputs |
| `_pick_last` | 取最后值 | human_input, fix_approved |

### CommonSOPStage — 跨 SOP 抽象

```
Test SOP 9 Phase                CommonSOPStage        Dev SOP 10 Phase
─────────────────────────────────────────────────────────────────────
Preflight / Project Init / Req  →  PLAN   ←  Plan / Requirements
Test Design / Automation        →  EXECUTE ←  Arch / Design / FE / BE
Execute & Debug / Bug Analysis  →  VERIFY  ←  Review / Test / Debug
Data Sanitize / Report / Knowl  →  CLOSE   ←  Build
```

---

## 七、项目关系全景图

```
                     ┌──────────────────────────────────────────┐
                     │        full-sop / dev-full-sop            │
                     │         (编排器 — 串联 Agent)              │
                     └────┬─────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                                     │
   Test SOP (落地)                       Dev SOP (定义)
   ┌──────────────────┐              ┌──────────────────────┐
   │ project-agent    │              │ pm-agent             │
   │ requirement-agent│              │ req-agent            │
   │ test-design-agent│              │ arch-agent           │
   │ automation-agent │              │ design-agent         │
   │ execution-agent  │              │ frontend-agent       │
   │ bug-analysis-agent│             │ backend-agent        │
   │ report-agent     │              │ review-agent         │
   │ knowledge-agent  │              │ dev-test-agent       │
   └──────┬───────────┘              │ debug-agent          │
          │                          │ build-agent          │
          │                          └──────────────────────┘
          │                                     │
   ┌──────┴───────────┐              ┌──────────┴───────────┐
   │  29 个 Skill     │              │  45 个 Skill (定义)  │
   │  ✅ 全部有 .md   │              │  ❌ 0 个 .md 文件    │
   └──────────────────┘              └──────────────────────┘
          │                                     │
          └─────────────┬───────────────────────┘
                        │
              ┌─────────┴─────────┐
              │    SOPState       │
              │ (共享数据协议)     │
              └─────────┬─────────┘
                        │
              ┌─────────┴─────────┐
              │    LangGraph      │
              │ (StateGraph 驱动) │
              └─────────┬─────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   AgentLoop       SkillExecutor    RAG Engine
   (Perceive→      (Skill 加载      (知识检索)
    Plan→Act→       + 执行引擎)
    Observe)
        │               │               │
        └───────────────┼───────────────┘
                        │
              ┌─────────┴─────────┐
              │   治理状态审计     │
              │ (state_auditor)   │
              └───────────────────┘
```

---

## 八、已废弃 Skill

| Skill 文件 | 状态 |
|------------|------|
| `_deprecated/page-analysis-v0.9-degraded.md` | 空壳文件，待删除 |
| `test-design/page-analysis-v1.1.md` | 被 `page-analysis.md` 替代（内容相同） |

---

## 九、Skill 目录汇总

| 目录 | 文件数 | Skills |
|------|:---:|--------|
| `automation/` | 5 | tech-analysis / auto-strategy / page-object-generator / test-script-generator / code-consistency-checker |
| `execution/` | 3 | allure-report-analyzer / data-sanitization / excel-exporter |
| `project/` | 3 | project-context-manager / context-sync / hygiene-check |
| `diagnosis/` | 3 | bug-analysis / ci-pipeline-analysis / jenkinsfile-generator |
| `reporting/` | 1 | report-generator |
| `requirements/` | 2 | module-modeling / requirement-analysis |
| `test-design/` | 7 | page-analysis / page-observe / risk-modeling / testcase-design / test-data-generation / api-testing / miniapp-testing |
| `knowledge/` | 2 | completeness-check / knowledge-manager |
| `productivity/` | 1 | caveman |
| `_deprecated/` | 1 | page-analysis-v0.9-degraded |
| **总计** | **28** | (24 active + 4 deprecated/duplicate) |

---

## 十、关键设计决策

1. **单一事实源**：`agent-definitions.yaml` 是 Agent 和 Skill 分配的唯一权威来源，其他文件从此派生。运行 `python -m aitest.check_agent_drift` 检测同步漂移。

2. **Skill 作为能力原子**：每个 Skill 有标准结构（目标/输入/输出/规则/依赖/边界），可被多个 Agent 复用。

3. **双 SOP 共享 State**：Test SOP 和 Dev SOP 通过 `CommonSOPStage` 抽象层共享 State 结构，避免重复设计。

4. **知识 Agent 独占写权限**：只有 knowledge-agent 可以跨 Agent 写入知识库，其他 Agent 只能读取。

5. **横向 Skill 与 PE 专家**：`caveman` 和 `prompt-engineering-expert` 不绑定特定 Agent，可按需加载。

6. **质量门禁 + HITL**：Testcase Quality Gate (BSC Score) + auto_strategy_approved + test_cases_approved 构成三层质量关卡。
