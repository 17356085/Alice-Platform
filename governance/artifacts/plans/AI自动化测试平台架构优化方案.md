# AI自动化测试平台架构优化方案

> 版本：v1.0 | 日期：2026-06-11 | 作者：AI 架构分析
> 基于 governance/ 全量资产深度审计

---

## 目录

1. [第一部分：成熟度评估](#一成熟度评估)
2. [第二部分：架构审计](#二架构审计)
3. [第三部分：Skill架构优化](#三skill架构优化)
4. [第四部分：Agent架构优化](#四agent架构优化)
5. [第五部分：知识库设计](#五知识库设计)
6. [第六部分：自动化测试平台设计](#六自动化测试平台设计)
7. [第七部分：扩展能力分析](#七扩展能力分析)
8. [第八部分：路线图规划](#八路线图规划)

---

## 一、成熟度评估

### 1.1 Context 成熟度：⭐ Level 3 — "已结构化但局部碎片化"

| 维度 | 评分 | 说明 |
|------|------|------|
| 项目级上下文 | ✅ 良好 | [PROJECT_CONTEXT.md](governance/context/projects/web-automation/PROJECT_CONTEXT.md) 200+行，含 BasePage API 参考、Element Plus 坑位、编码规范 |
| 模块级上下文 | ⚠️ 不均衡 | MODULE_INDEX 已映射 7 个模块，但仅 tank 模块全闭环，其余模块 PAGE_CONTEXT 等缺失 |
| 页面级上下文 | ⚠️ 覆盖率低 | 7 个模块仅部分页面有 PAGE_CONTEXT，大部分未达到可进入设计阶段的完整度 |
| 事实源规则 | ✅ 清晰 | source-of-truth.md 定义了唯一事实源，但"旧资产在 TestIntern_library"的过渡期仍在持续 |
| 跨项目复用 | ❌ 缺失 | Web 项目和小程序项目的 Context 完全独立，无共享层 |
| 版本化/变更追踪 | ❌ 缺失 | Context 无变更历史，无法回溯"谁在何时因为什么修改了什么" |

**关键差距**：当前 Context 是"骨架完整、血肉不均"——Tank 模块 13 个文档全闭环证明了模型可行，但其他 6 个模块远未达到同等完整度。

### 1.2 Workflow 成熟度：⭐ Level 3 — "流程定义完整但执行依赖人工"

| 维度 | 评分 | 说明 |
|------|------|------|
| 流程覆盖 | ✅ 良好 | 10 Phase SOP 完整，9 个 Workflow 注册覆盖从项目接管到测试闭环 |
| 自动化程度 | ⚠️ 半自动 | Workflow 定义存在，但 Phase 间状态传递依赖人工阅读文档，无自动流转 |
| 门禁规则 | ✅ 良好 | 分析 Agent 含门禁（PAGE_CONTEXT < 60% 禁止进入风险建模），但多为软约束 |
| 异常路径 | ❌ 缺失 | 无回退/重试/降级路径——某个 Phase 失败后如何恢复到前一 Phase？ |
| 并行化 | ❌ 未定义 | 所有 Workflow 串行，但 testcase-design 和 tech-analysis 可并行执行 |
| 可观测性 | ❌ 缺失 | 无法实时追踪"当前哪个模块在哪个 Phase，谁在操作" |

**关键差距**：Workflow 定义是"文档级"的而非"执行级"的。它们更像 SOP 指南而非可被机器驱动的 DAG。

### 1.3 Skill 成熟度：⭐ Level 4 — "丰富但需归类优化"

| 维度 | 评分 | 说明 |
|------|------|------|
| 覆盖率 | ✅ 优秀 | 29 个 Skill (26 active)，覆盖从项目初始化到知识沉淀的全链路 |
| Prompt 质量 | ✅ 良好 | 每个 Skill 含完整 Prompt 模板 + 检查清单 + 约束规则 |
| 分类体系 | ⚠️ 混乱 | skill-registry.yaml 使用 6 个 category，但子目录仅 2 个(automation/debug)，其余 17 个平铺在 skills/ 根目录 |
| 去重 | ⚠️ 有冗余 | code-generation（deprecated）与 3 个子 Skill 并存；tech-analysis 与 element-plus-locator 定位能力重叠 |
| 边界定义 | ✅ 良好 | 每个 Skill 有"边界"章节，明确职责范围 |
| 可组合性 | ⚠️ 弱 | Skill 之间无标准化的组合/编排接口，Agent 层手工编排 |

**关键差距**：Skill 质量高但管理混乱——缺少统一的分类目录、部分 Skill 已废弃但文件仍在、子目录结构不反映逻辑分类。

### 1.4 Agent 成熟度：⭐ Level 3 — "架构清晰但未完全落地"

| 维度 | 评分 | 说明 |
|------|------|------|
| 角色分工 | ✅ 优秀 | 4 Agent (分析/设计/编码/诊断) 覆盖完整链路，职责边界清晰 |
| 双通道 | ✅ 创新 | Skill 斜杠命令 + Workflow 脚本双通道，兼顾交互式和批量 |
| Workflow 脚本 | ⚠️ 初版 | 4 个 .workflow.js 文件已编写，使用了结构化输出和 pipeline/phase，但执行覆盖率未知 |
| 状态管理 | ❌ 缺失 | Agent 不持有状态——每次调用独立加载 Context，但缺少"当前进度"的显式管理 |
| Agent 间通信 | ⚠️ 文档传递 | 通过 Context 文档传递状态是正确的设计，但缺少"上游产出就绪"的通知机制 |
| 错误恢复 | ❌ 缺失 | 当 Agent 执行中途失败，无断点续传能力 |

**关键差距**：Agent 从"设计文档"到"可靠执行"的最后一公里尚未打通。Workflow 脚本质量高但需要更多的实战验证和容错机制。

### 1.5 Knowledge 成熟度：⭐ Level 2 — "有意图但缺基础设施"

| 维度 | 评分 | 说明 |
|------|------|------|
| 已知问题库 | ⚠️ 概念阶段 | known-issues.yaml 在设计中被引用（diagnosis-agent 加载它），但实际内容和更新频率未知 |
| 踩坑经验 | ✅ 有机制 | PROJECT_CONTEXT § Element Plus 已知坑位清单 (11个)，knowledge-extractor Skill 定义了沉淀流程 |
| 历史 Bug 库 | ❌ 缺失 | 无结构化历史 Bug 存储，无法实现"这个 Bug 以前见过吗" |
| 测试案例复用 | ❌ 缺失 | TEST_CASES 按页面分散存储，无跨模块/跨项目的测试模式库 |
| 自动化脚本模板 | ⚠️ 隐式 | code-generation Skill 的 Prompt 模板充当了非正式的知识库 |
| 长期记忆 | ❌ 缺失 | AI 会话结束后知识仅存在于文档中，无法被 AI 直接检索 |

**关键差距**：Knowledge 层目前是"嵌入在 Skill Prompt 和 Context 文档中的隐性知识"，缺少独立的、可检索的知识存储层。

### 1.6 Tool 成熟度：⭐ Level 2 — "工具存在但未体系化"

| 维度 | 评分 | 说明 |
|------|------|------|
| 代码质量工具 | ✅ 良好 | check_code_quality.py 全量/单文件/Stage 扫描 + setup_quality_gates.py 防护体系 |
| 自动化执行 | ✅ 良好 | pytest + Selenium + Allure 标准三件套 |
| CI 集成 | ✅ 良好 | Jenkins pipeline + Jenkinsfile |
| 报告生成 | ⚠️ 部分 | Allure 原生报告 + allure-report-analyzer Skill（需手动触发） |
| 测试数据管理 | ❌ 缺失 | 无测试数据工厂/数据生成/数据清理工具 |
| 环境管理 | ❌ 缺失 | 环境切换依赖手动 .env 配置 |
| 日志聚合 | ❌ 缺失 | 无集中式测试日志 |

**关键差距**：Tool 层主要是测试框架本身，缺乏测试数据管理、环境编排、日志聚合等平台级基础设施。

### 1.7 Platform 成熟度：⭐ Level 1 — "概念阶段"

| 维度 | 评分 | 说明 |
|------|------|------|
| 统一入口 | ❌ 缺失 | 无 Web UI 或 CLI 入口，依赖 Claude Code 对话 |
| 任务调度 | ❌ 缺失 | 无定时/触发式任务调度 |
| 多租户/多项目 | ❌ 缺失 | 仅支持单项目 |
| API 层 | ❌ 缺失 | 无可编程接口 |
| 监控告警 | ❌ 缺失 | 失败不自动通知 |

**关键差距**：当前是一个"AI 增强的工作流集合"，还不是一个平台。

### 成熟度总览

```
Context:    ████████░░ Level 3 — 骨架完整，血肉不均
Workflow:   ████████░░ Level 3 — 流程定义完整，自动化执行不足
Skill:      █████████░ Level 4 — 丰富但需归类优化
Agent:      ████████░░ Level 3 — 架构清晰，最后一公里未打通
Knowledge:  █████░░░░░ Level 2 — 有意图，缺基础设施
Tool:       █████░░░░░ Level 2 — 工具存在，未体系化
Platform:   ███░░░░░░░ Level 1 — 概念阶段

综合评级:   Level 2.6 / 5
```

---

## 二、架构审计

### 2.1 问题清单

#### 问题 1: Skill 重复建设 — code-generation 与子 Skill 并存

- **现象**: `code-generation.md` 标记为 deprecated，但文件仍完整保留，其 Prompt 内容与 `page-object-generator`/`test-script-generator`/`conftest-generator` 大量重叠
- **影响**: 新 AI/新人可能误用废弃 Skill，维护负担翻倍
- **建议**: 删除 code-generation.md 主文件，仅保留一行跳转说明；同样处理 element-plus-locator.md

#### 问题 2: tech-analysis 与 page-analysis 定位器职责重叠

- **现象**: `page-analysis` 产出 PAGE_ELEMENT_POSITION.md（含定位器设计），`tech-analysis` 也产出定位器设计表。两个 Skill 都有 A/B/C 三级定位器设计逻辑
- **影响**: 同一页面生成两份定位器文档，可能不一致
- **建议**: 明确 page-analysis 只产出"元素清单"（有什么），tech-analysis 产出"定位方案"（怎么定位）。PAGE_ELEMENT_POSITION 应只由 tech-analysis 产出

#### 问题 3: diagnosis-agent 职责过重

- **现象**: diagnosis-agent 绑定了 6 个 Skill（bug-analysis、ci-pipeline-analysis、test-summary、progress-report、knowledge-precipitation、completeness-check），覆盖 Phase 4.5 ~ Phase 9
- **影响**: 单个 Agent 涵盖"诊断+报告+沉淀+审计"4 种不同性质的任务，Prompt 臃肿
- **建议**: 拆分为 Bug Analysis Agent + Report Agent + Knowledge Agent

#### 问题 4: Context 文档链断裂风险

- **现象**: Context 链（PROJECT_CONTEXT → MODULE_CONTEXT → PAGE_CONTEXT → RISK_MODEL）依赖人工按序加载
- **影响**: 跳过中间层直接操作下层时，AI 缺少必要的上下文约束，产出质量下降
- **建议**: Agent 层硬编码前置检查（已在 analysis-agent 中部分实现），增加自动化的 Context 完整性校验

#### 问题 5: Skill 文件平铺在根目录

- **现象**: 17 个 Skill 文件平铺在 `skills/` 根目录，仅有 automation/ 和 debug/ 两个子目录
- **影响**: 查找困难，分类混乱，新增 Skill 不知道该放哪
- **建议**: 建立完整的目录分类体系

#### 问题 6: 知识沉淀闭环未完全打通

- **现象**: knowledge-precipitation Skill 定义了沉淀流程，knowledge-extractor 定义了提取逻辑，但两者之间的衔接依赖 diagnosis-agent 手工编排
- **影响**: 知识沉淀容易在一次会话结束后被遗忘
- **建议**: 将 knowledge-extractor 作为每个 Agent 结束时的自动触发步骤，而非仅 diagnosis-agent 专属

### 2.2 风险矩阵

| 风险 | 等级 | 触发条件 | 影响 |
|------|------|----------|------|
| Context 碎片化加剧 | 🔴 高 | 新模块不断接入但旧模块文档不补齐 | AI 对不同模块的产出质量差异扩大 |
| Skill 名称冲突 | 🟡 中 | 继续在 skills/ 根目录平铺文件 | 同名 Skill 或功能混淆 |
| Agent 执行中断 | 🟡 中 | Workflow 脚本执行到一半因 API 限流/超时失败 | 模块处于"半分析/半设计"的不一致状态 |
| 知识遗失 | 🔴 高 | 每次 Bug 分析和测试总结后不做沉淀 | 踩过的坑反复踩，经验无法复用 |
| Token 浪费 | 🟡 中 | 每次 Agent 调用都全量加载 PROJECT_CONTEXT (200+行) | 大量 Token 消耗在重复加载不变信息上 |
| 废弃资产误导 | 🟡 中 | AI 读取到 deprecated Skill/旧 context 文件 | 产出基于过时信息 |

### 2.3 Token 浪费分析

当前每次 Agent 调用（以 analysis-agent 为例）需加载：

| 加载项 | 预估 Token | 复用率 |
|--------|-----------|--------|
| PROJECT_CONTEXT.md (200行) | ~3000 | 每次 Agent 都加载 |
| Agent SKILL.md (130行) | ~1500 | 每次调用加载 |
| Skill Prompt 模板 (100行) | ~2000 | 每个 Skill 步骤加载 |
| 输出模板 (80行) | ~1200 | 每个步骤加载 |
| 上游 Context 文档 | ~2000 | 有变化但低频 |
| **单次 Agent 调用总计** | **~9700** | — |

**优化空间**：
- PROJECT_CONTEXT 的 BasePage API 参考（60+ 方法）是高频引用但低频变化的内容 → 适合缓存
- Skill Prompt 模板是纯指令 → 适合缓存
- Agent 编排规则（如"逐级加载不可跳过"）每次重复 → 适合分离为常驻系统指令

---

## 三、Skill 架构优化

### 3.1 当前 Skill 分类问题

**现状**：skill-registry.yaml 使用 6 个 category（governance/qa-design/automation/qa-debug/ci/cross-scenario），但物理目录结构不匹配：

```
skills/                          ← 17 个 Skill 平铺
skills/automation/               ← 6 个 Skill
skills/debug/                    ← 2 个 Skill
```

3 个 deprecated/合并后的 Skill 文件仍在原位，形成"僵尸文件"。

### 3.2 推荐分类体系

```
skills/
├── README.md                     ← 总索引（保留）
├── skill-registry.yaml           ← 注册表（保留）
│
├── project/                      ← 项目级上下文管理
│   ├── project-context-manager.md
│   └── context-sync.md
│
├── requirements/                 ← 需求分析
│   ├── requirement-analysis.md
│   └── module-modeling.md
│
├── test-design/                  ← 测试分析与设计
│   ├── page-analysis.md          ← 纯元素识别（去定位器职责）
│   ├── risk-modeling.md
│   ├── testcase-design.md
│   ├── test-data-generation.md
│   ├── api-testing.md
│   └── miniapp-testing.md
│
├── automation/                   ← 自动化技术 & 代码生成
│   ├── tech-analysis.md          ← 含定位器设计（合并 element-plus-locator 能力）
│   ├── auto-strategy.md
│   ├── page-object-generator.md
│   ├── test-script-generator.md
│   ├── conftest-generator.md
│   └── code-consistency-checker.md
│
├── execution/                    ← 执行 & 报告
│   ├── allure-report-analyzer.md
│   └── excel-exporter.md
│
├── diagnosis/                    ← Bug 诊断 & CI 分析
│   ├── bug-analysis.md
│   ├── ci-pipeline-analysis.md
│   └── jenkinsfile-generator.md
│
├── knowledge/                    ← 知识管理
│   ├── knowledge-precipitation.md
│   ├── knowledge-extractor.md
│   └── completeness-check.md
│
├── reporting/                    ← 进度 & 报告
│   ├── test-summary.md
│   └── progress-report.md
│
└── _deprecated/                  ← 废弃 Skill 归档
    ├── code-generation.md        ← 已拆分，仅保留跳转说明
    └── element-plus-locator.md   ← 已合并到 tech-analysis，仅保留跳转说明
```

### 3.3 Skill 操作清单

| 操作 | Skill | 原因 |
|------|-------|------|
| ✅ **保留** | page-analysis, testcase-design, risk-modeling, tech-analysis, auto-strategy, bug-analysis, project-context-manager, module-modeling, context-sync, api-testing, miniapp-testing, test-data-generation, progress-report, completeness-check | 职责清晰，无替代 |
| ✅ **保留** | page-object-generator, test-script-generator, conftest-generator, code-consistency-checker, allure-report-analyzer, excel-exporter, jenkinsfile-generator, knowledge-extractor | code-generation 拆分后的独立 Skill |
| 🔄 **合并** | knowledge-precipitation + knowledge-extractor → `knowledge-sync` | 两者职责高度互补（一个提取，一个沉淀），合并为完整的知识闭环 Skill |
| 🔄 **拆分** | bug-analysis → `bug-analysis` (单Bug) + `batch-failure-analysis` (批量) | 单个和批量的 Prompt 模板、检查清单差异大，拆分后更聚焦 |
| 🗑️ **废弃** | code-generation（已 deprecated） | 移至 _deprecated/，删除完整内容，仅保留跳转说明 |
| 🗑️ **废弃** | element-plus-locator（已 deprecated） | 移至 _deprecated/，定位能力已完整合并到 tech-analysis |

### 3.4 优化后 Skill 统计

| 类别 | 数量 | 说明 |
|------|------|------|
| project/ | 2 | 项目上下文管理 |
| requirements/ | 2 | 需求分析与模块建模 |
| test-design/ | 6 | 测试分析与设计 |
| automation/ | 6 | 自动化技术与代码生成 |
| execution/ | 2 | 执行与报告 |
| diagnosis/ | 3 | Bug 诊断与 CI 分析 |
| knowledge/ | 3 | 知识管理 |
| reporting/ | 2 | 进度与报告 |
| **_deprecated/** | 2 | 废弃归档 |
| **合计** | **28 active** (从 29 → 28，合并 2→1，拆分 1→2) | — |

---

## 四、Agent 架构优化

### 4.1 当前 Agent 设计问题

1. **diagnosis-agent 过重**：绑定了 6 个性质不同的 Skill（诊断/报告/沉淀/审计）
2. **缺少 Project Agent**：项目初始化和模块索引管理散落在 analysis-agent 的第一步
3. **缺少 Knowledge Agent**：知识沉淀未独立为 Agent，容易被忽略
4. **Agent 间状态传递弱**：仅靠"建议进入下一个 Agent"的口语化提示

### 4.2 推荐：7 Agent 架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Agent 协作全景                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │ ① Project    │───▶│ ② Requirement    │───▶│ ③ Test Design    │   │
│  │    Agent     │    │    Agent         │    │    Agent         │   │
│  │ (Phase 0)    │    │ (Phase 0.5~0.8)  │    │ (Phase 1~1.5)   │   │
│  └──────────────┘    └──────────────────┘    └────────┬─────────┘   │
│        │                                              │              │
│        │ 产出: PROJECT_CONTEXT                         │ 产出:        │
│        │       MODULE_INDEX                          │ PAGE_CONTEXT │
│        ▼                                              │ RISK_MODEL   │
│  ┌──────────────────────────────────────────────────┐ │ TEST_DESIGN  │
│  │            ⑧ Knowledge Agent (横向贯穿)           │ │ TEST_CASES   │
│  │  每个 Agent 结束时触发: 提取→判断→沉淀             │◀┘              │
│  └──────────────────────────────────────────────────┘                │
│                                                                      │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │ ④ Automation │◀───│ ⑤ Execution      │◀───│ ⑥ Bug Analysis   │   │
│  │    Agent     │    │    Agent         │    │    Agent         │   │
│  │ (Phase 3~4)  │    │ (Phase 4.5~7)   │    │ (Phase 4.5~5)   │   │
│  └──────┬───────┘    └────────┬─────────┘    └────────┬─────────┘   │
│         │                     │                       │              │
│         │ 产出:               │ 产出:                 │ 产出:        │
│         │ TECH_ANALYSIS      │ 执行结果               │ BUG_ANALYSIS │
│         │ AUTO_STRATEGY      │ Allure 报告            │ 分类报告     │
│         │ PageObject         │                        │ 根因分析     │
│         │ test_*.py          │                        │              │
│         │ conftest.py        │                        │              │
│         └─────────────────────┼────────────────────────┘              │
│                               │                                       │
│                               ▼                                       │
│                      ┌──────────────────┐                            │
│                      │ ⑦ Report         │                            │
│                      │    Agent         │                            │
│                      │ (Phase 8~9)      │                            │
│                      └──────────────────┘                            │
│                        产出: TEST_SUMMARY, 进度报告                    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.3 各 Agent 详细定义

#### ① Project Agent（新增）

| 维度 | 内容 |
|------|------|
| **职责** | 项目级上下文初始化与维护、模块索引管理、环境配置验证 |
| **绑定 Skill** | `project-context-manager`、`context-sync`、`completeness-check` |
| **输入** | 项目代码仓库、环境信息、旧资产目录 |
| **输出** | PROJECT_CONTEXT.md、MODULE_INDEX.md、project-index.yaml |
| **触发** | 新项目接入、"更新项目上下文"、"检查模块文档完整度" |
| **边界** | 不分析具体模块/页面（交给 Requirement Agent） |

#### ② Requirement Agent（新增，从 analysis-agent 拆分）

| 维度 | 内容 |
|------|------|
| **职责** | 模块边界建模、需求分析、页面发现与注册 |
| **绑定 Skill** | `module-modeling`、`requirement-analysis` |
| **输入** | PROJECT_CONTEXT.md、PRD/原型/需求文档 |
| **输出** | MODULE_CONTEXT.md、REQUIREMENT_ANALYSIS.md |
| **触发** | "分析XX模块"、"这个需求怎么测" |
| **边界** | 不分析页面元素（交给 Test Design Agent） |

#### ③ Test Design Agent（原 design-agent，职责收窄）

| 维度 | 内容 |
|------|------|
| **职责** | 页面分析、风险建模、测试设计、测试用例 |
| **绑定 Skill** | `page-analysis`、`risk-modeling`、`testcase-design`、`test-data-generation`、`api-testing`、`miniapp-testing` |
| **输入** | MODULE_CONTEXT.md、页面截图/HTML、需求文档 |
| **输出** | PAGE_CONTEXT.md、RISK_MODEL.md、TEST_DESIGN.md、TEST_CASES.md |
| **触发** | "看看XX页面有什么元素"、"给XX设计测试用例"、"XX页面有什么风险" |
| **边界** | 不产出技术实现分析（交给 Automation Agent） |

#### ④ Automation Agent（原 code-agent + 技术分析，职责扩展）

| 维度 | 内容 |
|------|------|
| **职责** | 技术分析、自动化策略、代码生成、代码合规检查 |
| **绑定 Skill** | `tech-analysis`、`auto-strategy`、`page-object-generator`、`test-script-generator`、`conftest-generator`、`code-consistency-checker` |
| **输入** | PAGE_CONTEXT.md、TEST_CASES.md、BasePage 代码 |
| **输出** | TECH_ANALYSIS.md、AUTO_STRATEGY.md、PageObject、test_*.py、conftest.py |
| **触发** | "这个按钮怎么定位"、"生成XX的PageObject"、"写XX功能的测试脚本" |
| **边界** | 不设计测试用例（交给 Test Design Agent） |

#### ⑤ Execution Agent（新增）

| 维度 | 内容 |
|------|------|
| **职责** | 执行自动化测试、监控执行状态、收集结果、生成 Allure 报告 |
| **绑定 Skill** | `allure-report-analyzer`、`excel-exporter` |
| **输入** | 测试模块名、执行参数（marker/并行度/环境） |
| **输出** | 执行摘要、Allure 报告、Excel 报告 |
| **触发** | "运行XX模块的测试"、"执行冒烟测试"、"导出测试报告到 Excel" |
| **边界** | 不分析失败原因（交给 Bug Analysis Agent） |

#### ⑥ Bug Analysis Agent（从 diagnosis-agent 拆分，职责聚焦）

| 维度 | 内容 |
|------|------|
| **职责** | 单个/批量 Bug 分析、CI 流水线诊断、Jenkins 配置更新 |
| **绑定 Skill** | `bug-analysis`、`ci-pipeline-analysis`、`jenkinsfile-generator` |
| **输入** | 失败日志、截图、代码上下文、CI 日志 |
| **输出** | BUG_ANALYSIS.md、CI 分析报告、Jenkinsfile 更新 |
| **触发** | "这个用例为什么挂了"、"一堆失败帮我分类"、"Jenkins 构建失败了" |
| **边界** | 不生成测试报告（交给 Report Agent）、不沉淀知识（交给 Knowledge Agent） |

#### ⑦ Report Agent（从 diagnosis-agent 拆分，新增）

| 维度 | 内容 |
|------|------|
| **职责** | 测试总结报告、进度报告、周报/月报 |
| **绑定 Skill** | `test-summary`、`progress-report`、`excel-exporter` |
| **输入** | 执行报告、Bug 统计、进度追踪 |
| **输出** | TEST_SUMMARY.md、进度报告、周报 |
| **触发** | "生成测试总结报告"、"本周测试进度汇报" |
| **边界** | 不分析 Bug（交给 Bug Analysis Agent） |

#### ⑧ Knowledge Agent（从 diagnosis-agent 拆分，新增）

| 维度 | 内容 |
|------|------|
| **职责** | 知识提取、已知问题库维护、PROJECT_CONTEXT 更新、文档完整性审计 |
| **绑定 Skill** | `knowledge-sync`（合并 knowledge-precipitation + knowledge-extractor）、`completeness-check` |
| **输入** | Bug 分析结论、踩坑记录、新增模块上下文 |
| **输出** | known-issues.yaml 更新、PROJECT_CONTEXT 更新、知识库索引更新 |
| **触发** | "沉淀本轮经验"、"这个 Bug 别人也会遇到吗"、"更新已知问题库" |
| **边界** | 不产出测试设计/代码/报告 |

### 4.4 Agent 协作协议

```
Agent 间数据流：

① Project Agent
    │  PROJECT_CONTEXT.md, MODULE_INDEX.md
    ▼
② Requirement Agent
    │  MODULE_CONTEXT.md, REQUIREMENT_ANALYSIS.md
    ▼
③ Test Design Agent
    │  PAGE_CONTEXT.md, RISK_MODEL.md, TEST_DESIGN.md, TEST_CASES.md
    ▼
④ Automation Agent ─────────────────────────────┐
    │  TECH_ANALYSIS.md, AUTO_STRATEGY.md        │
    │  PageObject, test_*.py, conftest.py         │
    ▼                                             │
⑤ Execution Agent                                │
    │  执行结果, Allure 报告                       │
    ├─────────────────────────────────────────────┘
    │
    ├──成功──▶ ⑦ Report Agent ──▶ ⑧ Knowledge Agent
    │
    └──失败──▶ ⑥ Bug Analysis Agent ──▶ ④ Automation Agent (修复)
                    │
                    └──▶ ⑧ Knowledge Agent (沉淀)
```

### 4.5 状态流转规范

每个 Agent 产出的文档须包含状态标记：

```yaml
# 在每个产出文档的 Footer 添加
---
phase: Phase 1.5
status: complete          # draft | complete | needs_review | deprecated
completed_by: analysis-agent
completed_at: 2026-06-11
next_phase: Phase 2
next_agent: design-agent
prerequisites_met: true   # 上游文档是否齐备
---
```

### 4.6 边界划分铁律

| 规则 | 说明 |
|------|------|
| **一个 Agent 不跨 Phase 大类** | 分析(0~1.5) / 设计(2~2.5) / 自动化(3~4) / 执行(4.5~7) / 报告(8~9) 严格分离 |
| **Agent 间不共享会话** | 每次调用独立加载 Context 文档 |
| **上游产出未完成，下游拒绝执行** | 硬编码门禁检查 |
| **Knowledge Agent 是唯一可跨 Agent 写入的** | 其他 Agent 只能读取知识库，不能写入（防止碎片化） |

---

## 五、知识库设计

### 5.1 需求评估矩阵

| 能力 | 价值 | 成本 | ROI | 推荐 |
|------|------|------|-----|------|
| **已知问题库 (known-issues.yaml)** | 🔴 高：高频 Bug 快速匹配 | 低：YAML 文件即可 | ⭐⭐⭐⭐⭐ | ✅ 立刻建设 |
| **踩坑经验库 (pitfalls/)** | 🔴 高：Element Plus 坑位已证明价值 | 低：MD 文件即可 | ⭐⭐⭐⭐⭐ | ✅ 立刻建设 |
| **测试模式库 (test-patterns/)** | 🟡 中：跨模块复用测试设计 | 中：需要抽象通用模式 | ⭐⭐⭐⭐ | ✅ 中期建设 |
| **历史 Bug 向量库** | 🟡 中：相似 Bug 检索 | 🔴 高：需向量化+检索 | ⭐⭐⭐ | ⚠️ 远期评估 |
| **RAG 知识检索** | 🟡 中：提升 AI 上下文效率 | 🔴 高：需 Embedding + VectorDB | ⭐⭐ | ⚠️ 远期评估 |
| **长期记忆 (AI Memory)** | 🟢 低：跨会话记忆 | 🟡 中：Claude Code Memory 已内置 | ⭐⭐ | ❌ 不需要额外建设 |
| **自动化脚本模板库** | 🟢 低：Skill Prompt 已充当模板 | 低：已有 | ⭐ | ❌ 不需要（已覆盖） |
| **向量数据库** | 🟢 低：当前规模不需要 | 🔴 高：基础设施+运维 | ⭐ | ❌ 过度设计 |

### 5.2 推荐建设方案

#### 阶段 1：结构化文件知识库（立即建设，1 周）

```
governance/knowledge/
├── README.md                        ← 知识库索引与使用指南
├── known-issues.yaml                ← 已知问题库（结构化的高频 Bug）
├── pitfalls/                        ← 踩坑经验
│   ├── element-plus/                ← Element Plus 组件踩坑
│   │   ├── el-select-teleport.md
│   │   ├── el-date-picker-range.md
│   │   └── el-cascader-dynamic.md
│   ├── selenium/                    ← Selenium 通用踩坑
│   │   ├── stale-element.md
│   │   └── iframe-cross-origin.md
│   └── project-specific/            ← 本系统特有的坑
│       ├── permission-cache.md
│       └── token-expiry-popup.md
├── test-patterns/                   ← 测试模式库（中期）
│   ├── crud-standard.md             ← 标准 CRUD 测试模式
│   ├── search-filter.md             ← 搜索筛选测试模式
│   ├── batch-operation.md           ← 批量操作测试模式
│   └── permission-matrix.md         ← 权限矩阵测试模式
└── changelog/                       ← Context 变更记录
    └── CHANGELOG.yaml               ← 谁在何时改了哪个文档
```

#### 阶段 2：known-issues.yaml 格式设计

```yaml
# 已知问题库 — AI 和人类都可维护
issues:
  - id: KI-001
    title: "el-select 下拉选项渲染在 body 层导致普通定位器失效"
    category: element-plus
    component: el-select
    severity: high
    reproduce_rate: 90%
    symptoms:
      - "ElementClickInterceptedException"
      - "element not interactable"
    root_cause: "Element Plus 将下拉选项 teleport 到 body 末尾"
    solution: "使用 BasePage.select_el_option() 或定位 body 层下拉选项"
    affected_modules: ["equipment", "system-user", "personnel"]
    first_seen: 2026-05-15
    last_seen: 2026-06-10
    occurrence_count: 12
    automated_detection: false  # 是否已加入 CI 自动检测

  - id: KI-002
    title: "Vue v-if 导致元素不在 DOM 中，等待策略失效"
    # ...
```

#### 阶段 3：不推荐建设的能力及原因

| 能力 | 不推荐原因 |
|------|-----------|
| **Milvus/Weaviate 向量数据库** | 当前 < 10 个模块、< 100 个文档，全文检索完全够用，向量 DB 运维成本远大于收益 |
| **RAG Pipeline (LangChain/LlamaIndex)** | 当前 AI (Claude) 已有 200K 上下文窗口，全量加载所有 Context 文档绰绰有余。在单仓库规模超过 10 万行才需要 RAG |
| **长期记忆系统 (Mem0/Letta)** | Claude Code 内置的 Memory 功能已覆盖跨会话记忆需求。额外的记忆系统增加复杂度而不增加价值 |
| **图数据库 (Neo4j)** | 知识图谱对测试场景的 ROI 极低——测试知识的核心关联是线性的（模块→页面→元素），不需要图遍历 |

---

## 六、自动化测试平台设计

### 6.1 目标架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                      AI 自动化测试平台 (v2.0)                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────── 接入层 ──────────────────────────────┐  │
│  │                                                                  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │  │
│  │  │ Claude   │  │ Web UI   │  │ CLI      │  │ CI/CD        │   │  │
│  │  │ Code     │  │ (远期)    │  │ (中期)    │  │ (Jenkins)    │   │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │  │
│  │       └──────────────┴────────────┴───────────────┘             │  │
│  └──────────────────────────┬───────────────────────────────────────┘  │
│                             │                                         │
│  ┌────────────────────────── 编排层 ───────────────────────────────┐  │
│  │                                                                  │  │
│  │  ┌──────────────────────────────────────────────────────────┐  │  │
│  │  │                    Agent 路由 & 编排                       │  │  │
│  │  │  Project → Requirement → TestDesign → Automation         │  │  │
│  │  │       → Execution → BugAnalysis → Report → Knowledge     │  │  │
│  │  └──────────────────────────────────────────────────────────┘  │  │
│  │                                                                  │  │
│  │  ┌──────────────────────────────────────────────────────────┐  │  │
│  │  │                    Workflow 引擎                          │  │  │
│  │  │  DAG 定义 → Phase 调度 → 门禁检查 → 异常恢复 → 回调通知    │  │  │
│  │  └──────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                             │                                         │
│  ┌────────────────────────── 能力层 ───────────────────────────────┐  │
│  │                                                                  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │ Skill 库  │ │ Agent 层  │ │ 知识库   │ │ Context 引擎     │  │  │
│  │  │ 28 Skills │ │ 7 Agents │ │ known-   │ │ 上下文链加载      │  │  │
│  │  │ 7 个分类  │ │ + 编排   │ │ issues   │ │ 完整性校验        │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                             │                                         │
│  ┌────────────────────────── 执行层 ───────────────────────────────┐  │
│  │                                                                  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │ pytest   │ │ Selenium │ │ Allure   │ │ 代码质量扫描      │  │  │
│  │  │ 7.4.4    │ │ 4.15.2   │ │ 2.13.2   │ │ check_code_quality│  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │  │
│  │                                                                  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────────────────┐   │  │
│  │  │ 数据工厂  │ │ 环境管理 │ │ 日志聚合 (中期)               │   │  │
│  │  │ (中期)   │ │ (中期)    │ │                              │   │  │
│  │  └──────────┘ └──────────┘ └──────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                             │                                         │
│  ┌────────────────────────── 数据层 ───────────────────────────────┐  │
│  │                                                                  │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │  │
│  │  │ Context 文档      │  │ Artifacts 产物    │  │ 知识库       │  │  │
│  │  │ PROJECT_CONTEXT   │  │ BUG_ANALYSIS     │  │ known-issues │  │  │
│  │  │ MODULE_CONTEXT    │  │ TEST_SUMMARY     │  │ pitfalls     │  │  │
│  │  │ PAGE_CONTEXT      │  │ Allure 报告      │  │ test-patterns│  │  │
│  │  │ (git 版本控制)     │  │ (按日期归档)      │  │ (git 版本控制)│  │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2 核心数据流

```
用户输入 "分析设备管理模块的报警配置页面"
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ ① 接入层：路由到 Claude Code → 匹配 /analysis-agent      │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ ② 编排层：Agent 加载 Context 链                          │
│    PROJECT_CONTEXT → MODULE_CONTEXT → (如有) PAGE_CONTEXT│
│    完整性校验 → 决定从哪个 Phase 开始                     │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ ③ 能力层：Agent 调用 Skill 逐 Phase 执行                 │
│    Phase 1: page-analysis → PAGE_CONTEXT.md              │
│    Phase 1.5: risk-modeling → RISK_MODEL.md              │
│    门禁：PAGE_CONTEXT 完整度 ≥ 60% → 通过                │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ ④ 能力层：产出写入 Context 文档                          │
│    governance/context/projects/web-automation/modules/   │
│      equipment/pages/alarm-config/                       │
│        ├── PAGE_CONTEXT.md                               │
│        ├── PAGE_ELEMENT_POSITION.md                      │
│        └── RISK_MODEL.md                                 │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ ⑤ 知识层：Knowledge Agent 自动触发                       │
│    判断是否有新的高频模式 → 写入 known-issues.yaml        │
│    更新 MODULE_INDEX 状态标记                            │
│    建议下一个 Agent：/design-agent                        │
└─────────────────────────────────────────────────────────┘
```

### 6.3 调用链

```
/analysis-agent
  ├─ Read PROJECT_CONTEXT.md (~3000 tokens)
  ├─ Read MODULE_INDEX.md (~500 tokens)
  ├─ Read governance/skills/test-design/page-analysis.md (~2000 tokens)
  ├─ Read governance/templates/page-context.template.md (~1000 tokens)
  ├─ [分析执行] (~5000 tokens 思考+输出)
  ├─ Write PAGE_CONTEXT.md
  ├─ Read governance/skills/test-design/risk-modeling.md (~1500 tokens)
  ├─ [风险评估] (~3000 tokens)
  ├─ Write RISK_MODEL.md
  ├─ Trigger Knowledge Agent
  │   └─ Update MODULE_INDEX.md
  └─ Return: "✅ 分析完成，建议 /design-agent"
```

### 6.4 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Context 存储 | Git 版本控制 + Markdown 文件 | 简单、可审计、AI 可直接读写 |
| 知识库存储 | YAML + Markdown 文件 | 结构化程度刚好，不需要数据库 |
| Agent 间通信 | 文档传递（非 API/消息队列） | 与 Claude Code 工作模式一致，零额外基础设施 |
| 执行引擎 | 复用 Claude Code Workflow 工具 | 已有 pipeline/parallel/phase 原语，无需自建调度器 |
| 平台入口 | Claude Code CLI（短期）/ 自定义 CLI（中期） | 避免过早建设 Web UI |

---

## 七、扩展能力分析

### 7.1 技术适用性评估

| 技术 | 适用时机 | 接入收益 | 复杂度 | 优先级 | 判定 |
|------|---------|---------|--------|--------|------|
| **MCP (Model Context Protocol)** | 现在 | 🔴 高：标准化工具接入，可封装 pytest/Allure/Jenkins 为 MCP Server | 中 | ⭐⭐⭐⭐⭐ | ✅ **P0 优先级** |
| **A2A (Agent-to-Agent)** | 3个月后 | 🔴 高：Agent 间标准化通信协议，替代当前的"文档约定" | 中 | ⭐⭐⭐⭐ | ✅ **P1 优先级** |
| **OpenAI Agent SDK** | 不需要 | 🟢 低：当前使用 Claude Code 的 Agent/Workflow 工具，无需跨模型 | — | ⭐ | ❌ 不适用 |
| **LangGraph** | 6个月后 | 🟡 中：可视化 DAG 编排，但当前 Workflow 脚本已覆盖 | 高 | ⭐⭐⭐ | ⚠️ 远期评估 |
| **LangChain** | 不需要 | 🟢 低：当前无需 Chain 抽象——Workflow 脚本+Skill Prompt 更直接 | 高 | ⭐ | ❌ 过度抽象 |
| **Dify** | 6个月后 | 🟡 中：低代码 AI 应用搭建，适合非技术人员使用 | 低 | ⭐⭐⭐ | ⚠️ 远期评估 |
| **多 Agent 协作框架** | 3个月后 | 🔴 高：7 Agent 架构需要标准化协作协议 | 高 | ⭐⭐⭐⭐ | ✅ **P1 优先级** |

### 7.2 重点推荐

#### MCP (Model Context Protocol) — P0 优先级

```
推荐建设 4 个 MCP Server：

1. pytest-mcp-server
   - 暴露: run_test(module, markers, parallel), get_test_status(), get_test_list()
   - 收益: CI 集成自动化，Agent 可直接触发执行

2. allure-mcp-server
   - 暴露: get_report_summary(), get_failed_tests(), get_trend()
   - 收益: 报告分析自动化，不再需要手动执行 allure 命令

3. jenkins-mcp-server
   - 暴露: trigger_build(), get_build_status(), get_build_log()
   - 收益: CI 诊断直接在对话中完成

4. context-mcp-server
   - 暴露: get_module_context(module), get_page_context(module, page), check_completeness()
   - 收益: Context 加载标准化，减少 Token 浪费
```

#### A2A (Agent-to-Agent Protocol) — P1 优先级

```
当前 Agent 间通信方式:
  分析 Agent → 产出文档 → 口头告知"建议进入设计 Agent" → 用户手动调用

A2A 改造后:
  分析 Agent → 产出文档 + 发送 A2A 消息 → 设计 Agent 收到通知 → 
  询问用户"是否继续测试设计？" → 用户确认 → 设计 Agent 开始工作

A2A 消息格式:
  {
    "from": "analysis-agent",
    "to": "design-agent",
    "type": "handoff",
    "payload": {
      "module": "equipment",
      "page": "alarm-config",
      "completed_phase": "Phase 1.5",
      "outputs": ["PAGE_CONTEXT.md", "RISK_MODEL.md"],
      "context_path": "governance/context/projects/web-automation/modules/equipment/pages/alarm-config/"
    }
  }
```

### 7.3 不推荐的技术

| 技术 | 不推荐原因 |
|------|-----------|
| **LangChain** | 为"Chain"而"Chain"的抽象层，当前 Skill 编排用 Workflow 脚本已足够。LangChain 的 Agent/Supervisor 模式在 Claude Code 的 Workflow 工具面前是重复建设 |
| **OpenAI Agent SDK** | 项目基于 Claude/Anthropic 生态，引入 OpenAI SDK 产生不必要的依赖耦合 |
| **向量数据库 (Chroma/Pinecone)** | 当前文档量级（< 100 个 MD 文件）下，全文检索 + AI 上下文窗口完全够用 |

---

## 八、路线图规划

### 8.1 1 个月路线图（2026-06 ～ 2026-07）

**主题：底座加固 — 提升复用率和一致性**

| 周 | 任务 | 产出 | 优先级 |
|------|------|------|--------|
| W1 | **Skill 目录重组**：按 7 分类体系迁移文件，deprecated Skill 归档至 _deprecated/ | 新 skills/ 目录结构 | 🔴 P0 |
| W1 | **Agent 拆分**：从 diagnosis-agent 拆分出 Report Agent + Knowledge Agent | 3 个新 Agent SKILL.md + .workflow.js | 🔴 P0 |
| W2 | **Project Agent 上线**：将 project-context-manager 独立为 Agent，含自动化 Context 完整性校验 | Project Agent 就绪 | 🔴 P0 |
| W2 | **known-issues.yaml 初始化**：将 PROJECT_CONTEXT 中的 11 个 Element Plus 坑位迁移到结构化 YAML | known-issues.yaml 就绪 | 🔴 P0 |
| W3 | **Skill 去重清理**：删除 code-generation.md 完整内容，仅保留跳转；合并 page-analysis 和 tech-analysis 的定位器边界 | 2 个废弃 Skill 归档 | 🟡 P1 |
| W3 | **Context 文档状态标记规范落地**：所有产出文档 Footer 添加 phase/status/next_agent | Context 文档规范化 | 🟡 P1 |
| W4 | **pitfalls/ 踩坑经验库建设**：从现有 Bug 分析记录中提取 5-10 条结构化踩坑经验 | pitfalls/ 目录就绪 | 🟡 P1 |

**1 个月后预期状态**：
- Skill 目录结构清晰，7 个分类目录各司其职
- Agent 从 4 个扩展为 7 个，职责边界清晰
- known-issues.yaml 成为 Bug 分析的权威参考
- Context 文档全部包含状态标记，Agent 间流转可追踪

### 8.2 3 个月路线图（2026-07 ～ 2026-09）

**主题：能力提升 — 自动化程度和 Agent 协作**

| 月 | 任务 | 产出 | 优先级 |
|------|------|------|--------|
| M2 | **MCP Server 建设 (Phase 1)**：pytest-mcp-server + allure-mcp-server 最小可用版本 | 2 个 MCP Server | 🔴 P0 |
| M2 | **Agent Workflow 脚本增强**：添加断点续传（resume）和异常恢复逻辑 | 7 个 .workflow.js 升级 | 🔴 P0 |
| M2 | **test-patterns/ 测试模式库初始化**：提取 CRUD/搜索/批量操作/权限矩阵 4 个通用测试模式 | 4 个 test-pattern 文档 | 🟡 P1 |
| M3 | **Execution Agent 上线**：自动化执行 → 结果收集 → 失败自动路由到 Bug Analysis Agent | Execution Agent 就绪 | 🔴 P0 |
| M3 | **A2A 通信试点**：在 Analysis → Design → Automation 三个 Agent 间实现标准化 Handoff | A2A 协议 v0.1 | 🟡 P1 |
| M3 | **环境管理工具**：基于 .env 的环境切换 CLI 工具 + 环境健康检查 | 环境管理工具 | 🟡 P1 |
| M4 | **测试数据工厂**：基于 YAML 的测试数据生成器，支持依赖数据和唯一性约束 | 数据工厂 v0.1 | 🟡 P1 |
| M4 | **CI 集成增强**：Jenkins Pipeline 全自动化——代码提交 → Context 校验 → 自动化生成 → 执行 → 报告 | 全自动 CI Pipeline | 🟡 P1 |

**3 个月后预期状态**：
- Agent 可直接触发测试执行并获得结果
- Bug 从"发现"到"分析"到"沉淀"全自动闭环
- 新增模块的 4 个基础 test-pattern 可复用，减少 50% 测试设计时间
- Agent 间通过 A2A 协议实现自动流转，减少人工干预

### 8.3 6 个月路线图（2026-09 ～ 2026-12）

**主题：平台化 — 从工具集到平台**

| 月 | 任务 | 产出 | 优先级 |
|------|------|------|--------|
| M5 | **MCP Server 建设 (Phase 2)**：jenkins-mcp-server + context-mcp-server。4 个 MCP Server 全部可用 | MCP Server 套件 | 🔴 P0 |
| M5 | **CLI 入口**：`aitest analyze|design|generate|run|report <module>` 统一命令行入口 | aitest CLI | 🟡 P1 |
| M6 | **Web Dashboard (MVP)**：模块状态看板、测试通过率趋势、知识库检索 | Web Dashboard v0.1 | 🟡 P1 |
| M6 | **多项目支持**：Context 引擎支持 project switching，小程序项目全流程纳入 | 多项目 Context 管理 | 🟡 P1 |
| M7 | **知识库检索增强**：基于全文检索的知识库查询，AI 可主动查询"这个 Bug 以前见过吗" | 知识库检索 | 🟡 P1 |
| M8 | **持续学习闭环**：基于历史 Bug 数据自动优化 Skill Prompt（如"已知 el-select 定位易失败，tech-analysis 应自动生成 3 级备用方案"） | Prompt 自动优化 | 🟢 P2 |

**6 个月后预期状态**：
- 统一的 CLI 入口，告别"找对应 Skill 名称"的心智负担
- Web Dashboard 可视化整体测试健康度
- 知识库可被 AI 主动检索，而非被动依赖人力更新
- 小程序和 Web 项目共享同一套 Agent/Workflow/Skill 体系

### 8.4 不做的事项（避免过度设计）

| 不做 | 原因 |
|------|------|
| ❌ 自研测试框架 | pytest + Selenium + Allure 已经足够好 |
| ❌ 微服务架构 | 单体 Agent 通过文件协作已满足需求 |
| ❌ 实时协作（多人同时编辑同一 Context） | 模块独立原则已解决冲突问题 |
| ❌ 自定义 DSL 描述测试用例 | Markdown 表格已足够，DSL 增加学习成本 |
| ❌ 向量数据库 + RAG | 当前文档量级不需要，成本远大于收益 |
| ❌ AI 自动修 Bug | 诊断 Agent 给出修复建议但由人决策，完全自动修复风险不可控 |

---

## 总结

### 当前状态

```
综合成熟度: Level 2.6 / 5
最大优势: Skill 库质量高（29个，含 Prompt 模板+检查清单），Agent 架构清晰（4 Agent 双通道）
最大短板: Knowledge 层缺失（知识散落在 Prompt 和文档中），Platform 层为 0
```

### 核心优化方向

```
1. Skill 归档重整       → 消除冗余，建立 7 分类体系
2. Agent 拆分 (4→7)     → 聚焦职责，解决 diagnosis-agent 过重
3. Knowledge 基础设施    → known-issues.yaml + pitfalls/ 建立知识底座
4. MCP Server 建设      → pytest/allure/jenkins/context 标准化工具接入
5. A2A Agent 协作       → 从"人工传递"到"自动流转"
```

### 风险与应对

| 风险 | 应对 |
|------|------|
| 重构影响当前工作流 | 所有变更是**增量式**的——旧文件移至 _deprecated/ 而非删除，Agent 拆分后原 diagnosis-agent 保留兼容期 |
| 过度设计 | 路线图明确标注了"不做的事项"，每个阶段有明确的 P0/P1/P2 优先级 |
| 知识库维护负担 | known-issues.yaml 和 pitfalls/ 由 Knowledge Agent 自动维护，人工仅需审核 |

---

> 📋 本文档是架构分析产物，存放于 `governance/artifacts/plans/`。
> 实施前建议按路线图的 1 个月 / 3 个月 / 6 个月分阶段评审和调整。
