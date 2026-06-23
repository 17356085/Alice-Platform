# AI自动化测试平台架构优化方案

> 版本：v1.0 | 日期：2026-06-11 | 作者：AI 系统架构师（基于项目全量审计）

---

## 目录

1. [现状分析](#一现状分析)
2. [第一部分：成熟度评估](#二第一部分成熟度评估)
3. [第二部分：架构审计](#三第二部分架构审计)
4. [第三部分：Skill 架构优化](#四第三部分skill-架构优化)
5. [第四部分：Agent 架构优化](#五第四部分agent-架构优化)
6. [第五部分：知识库设计](#六第五部分知识库设计)
7. [第六部分：自动化测试平台设计](#七第六部分自动化测试平台设计)
8. [第七部分：扩展能力分析](#八第七部分扩展能力分析)
9. [第八部分：路线图规划](#九第八部分路线图规划)
10. [风险评估](#十风险评估)

---

## 一、现状分析

### 1.1 项目概况

| 维度 | 现状 |
|------|------|
| 被测系统 | 鞍集涂源管理系统 — Web 管理端（Vue 3 + Element Plus）+ 微信小程序端 |
| 测试框架 | Python 3.x + pytest 7.4.4 + Selenium 4.15.2 + Allure 2.13.2 |
| CI/CD | Jenkins Pipeline（5 Stage：Sync→Lint→Safe并行→Destructive串行→Report） |
| 工程阶段 | Prompt工程✅ → Workflow工程✅ → Skill工程✅ (28个, 7分类) → Agent工程✅ (8 Agent v2.0) |
| 治理骨架 | governance/ 目录完整（context/skills/workflows/templates/agents/artifacts） |
| 纳管模块 | 10 个（7 active + 1 active-soon + 2 scaffold-only） |
| 小程序测试 | Node.js + 自研 mp-weixin-automator，20 页面已建模 |

### 1.2 核心资产盘点

| 资产层 | 数量 | 状态 |
|--------|------|------|
| Context 文档 | PROJECT_CONTEXT (200行) + MODULE_INDEX + 多模块 MODULE_CONTEXT/PAGE_CONTEXT/... | 🟢 体系完整 |
| Workflow | 9 个核心流程定义 | 🟢 覆盖主链路 |
| Skill | 28 个（26 active + 2 deprecated），7 分类 | 🟢 分类清晰 |
| Agent | 8 个 v2.0 + 4 个 v1.0 deprecated | 🟡 v1.0 残留 |
| Template | 10 个输出格式模板 | 🟢 覆盖完整 |
| Knowledge Base | known-issues.yaml（16条结构化） | 🟡 体量小 |
| Memory | Claude 原生 Memory（基本未使用） | 🔴 未激活 |
| Tool | check_code_quality.py + setup_quality_gates.py | 🟡 仅代码层 |
| Platform | Claude Code Native + VSCode Extension | 🟡 无独立平台 |

---

## 二、第一部分：成熟度评估

### 2.1 综合评分

| 维度 | 级别 | 评分 | 关键词 |
|------|------|------|--------|
| **Context 成熟度** | **L4** | 85/100 | 体系完整、结构化好、部分模块深度不足 |
| **Workflow 成熟度** | **L3** | 70/100 | 流程覆盖全、但耦合度高、动态编排缺失 |
| **Skill 成熟度** | **L4** | 82/100 | 分类科学、职责清晰、少数 Skill 体量过大 |
| **Agent 成熟度** | **L3** | 68/100 | 边界清晰、协作模式确立、缺少运行时协作 |
| **Knowledge 成熟度** | **L2** | 45/100 | 仅静态 YAML、无向量化、无历史检索 |
| **Tool 成熟度** | **L2** | 40/100 | 仅代码层工具、缺少平台化 Tool 体系 |
| **Platform 成熟度** | **L1** | 25/100 | 纯 CLI 驱动、无独立平台入口 |
| **综合** | **L3** | **59/100** | 工程化初具规模，平台化尚未起步 |

### 2.2 各维度详细评估

#### Context 成熟度：L4（体系化）

**优势：**
- `source-of-truth.md` 明确了单一事实源原则，避免数据重复
- PROJECT_CONTEXT 达到 200+ 行，BasePage 60+ API 全覆盖，Element Plus 11 坑位结构化
- 模块/页面级上下文层级清晰：PROJECT → MODULE → PAGE → TECH_ANALYSIS → AUTO_STRATEGY
- 模板体系完整（10 个），产出格式统一

**不足：**
- 部分模块 MODULE_CONTEXT 仍为空壳（production/dcs scaffold-only）
- Cross-module 依赖关系未显式建模（如 equipment 页面引用了 system-user 的组件）
- CURRENT_TASK 机制未标准化，会话恢复依赖人工描述
- 上下文版本管理缺失：PROJECT_CONTEXT 更新后，下游文档是否过期无检测

**提升到 L5 需要：**
- 模块间依赖关系图
- Context 版本号 + 自动过期检测
- CURRENT_TASK 标准化模板 + 自动恢复

---

#### Workflow 成熟度：L3（流程化）

**优势：**
- 9 个核心 Workflow 覆盖完整测试生命周期
- module-onboarding 和 automation-implementation 是最高价值流程
- test-cycle-closure 实现了执行→报告→知识沉淀的闭环
- 输入输出定义清晰

**不足：**
- **耦合度过高**：module-onboarding 作为"巨无霸"Workflow 承载 Phase 0.5→2.5，内部 Skill 编排僵化
- **无动态路由**：失败后走 Bug Analysis 还是直接修复？当前是人工判断，缺少自动决策
- **无并行编排**：多个模块的 Page Analysis 无法并行执行
- **Workflow 定义与执行脱节**：定义在 .md 文件中，实际执行靠 Agent 手动编排，不可复现
- **缺少回滚机制**：Workflow 中途失败无状态保存，无法断点续跑

**提升到 L5 需要：**
- Workflow 引擎（哪怕是 YAML/JSON 定义的 DAG）
- 动态路由（条件分支）
- 断点续跑 + 状态持久化
- 并行执行能力

---

#### Skill 成熟度：L4（精细化）

**优势：**
- 7 分类体系科学：project / requirements / test-design / automation / execution / diagnosis / knowledge / reporting
- 口语化路由表（21条）降低使用门槛
- code-generation 已拆分为 3 个独立 Skill，element-plus-locator 已合并到 tech-analysis——拆分/合并决策合理
- code-consistency-checker 提供自动化质量门禁
- 每个 Skill 有明确的输入/输出/规则/边界定义

**不足：**
- **Skill 体量不均**：tech-analysis 承载了定位器设计 + 等待策略 + Element Plus 深度定位，体量过大
- **test-data-generation 使用率低**：独立 Skill 但缺乏与 test-script-generator 的自动联动
- **Skill 之间信息传递靠文档**：page-analysis 产出 PAGE_CONTEXT → tech-analysis 重新解析，无结构化接口
- **Skill 版本管理缺失**：Skill Prompt 修改后无法追溯变更历史

**提升到 L5 需要：**
- Skill 间结构化数据接口（非纯 Markdown 传递）
- Skill 版本号 + 变更日志
- 大 Skill 继续拆分（tech-analysis 考虑拆为 locator-design + wait-strategy）

---

#### Agent 成熟度：L3（职责化）

**优势：**
- 8 Agent v2.0 职责边界清晰，每个 Agent 有明确的"不做什么"
- Context 链通信模式确立：上游 Agent 产出文档 → 下游 Agent 消费文档
- Agent = Skill 集合 + 编排规则，抽象合理
- v1.0 4 Agent 已 deprecated 且保留兼容

**不足：**
- **Agent 协作仍是串行的**：Project → Requirement → Test Design → Automation → Execution，无并行可能
- **Agent 间状态靠文件传递**：Test Design Agent 产出 TEST_CASES.md → Automation Agent 读取，中间无结构化校验
- **缺少 Agent 调度器**：当前由人工决定"下一步启动哪个 Agent"
- **Knowledge Agent "横向贯穿"机制未落地**：定义上说"每个 Agent 结束时可自动触发"，实际上没有自动触发机制
- **斜杠命令是 CLI 特有能力**：如果未来切换到其他平台，Agent 入口需要重新实现

**提升到 L5 需要：**
- Agent 调度器（自动检测前置条件满足 → 触发下游 Agent）
- Agent 间结构化消息协议（非纯文件传递）
- 横向 Agent 的事件驱动机制

---

#### Knowledge 成熟度：L2（结构化起步）

**优势：**
- known-issues.yaml 结构化（16条，EP/FP/ENV 三类），含 severity/reproduce_rate/solution/affected_modules
- 字段设计合理：first_seen/last_seen/occurrence_count 支持趋势分析
- 与 PROJECT_CONTEXT 双向同步机制

**不足：**
- **无向量化/语义检索**：Bug 分析时靠人工匹配已知问题，无法自动"这个报错看起来像 EP-003"
- **历史 Bug 库缺失**：BUG_ANALYSIS_*.md 散落在 artifacts/ 中，无结构化索引
- **测试案例库缺失**：TEST_CASES.md 按页面存，无法跨模块检索"类似场景的用例"
- **自动化脚本库缺失**：Page Object / test_*.py 无注册表，复用靠人工查找
- **经验库碎片化**：learning/ 目录的踩坑记录未与 known-issues 联动

**提升到 L5 需要：**
- Bug 向量库 + 自动匹配
- 测试案例标签化索引
- Page Object 注册表（方法签名 + 覆盖场景）
- 经验→坑位自动关联

---

#### Tool 成熟度：L2（代码层工具）

**优势：**
- check_code_quality.py：全量/单文件/Stage区扫描 + JSON 输出
- setup_quality_gates.py：pre-commit 钩子安装/检查
- 8 条代码红线 + 4 条自检命令

**不足：**
- **工具仅限代码层**：没有 Context 校验工具、Workflow 执行工具、Skill 测试工具
- **无平台 CLI**：所有操作靠手动执行命令
- **无可视化**：Context 依赖关系、模块状态、测试覆盖率无 Dashboard
- **无自动化触发器**：Git commit / CI 完成后不能自动触发下游流程

**提升到 L5 需要：**
- 统一 CLI 入口（`aitest check/sync/run/report`）
- Context 校验器（检测过期/缺失/冲突）
- Dashboard（模块状态/覆盖率/已知问题趋势）

---

#### Platform 成熟度：L1（CLI 原生）

**优势：**
- Claude Code Native 提供 Agent/Skill/Workflow 执行环境
- VSCode Extension 提供 IDE 集成
- .claude/skills/ 目录提供斜杠命令入口

**不足：**
- **无独立平台**：所有能力绑定在 Claude Code 上，无法对外暴露
- **无 Web UI**：非开发者无法使用
- **无 API 网关**：外部系统（如 Jenkins）无法主动调用 AI 测试能力
- **无多租户/权限**：所有人共用同一套 Context 和 Skill

**提升到 L5 需要：**
- 独立平台服务（FastAPI / Flask）
- Web UI / Dashboard
- REST API + Webhook
- 多项目管理

---

## 三、第二部分：架构审计

### 3.1 问题清单

#### 问题 1：Skill 重复建设（轻微）

| 重叠对 | 重叠内容 | 程度 |
|--------|----------|------|
| `knowledge-extractor` vs `knowledge-precipitation` | 都做"从事件中提取知识并写入知识库" | ⚠️ 中等 |
| `excel-exporter` 被 Execution Agent 和 Report Agent 共享 | 职责归属不唯一 | ⚠️ 轻微 |
| `completeness-check` 被 Project Agent 和 Knowledge Agent 共享 | 同一 Skill 两个 Agent 绑定 | ⚠️ 轻微 |

**分析：**
- `knowledge-extractor` 侧重"单一 Bug → 坑位提取"
- `knowledge-precipitation` 侧重"批量经验 → 知识库更新"
- 两者输入不同但输出目标一致（写入 known-issues.yaml），可合并为一个 Skill 的两个模式

#### 问题 2：Agent 职责重叠（轻微）

| Agent 对 | 重叠领域 | 影响 |
|----------|----------|------|
| Execution Agent ↔ Report Agent | 都涉及"报告生成"（Allure 摘要 vs 测试总结） | 边界模糊 |
| Project Agent ↔ Knowledge Agent | 都涉及"文档完整性检查"（completeness-check） | Skill 共享合理，但需明确 Primary Owner |
| Requirement Agent ↔ Test Design Agent | Phase 0.8 需求分析 vs Phase 1 页面分析，实际使用时常被跳过边界 | 实践中边界模糊 |

#### 问题 3：Workflow 耦合过高（中等）

**具体表现：**
- `module-onboarding` 是超长串行链：module-modeling → requirement-analysis → page-analysis → risk-modeling → element-position，无跳过/并行机制
- 当前 Tank 模块 SOP 全闭环依赖人工推动 13 个步骤，任意一步中断需人工恢复
- Workflow 定义与 Skill 注册表分离，新增 Skill 后需手动更新两端

#### 问题 4：Context 冗余（轻微但分散）

- `PROJECT_CONTEXT.md` § Element Plus 已知坑位 与 `known-issues.yaml` § EP-001~011 内容重复（维护两处）
- `skill-registry.yaml` 中的 Skill 描述 与 各 Skill .md 文件中的描述 存在不一致风险
- `CLAUDE.md` § 口语化入口 与 `skill-registry.yaml` 中的 workflow 关联 存在维护负担

#### 问题 5：知识库碎片化

- known-issues.yaml（16条）
- artifacts/bug-analysis/BUG_ANALYSIS_*.md（已分类存放）
- TestIntern_library/01-学习笔记/（历史踩坑，未结构化）
- PROJECT_CONTEXT § Element Plus 坑位（与 known-issues 重复）
- 四者之间无关联、无检索、无自动更新

#### 问题 6：上下文管理问题

- **会话恢复依赖人工描述**："上次做到哪了"靠 context-sync Skill 和人工记忆
- **CURRENT_TASK 未标准化**：没有结构化的"当前任务状态"文件
- **Context 链断裂风险**：如果 PROJECT_CONTEXT 更新（如新增 EP-012），下游 MODULE_CONTEXT 不会自动感知
- **跨模块依赖不可见**：equipment 页面引用了 system-role 的权限组件，但两个模块的 Context 文件中均未记录此依赖

#### 问题 7：Token 浪费问题

| 浪费来源 | 估算浪费比例 | 说明 |
|----------|-------------|------|
| PROJECT_CONTEXT 全量加载 | ~15% | 200行文件每次全量读入，但单次任务只需其中 30-40% |
| 口语化路由表全量加载 | ~5% | CLAUDE.md 21条映射每次加载，实际只用 1-2 条 |
| Page Object 代码全文读取 | ~20% | tech-analysis 时常全量读入已有 Page Object，只为参考一个定位器写法 |
| 重复读取 BasePage API 参考 | ~10% | 多个 Agent 每次重新读取 PROJECT_CONTEXT 中的 BasePage 60+ API |
| Agent 定义全量加载 | ~5% | 每次启动 Agent 读取完整 Agent .md 文件 |

**Token 优化潜力：约 30-40%**（通过分层加载 + 结构化索引 + RAG 检索）

---

### 3.2 风险矩阵

| 风险 | 概率 | 影响 | 等级 | 触发条件 |
|------|------|------|------|----------|
| Context 链断裂导致代码质量下降 | 中 | 高 | 🔴 高 | PROJECT_CONTEXT 更新后下游未同步 |
| Skill 体量膨胀导致维护困难 | 中 | 中 | 🟡 中 | tech-analysis 继续增加场景 |
| Agent 串行依赖导致效率瓶颈 | 高 | 中 | 🟡 中 | 多模块并行开发时 |
| 知识库碎片化导致经验流失 | 高 | 中 | 🟡 中 | 人员变动/长时间间隔 |
| Token 浪费导致成本失控 | 中 | 低 | 🟢 低 | 模块数量持续增长 |
| 平台绑定 Claude Code 导致迁移困难 | 低 | 高 | 🟡 中 | 未来技术栈变更 |
| Workflow 人工推动导致流程遗漏 | 中 | 中 | 🟡 中 | 复杂模块多步骤操作 |

---

### 3.3 优化建议汇总

| 编号 | 建议 | 优先级 | 预期收益 |
|------|------|--------|----------|
| A-1 | 合并 knowledge-extractor + knowledge-precipitation | P1 | 减少 Skill 数量 + 消除混淆 |
| A-2 | 明确 excel-exporter / completeness-check 的 Primary Owner | P2 | 消除职责歧义 |
| A-3 | module-onboarding 拆分为可独立执行的子流程 | P1 | 提升灵活性 + 支持断点续跑 |
| A-4 | 建立 Context 版本号 + 过期检测机制 | P1 | 防止 Context 链断裂 |
| A-5 | PROJECT_CONTEXT 与 known-issues.yaml 去重 | P2 | 减少维护负担 |
| A-6 | 标准化 CURRENT_TASK 格式 | P1 | 支持会话自动恢复 |
| A-7 | 分层加载 PROJECT_CONTEXT（摘要→完整→API参考） | P2 | Token 节省 30%+ |
| A-8 | 建立 Bug 向量索引 | P2 | 自动匹配已知问题 |
| A-9 | 建立 Page Object 注册表 | P3 | 提升代码复用 |
| A-10 | tech-analysis 按需拆分 | P3 | 控制 Skill 体量 |

---

## 四、第三部分：Skill 架构优化

### 4.1 当前 Skill 评估

#### ✅ 应保留（20 个）

| Skill | 理由 |
|-------|------|
| `project-context-manager` | 项目初始化唯一入口，不可替代 |
| `context-sync` | 会话同步关键能力 |
| `module-modeling` | 模块建模唯一入口 |
| `requirement-analysis` | 需求分析 - 独立场景 |
| `page-analysis` | 核心高频 Skill，页面分析不可替代 |
| `risk-modeling` | 风险驱动测试的关键环节 |
| `testcase-design` | 核心高频 Skill |
| `test-data-generation` | 独立场景，虽使用率低但不可合并 |
| `api-testing` | 接口测试独立场景 |
| `miniapp-testing` | 小程序测试独立场景 |
| `tech-analysis` | 核心高频 Skill（见下方拆分建议） |
| `auto-strategy` | 自动化策略独立决策环节 |
| `page-object-generator` | Page Object 生成——最高频代码生成 |
| `test-script-generator` | 测试脚本生成 |
| `conftest-generator` | conftest 生成（低频但独立） |
| `code-consistency-checker` | 质量门禁，不可替代 |
| `allure-report-analyzer` | Allure 报告解析 |
| `bug-analysis` | 核心诊断 Skill |
| `jenkinsfile-generator` | CI 配置管理 |
| `completeness-check` | 文档完整性审计 |

#### 🔀 应合并（2 对 → 2 个）

| 合并 | 理由 | 新 Skill 名 |
|------|------|-------------|
| `knowledge-extractor` + `knowledge-precipitation` | 输入不同但目标相同（写入知识库），合并为双模式 | `knowledge-manager` |
| `test-summary` + `progress-report` | 产出结构相似（摘要+趋势+计划），合并为统一报告引擎 | `report-generator` |

#### ✂️ 应拆分（1 个）

| Skill | 拆分为 | 理由 |
|-------|--------|------|
| `tech-analysis` | `locator-designer` + `wait-strategy-designer` | 当前体量过大：定位器设计 + 等待策略 + Element Plus 深度定位 + 自定义组件分析。拆分为两个独立 Skill，通过 AUTO_STRATEGY 衔接 |

> ⚠️ **拆分风险**：`tech-analysis` 是当前最成熟的 Skill，拆分可能引入衔接成本。建议 **P3 优先级**，待 Skill 体量确实影响维护时再执行。

#### 🗑️ 应废弃（2 个，已废弃）

| Skill | 状态 |
|-------|------|
| `code-generation` | ✅ 已废弃，由 3 个子 Skill 替代 |
| `element-plus-locator` | ✅ 已废弃，已合并到 tech-analysis |

### 4.2 优化后 Skill 分类体系

```
skills/
├── project/                    # 项目级上下文管理（2个）
│   ├── project-context-manager   ← 项目初始化/索引
│   └── context-sync              ← 会话上下文同步
│
├── requirements/               # 需求与模块（2个）
│   ├── module-modeling           ← 模块边界建模
│   └── requirement-analysis      ← 需求分析
│
├── test-design/                # 测试分析与设计（6个）
│   ├── page-analysis             ← 页面元素分析
│   ├── risk-modeling             ← 风险识别（6维度）
│   ├── testcase-design           ← 测试用例设计（8维度）
│   ├── test-data-generation      ← 测试数据生成
│   ├── api-testing               ← 接口测试设计
│   └── miniapp-testing           ← 小程序测试设计
│
├── automation/                 # 自动化技术实现（6→7个，待拆分）
│   ├── tech-analysis             ← 定位器+等待策略（⚠️ 待拆分为 locator-designer + wait-strategy-designer）
│   ├── auto-strategy             ← 自动化策略决策
│   ├── page-object-generator     ← Page Object 生成
│   ├── test-script-generator     ← 测试脚本生成
│   ├── conftest-generator        ← conftest 生成
│   └── code-consistency-checker  ← 代码合规检查
│
├── execution/                  # 执行与诊断（3个，合并后）
│   ├── allure-report-analyzer   ← Allure 摘要
│   ├── bug-analysis              ← 失败根因分析（单+批量模式）
│   └── jenkinsfile-generator     ← CI 配置管理
│
├── reporting/                  # 报告生成（1个，合并后）
│   └── report-generator          ← 测试总结 + 进度报告 + Excel导出
│       ├── mode: test-summary    ← 子模式：测试周期总结
│       ├── mode: progress        ← 子模式：进度报告
│       └── mode: excel-export    ← 子模式：Excel 导出
│
├── knowledge/                  # 知识管理（2个，合并后）
│   ├── knowledge-manager         ← 知识提取+沉淀（双模式）
│   └── completeness-check        ← 文档完整性审计
│
└── _deprecated/                # 废弃归档（2个）
    ├── code-generation           ← → 3子Skill
    └── element-plus-locator      ← → tech-analysis
```

**优化后统计：26 active Skill（从 26 减至 24-25，取决于 tech-analysis 是否拆分），2 deprecated**

### 4.3 Skill 间接口标准化（中期建议）

当前 Skill 间通过 Markdown 文件传递信息，下游 Skill 需"理解"上游文档。建议为高频 Skill 对定义结构化接口：

```yaml
# 示例：page-analysis → tech-analysis 接口
interface: page-to-tech
source: page-analysis
target: tech-analysis
fields:
  - element_name: string        # 元素名称
  - element_type: enum          # button|input|select|table|dialog|...
  - semantic_description: string # 业务语义
  - suggested_locator_type: enum # CSS|XPATH|text|placeholder|role
  - element_plus_component: string|null  # el-select|el-dialog|null
  - risk_flags: list            # [teleport|dynamic|conditional|animation]
  - interaction_pattern: enum   # click|input|select|wait|scroll
```

> 此优化依赖平台化（第六部分），建议在 P3 阶段实施。

---

## 五、第四部分：Agent 架构优化

### 5.1 当前 Agent 协作关系（现状）

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ ①Project │───▶│ ②Requirement │───▶│ ③Test Design │───▶│ ④Automation  │
│  Agent   │    │    Agent     │    │    Agent     │    │    Agent     │
│ Phase 0  │    │ Phase 0.5~0.8│    │ Phase 1~2.5  │    │ Phase 3~4    │
└──────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                               │
                                      ┌────────────────────────┘
                                      ▼
                              ┌──────────────┐    失败    ┌──────────────┐
                              │ ⑤Execution   │──────────▶│ ⑥Bug Analysis│
                              │    Agent     │           │    Agent     │
                              │ Phase 4.5~7  │           │ Phase 4.5~7  │
                              └──────┬───────┘           └──────┬───────┘
                                     │ 成功                     │
                                     ▼                          ▼
                              ┌──────────────┐          ┌──────────────┐
                              │ ⑦Report      │          │ ⑧Knowledge   │◀── 横向贯穿
                              │    Agent     │          │    Agent     │   所有 Agent
                              │ Phase 8~9    │          │ Phase 9      │
                              └──────────────┘          └──────────────┘
```

### 5.2 问题诊断

1. **纯串行链路**：①→②→③→④ 必须顺序执行，无法并行
2. **Knowledge Agent "横向贯穿"名存实亡**：没有事件触发机制，实际靠人工记得调用
3. **Execution Agent 与 Report Agent 边界模糊**：都产出"报告"，容易混淆
4. **无反馈回路**：Bug Analysis 发现根因后不能自动触发 Automation Agent 修复
5. **无 Agent 调度器**：每个 Agent 的启动条件需人工判断

### 5.3 目标 Agent 架构设计

#### 5.3.1 Agent 职责重定义

| Agent | 职责（一句话） | 输入 | 输出 | 触发条件 |
|-------|---------------|------|------|----------|
| **Project Agent** | 项目级骨架初始化与健康审计 | 代码仓库 / 旧资产 | PROJECT_CONTEXT + MODULE_INDEX + 完整性报告 | 新项目接入 / 审计请求 |
| **Requirement Agent** | 模块边界建模与需求分析 | 原型/PRD + PROJECT_CONTEXT | MODULE_CONTEXT + REQUIREMENT_ANALYSIS | 新模块入场 |
| **Test Design Agent** | 页面→风险→测试用例完整设计 | MODULE_CONTEXT + 页面截图/HTML | PAGE_CONTEXT + RISK_MODEL + TEST_DESIGN + TEST_CASES | MODULE_CONTEXT 就绪 |
| **Automation Agent** | 定位器设计→代码生成→合规检查 | PAGE_CONTEXT + TEST_CASES + HTML源码 | TECH_ANALYSIS + AUTO_STRATEGY + PageObject + test_*.py | TEST_CASES 就绪 |
| **Execution Agent** | 测试执行 + 结果收集 + 路由 | 模块名/marker + allure-results/ | 执行结果 + Allure 摘要 → 路由到 Report/Bug Analysis | 代码就绪 / CI 触发 |
| **Bug Analysis Agent** | 失败根因分析 + 修复建议 | 失败日志 + 截图 + 代码上下文 | BUG_ANALYSIS + Root Cause + 修复建议 | 执行失败（自动/手动） |
| **Report Agent** | 测试总结 + 进度报告 + Excel 导出 | 执行结果 + Bug 统计 + 进度数据 | TEST_SUMMARY + 周报 + Excel | 测试周期结束 / 定期 |
| **Knowledge Agent** | 知识提取 + 沉淀 + 审计（事件驱动） | 任意 Agent 的产出 | known-issues 更新 + 经验沉淀 + 完整性报告 | 事件触发（Agent 完成 / Bug 关闭 / 周期结束） |

#### 5.3.2 优化后协作关系

```
                        ┌──────────────────────────────────────┐
                        │          Agent Scheduler             │
                        │  (检测前置条件 → 触发下游Agent)        │
                        └──────────────────────────────────────┘
                                          │
        ┌────────────┬────────────┬───────┼───────┬────────────┬────────────┐
        ▼            ▼            ▼       │       ▼            ▼            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐   │  ┌─────────┐ ┌─────────┐ ┌─────────┐
   │①Project │ │②Req     │ │③Test    │   │  │⑤Execute │ │⑥Bug     │ │⑦Report  │
   │  Agent  │ │  Agent  │ │  Design │   │  │  Agent  │ │  Analysis│ │  Agent  │
   └────┬────┘ └────┬────┘ └────┬────┘   │  └────┬────┘ └────┬────┘ └────┬────┘
        │          │          │         │       │          │          │
        └──────────┴──────────┴─────────┘       └──────────┴──────────┘
                          │                                    │
                          ▼                                    ▼
                    ┌──────────────────────────────────────────────┐
                    │          ⑧ Knowledge Agent (事件驱动)         │
                    │  监听: AgentCompleted / BugClosed / CycleEnd  │
                    │  动作: 提取知识 → 去重 → 沉淀 → 通知订阅者     │
                    └──────────────────────────────────────────────┘
```

#### 5.3.3 状态流转

```
模块状态机：
  [未纳管] → Project Agent → [已索引]
  [已索引] → Requirement Agent → [已建模]
  [已建模] → Test Design Agent → [已设计]
  [已设计] → Automation Agent → [已自动化]
  [已自动化] → Execution Agent → [执行中]
  [执行中] → 全部通过 → Report Agent → [已闭环]
  [执行中] → 有失败 → Bug Analysis Agent → [待修复] → Automation Agent → [已自动化]

跨模块状态：
  Knowledge Agent 监听所有状态变更 → 自动沉淀 + 更新索引
```

#### 5.3.4 边界划分（强化版）

| 边界规则 | 内容 |
|----------|------|
| **代码边界** | 只有 Automation Agent 能写入 `ZJSN_Test-master526/page/` 和 `script/` |
| **Context 边界** | Project / Requirement / Test Design Agent 写入 `governance/context/`；Execution / Bug Analysis Agent 写入 `governance/artifacts/`（bug-analysis/ | test-summaries/ | sop-status/ 等子目录） |
| **知识边界** | 只有 Knowledge Agent 能写入 `known-issues.yaml` 和 `PROJECT_CONTEXT.md` 坑位清单 |
| **执行边界** | 只有 Execution Agent 能执行 `pytest` 命令 |
| **报告边界** | Report Agent 负责汇总报告；Execution Agent 只负责执行级摘要 |
| **Skill 归属** | 每个 Skill 有唯一 Primary Agent Owner，共享 Skill 标注 Primary → Secondary |

**Skill Primary Owner 明确化：**

| 共享 Skill | Primary Agent | Secondary Agent | 使用场景 |
|------------|---------------|-----------------|----------|
| `excel-exporter` | **Report Agent** | Execution Agent | Report Agent 为主要使用者 |
| `completeness-check` | **Project Agent** | Knowledge Agent | Project Agent 负责项目级完整性 |
| `ci-pipeline-analysis` | **Bug Analysis Agent** | — | 不再共享，仅 Bug Analysis 使用 |

#### 5.3.5 依赖关系矩阵

| | Project | Requirement | Test Design | Automation | Execution | Bug Analysis | Report | Knowledge |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Project** | — | — | — | — | — | — | — | — |
| **Requirement** | 读 PROJECT | — | — | — | — | — | — | — |
| **Test Design** | 读 PROJECT | 读 MODULE | — | — | — | — | — | — |
| **Automation** | 读 PROJECT | — | 读 PAGE+TEST | — | — | — | — | — |
| **Execution** | — | — | — | 读代码 | — | — | — | — |
| **Bug Analysis** | — | — | — | 读代码 | 读结果 | — | — | — |
| **Report** | — | — | — | — | 读结果 | 读 Bug | — | — |
| **Knowledge** | 读+写 | 读 | 读 | 读 | 读 | 读 | 读 | — |

> 读 = 读取该 Agent 产出；写 = Knowledge Agent 唯一可写 Context

---

## 六、第五部分：知识库设计

### 6.1 知识库需求评估

| 知识库类型 | 当前状态 | 建设价值 | ROI | 优先级 | 建议 |
|------------|----------|----------|-----|--------|------|
| **RAG（检索增强生成）** | 无 | ⭐⭐⭐⭐⭐ | 🔴 高 | P1 | **最值得建设**——直接解决 Token 浪费 + Context 断裂 |
| **向量数据库** | 无 | ⭐⭐⭐⭐ | 🟡 中高 | P2 | 支撑 RAG + 已知问题自动匹配 |
| **长期记忆（Memory）** | Claude 原生（未使用） | ⭐⭐⭐ | 🟢 中 | P2 | 跨会话偏好/决策记忆 |
| **经验库（Pitfall DB）** | known-issues.yaml（16条） | ⭐⭐⭐⭐ | 🟡 中高 | P2 | 结构化经验 + 自动匹配 |
| **历史 Bug 库** | artifacts/ 散落 | ⭐⭐⭐⭐ | 🟡 中高 | P2 | Bug 趋势分析 + 回归风险预测 |
| **测试案例库** | TEST_CASES.md 散落 | ⭐⭐⭐ | 🟢 中 | P3 | 跨模块用例复用 |
| **自动化脚本库** | .py 文件 | ⭐⭐⭐ | 🟢 中 | P3 | Page Object 方法复用 |

### 6.2 详细分析

#### 6.2.1 RAG — 最值得建设（P1）

**为什么需要：**
- 当前 PROJECT_CONTEXT（200行）每次全量加载，Token 浪费严重
- 已有 Page Object 代码是最好的"定位器写法示例库"，但每次靠人工 grep
- Bug 分析时需手动查找历史类似问题

**方案：**
```
┌─────────────────────────────────────────────────────┐
│                   RAG 知识检索层                      │
├─────────────────────────────────────────────────────┤
│  索引源：                                            │
│  ├── PROJECT_CONTEXT.md（分块：BasePage API / 规范 / 坑位） │
│  ├── 所有 PAGE_CONTEXT.md（页面元素语义描述）          │
│  ├── 所有 TECH_ANALYSIS.md（定位器设计表）             │
│  ├── 所有 Page Object .py（代码片段 + 方法签名）       │
│  ├── known-issues.yaml（结构化坑位）                   │
│  └── BUG_ANALYSIS_*.md（历史 Bug 分析）               │
│                                                      │
│  检索场景：                                           │
│  ├── "这个报错是什么已知问题？" → 检索 known-issues    │
│  ├── "el-cascader 怎么定位？" → 检索 TECH_ANALYSIS    │
│  ├── "类似页面的 Page Object 怎么写？" → 检索 .py     │
│  └── "这个模块的测试策略是什么？" → 检索 PAGE_CONTEXT  │
└─────────────────────────────────────────────────────┘
```

**推荐技术栈：**
- 嵌入模型：text-embedding-3-small（便宜）或本地 all-MiniLM-L6-v2（免费）
- 向量库：ChromaDB（轻量，Python 原生）或 LanceDB（无服务端）
- 检索策略：Hybrid（向量 + BM25 关键词）

**ROI 分析：**
- 成本：~$0.02/1M tokens embedding + ChromaDB 自托管（免费）
- 收益：Token 节省 30-40%，Bug 匹配速度提升 10x，代码参考效率提升 5x
- 回本周期：< 1 周

#### 6.2.2 向量数据库（P2，与 RAG 配套）

不需要独立建设。ChromaDB 或 LanceDB 作为 RAG 的存储后端即可。不推荐 Pinecone/Weaviate 等重量级方案。

#### 6.2.3 长期记忆（P2）

Claude Code 已提供 Memory 机制但当前未使用。建议：
- 激活 Memory 用于跨会话决策记录（如"tank 模块使用自定义 UI 框架"、"production 模块暂不自动化"）
- 不替代 Context 文档——Memory 存偏好/决策，Context 存事实

#### 6.2.4 经验库（P2）

在 known-issues.yaml 基础上扩展：

```yaml
# 扩展方向
pitfalls:
  - id: PIT-001
    pattern: "el-cascader 级联选择器动态加载子选项"
    detection_signature: "NoSuchElementException.*cascader"
    auto_match: true           # bug-analysis 自动匹配
    solution_template: |       # 可参数化的解决方案
      WebDriverWait(driver, 10).until(
          EC.presence_of_element_located((By.CSS_SELECTOR, ".el-cascader-node"))
      )
    code_examples:             # 关联的实际代码
      - file: page/equipment_page/AlarmConfigPage.py
        method: select_cascader_option
```

#### 6.2.5 历史 Bug 库（P2）

**值得建设，但需要结构化：**
```yaml
bug_history:
  - id: BUG-2026-0611-001
    date: 2026-06-11
    module: equipment
    page: unit_management
    error_type: NoSuchElementException
    root_cause: "自定义组件 stat-card 渲染晚于 document.readyState"
    matched_known_issue: FP-004
    fix: "navigate 末尾增加显式等待 WebDriverWait"
    fix_files: ["base/base_page.py"]
    regression_risk: low
    tags: [custom-component, timing, wait-strategy]
```

**ROI：** 中等。前 3 个月收益不明显（Bug 样本不足），6 个月后趋势分析价值凸显。

#### 6.2.6 测试案例库（P3）

**当前不值得独立建设。**
- TEST_CASES.md 按页面组织已经满足需求
- 跨模块用例复用场景有限（每个模块业务差异大）
- ROI 低：结构化成本高，复用收益低

**替代方案：** 在 RAG 中索引 TEST_CASES.md 即可，不需要独立数据库。

#### 6.2.7 自动化脚本库（P3）

**当前不值得独立建设。**
- Page Object 代码量尚在可控范围（10 模块 × ~3-5 Page = 30-50 文件）
- 方法签名可通过 IDE 的 Go-to-Definition 查找
- ROI 低：建立注册表维护成本高于收益

**替代方案：** Page Object 注册表可作为 RAG 的一个索引维度，不需要独立系统。

### 6.3 知识库建设优先级路线

```
第 1 个月：RAG 原型
  ├── ChromaDB 搭建
  ├── PROJECT_CONTEXT + known-issues 索引入库
  └── bug-analysis Skill 接入 RAG（自动匹配已知问题）

第 2-3 个月：知识库扩展
  ├── PAGE_CONTEXT + TECH_ANALYSIS 索引入库
  ├── Page Object 代码索引入库
  ├── Memory 激活（跨会话决策记录）
  └── 经验库结构化扩展

第 4-6 个月：智能化
  ├── 历史 Bug 库建设
  ├── Bug 趋势分析 Dashboard
  └── 自动推荐修复方案
```

---

## 七、第六部分：自动化测试平台设计

### 7.1 目标架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI 自动化测试平台 (AITest Platform)                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      接入层 (Access Layer)                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │   │
│  │  │ VSCode   │  │ CLI      │  │ Web UI   │  │ API Gateway      │ │   │
│  │  │ Extension│  │ (aitest) │  │ (React)  │  │ (FastAPI+Webhook)│ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      编排层 (Orchestration Layer)                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐│   │
│  │  │ Agent        │  │ Workflow     │  │ Event Bus                ││   │
│  │  │ Scheduler    │  │ Engine (DAG) │  │ (AgentCompleted, etc.)   ││   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘│   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      能力层 (Capability Layer)                     │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐ │   │
│  │  │ 8      │ │ 24+    │ │ 9      │ │ RAG    │ │ Tool Chain     │ │   │
│  │  │ Agents │ │ Skills │ │Workflows│ │ Engine │ │ (check/sync/   │ │   │
│  │  │        │ │        │ │        │ │        │ │  run/report)    │ │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      数据层 (Data Layer)                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐│   │
│  │  │ Context  │ │ Knowledge│ │ Vector   │ │ Artifacts            ││   │
│  │  │ Store    │ │ Base     │ │ Store    │ │ Store                ││   │
│  │  │ (Markdown│ │ (YAML+DB)│ │(ChromaDB)│ │ (Markdown+Screenshots││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘│   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      基础设施层 (Infrastructure)                   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐│   │
│  │  │ Jenkins  │ │ pytest   │ │ Selenium │ │ Claude API / LLM     ││   │
│  │  │ CI/CD    │ │ Framework│ │ Grid     │ │ Provider             ││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘│   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 模块划分

| 层 | 模块 | 职责 | 技术选型 |
|----|------|------|----------|
| **接入层** | VSCode Extension | IDE 内 Agent/Skill 调用 | 已有（Claude Code VSCode） |
| | CLI (`aitest`) | 命令行统一入口 | Python Click/Typer |
| | Web UI | 非开发者使用 + Dashboard | React + Flask/FastAPI |
| | API Gateway | 外部系统集成（Jenkins Webhook） | FastAPI + Pydantic |
| **编排层** | Agent Scheduler | 检测前置条件 → 自动触发下游 Agent | Python 状态机 |
| | Workflow Engine | DAG 定义 + 断点续跑 + 并行执行 | YAML/JSON DAG + Prefect/Temporal（可选） |
| | Event Bus | AgentCompleted / BugClosed / CycleEnd 事件 | Redis Pub/Sub 或内存事件 |
| **能力层** | 8 Agents | 测试全生命周期 | Claude API + Agent SDK |
| | 24+ Skills | 可复用 AI 能力 | Skill Markdown + Prompt 模板 |
| | 9 Workflows | 多步骤协作流程 | DAG 定义文件 |
| | RAG Engine | 知识检索 + 自动匹配 | ChromaDB + embedding |
| | Tool Chain | 代码检查/同步/执行/报告 | Python 脚本集 |
| **数据层** | Context Store | 项目/模块/页面级上下文 | Markdown + YAML |
| | Knowledge Base | 已知问题 + 经验 + Bug 历史 | YAML + SQLite |
| | Vector Store | RAG 向量索引 | ChromaDB |
| | Artifacts Store | 过程产物（Bug 分析/报告） | Markdown + 截图 |
| **基础设施** | Jenkins CI/CD | 自动化调度 | 已有 |
| | pytest + Selenium | 测试执行 | 已有 |
| | Claude API | LLM 推理 | 已有 |

### 7.3 数据流

```
┌─────────────────────────────────────────────────────────────────────┐
│                          主数据流 (Happy Path)                        │
│                                                                      │
│  用户输入                                                             │
│    │                                                                  │
│    ▼                                                                  │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐           │
│  │Project  │───▶│Req      │───▶│Test     │───▶│Auto-    │           │
│  │Agent    │    │Agent    │    │Design   │    │mation   │           │
│  │         │    │         │    │Agent    │    │Agent    │           │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘           │
│       │              │              │              │                 │
│       ▼              ▼              ▼              ▼                 │
│  PROJECT_       MODULE_       PAGE_CONTEXT   PageObject.py           │
│  CONTEXT.md     CONTEXT.md    RISK_MODEL     test_*.py               │
│  MODULE_INDEX   REQ_ANALYSIS  TEST_DESIGN    conftest.py             │
│                               TEST_CASES                             │
│                                                                      │
│                                          ┌─────────┐                │
│                                          │Execution│                │
│                                          │Agent    │                │
│                                          └────┬────┘                │
│                                               │                     │
│                                    ┌──────────┴──────────┐          │
│                                    │                     │          │
│                                    ▼ 成功                ▼ 失败      │
│                              ┌─────────┐          ┌─────────┐       │
│                              │Report   │          │Bug      │       │
│                              │Agent    │          │Analysis │       │
│                              └────┬────┘          │Agent    │       │
│                                   │               └────┬────┘       │
│                                   │                    │            │
│                                   ▼                    ▼            │
│                              TEST_SUMMARY        BUG_ANALYSIS       │
│                              Excel Report        Root Cause         │
│                                                  Fix Suggestion     │
│                                                                      │
│                              ┌────────────────────────┐             │
│                              │   Knowledge Agent      │             │
│                              │   (事件驱动，持续监听)   │             │
│                              └────────────┬───────────┘             │
│                                           │                         │
│                                           ▼                         │
│                              known-issues.yaml 更新                 │
│                              PROJECT_CONTEXT 坑位更新                │
│                              Vector Store 索引更新                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.4 调用链（以"为 equipment/alarm-config 新增自动化"为例）

```
1. 用户: "为 equipment 模块的 alarm-config 页面生成自动化测试"

2. Agent Scheduler 检测前置条件:
   ├── PROJECT_CONTEXT.md ✅ 存在
   ├── MODULE_CONTEXT (equipment) ✅ 存在
   ├── PAGE_CONTEXT (alarm-config) ❌ 缺失
   └── 决策: 从 Test Design Agent 开始

3. Test Design Agent:
   ├── page-analysis Skill → PAGE_CONTEXT.md
   ├── risk-modeling Skill → RISK_MODEL.md
   ├── testcase-design Skill → TEST_DESIGN.md + TEST_CASES.md
   └── 触发事件: AgentCompleted(test-design, equipment/alarm-config)

4. Agent Scheduler 检测: TEST_CASES 就绪 → 触发 Automation Agent

5. Automation Agent:
   ├── RAG 检索: "alarm-config 类似页面的定位器写法"
   ├── tech-analysis Skill → TECH_ANALYSIS.md
   ├── auto-strategy Skill → AUTO_STRATEGY.md
   ├── page-object-generator → AlarmConfigPage.py
   ├── test-script-generator → test_alarm_config.py
   ├── code-consistency-checker → 合规检查 ✅
   └── 触发事件: AgentCompleted(automation, equipment/alarm-config)

6. Agent Scheduler 检测: 代码就绪 → 询问是否执行

7. 用户: "执行"

8. Execution Agent:
   ├── pytest script/equipment/test_alarm_config.py -v --alluredir=allure-results
   ├── allure-report-analyzer → 报告摘要
   ├── 3/5 通过, 2 失败 → 触发事件: TestFailed(equipment/alarm-config, 2 failures)

9. Agent Scheduler 检测: 有失败 → 自动触发 Bug Analysis Agent

10. Bug Analysis Agent:
    ├── RAG 检索: 失败签名 → 匹配 EP-003 (loading 遮罩不消失)
    ├── bug-analysis Skill → BUG_ANALYSIS.md
    └── 触发事件: BugClosed(equipment/alarm-config, EP-003)

11. Knowledge Agent (事件驱动):
    ├── 检测 BugClosed → 更新 known-issues EP-003 occurrence_count +1
    ├── 判断: 是否需要沉淀新知识? → 否 (已匹配已知问题)
    └── 更新 Vector Store 索引
```

### 7.5 架构关键决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| LLM 层 | Claude API（当前）+ 保留其他模型接入能力 | 已深度绑定 Claude Code，不重复建设 |
| 向量库 | ChromaDB | 轻量、Python 原生、零运维 |
| 编排引擎 | 自研轻量 YAML DAG（阶段1）→ Prefect（阶段3） | 避免过早引入重量级框架 |
| Web UI | 暂不建设（阶段1-2），CLI + VSCode 优先 | 当前用户为开发者，Web UI ROI 低 |
| API Gateway | FastAPI（阶段2） | Jenkins Webhook 集成需求 |
| 数据库 | SQLite（知识库）+ ChromaDB（向量）+ Markdown（Context） | 零运维，单机足够 |

---

## 八、第七部分：扩展能力分析

### 8.1 技术评估矩阵

| 技术 | 适用时机 | 收益 | 复杂度 | 优先级 | 建议 |
|------|----------|------|--------|--------|------|
| **MCP (Model Context Protocol)** | 现在 | ⭐⭐⭐⭐⭐ | 🟢 低 | **P0** | **立即接入** |
| **OpenAI Agent SDK** | 备用 | ⭐⭐ | 🟢 低 | P3 | 观望 |
| **LangChain** | 6个月后 | ⭐⭐⭐ | 🔴 高 | P3 | 暂不引入 |
| **LangGraph** | 6个月后 | ⭐⭐⭐⭐ | 🔴 高 | P3 | 需要时评估 |
| **Dify** | 12个月后 | ⭐⭐⭐ | 🟡 中 | P4 | Web UI 阶段考虑 |
| **A2A (Agent-to-Agent)** | 12个月后 | ⭐⭐⭐⭐ | 🔴 高 | P4 | 多团队协作时 |
| **多 Agent 协作** | 3个月后 | ⭐⭐⭐⭐ | 🟡 中 | P2 | 在 Workflow Engine 中实现 |

### 8.2 详细分析

#### MCP (Model Context Protocol) — P0 立即接入

**为什么：**
- MCP 是 Anthropic 官方的工具/资源标准化协议，Claude Code 原生支持
- 当前项目的 Tool 层（check_code_quality.py 等）可以通过 MCP Server 标准化暴露给 Agent
- 无需额外框架，直接在 `.claude/mcp.json` 配置

**接入方案：**
```json
// .claude/mcp.json
{
  "mcpServers": {
    "aitest-tools": {
      "command": "python",
      "args": ["-m", "aitest.mcp_server"],
      "tools": [
        "check_code_quality",
        "get_module_status",
        "search_known_issues",
        "run_test",
        "generate_report"
      ]
    },
    "aitest-knowledge": {
      "command": "python",
      "args": ["-m", "aitest.knowledge_server"],
      "resources": [
        "known-issues://*",
        "page-context://*",
        "test-cases://*"
      ]
    }
  }
}
```

**收益：**
- Tool 标准化：所有工具通过统一协议暴露
- Knowledge 资源化：Context 通过 `resource://` URI 按需加载（解决 Token 浪费）
- 跨 Agent 复用：MCP Tool 可被所有 Agent 共享

**复杂度：** 低。Python MCP SDK（`mcp`）已可用，实现 2-3 个 MCP Server 约 2-3 天。

#### OpenAI Agent SDK — P3 观望

- 当前项目深度绑定 Claude Code，切换 LLM Provider 不是短期需求
- 如果未来需要支持多模型（如 GPT-5 在某些任务上更优），再评估
- 建议：在 Automation Agent 中预留 LLM Provider 抽象层，但不急于实现

#### LangChain — P3 暂不引入

**不建议当前引入的原因：**
1. 项目已有自己的 Agent/Workflow/Skill 编排体系，LangChain 的 Agent/Chain 抽象与之重叠
2. LangChain 抽象层重，引入后会与现有 Claude Code 原生能力产生摩擦
3. 项目规模尚不需要 LangChain 的复杂编排（如 LCEL、RunnableBranch）

**未来适用时机：**
- 当 Workflow Engine 需要更复杂的条件分支/循环/并行时
- 当需要接入多种 LLM Provider 时
- 当需要 LangSmith 可观测性时

#### LangGraph — P3 需要时评估

- LangGraph 的核心价值是带状态的 Agent 工作流（StateGraph），适合复杂多步骤 Agent 协作
- 当前 8 Agent 串行链路不需要 LangGraph 的状态管理
- 当 Agent 间需要复杂的条件路由 + 状态持久化时再评估

**对比：自研 YAML DAG vs LangGraph**

| 维度 | 自研 YAML DAG | LangGraph |
|------|-------------|-----------|
| 开发成本 | 1-2 周 | 2-4 周（学习+集成） |
| 灵活性 | 中（预设路径） | 高（动态路由） |
| 可维护性 | 高（简单） | 中（需理解 LangGraph 概念） |
| 可观测性 | 需自建 | LangSmith 自带 |
| 适用场景 | 确定性流程 | 非确定性/自适应流程 |

**建议：** 当前用自研 YAML DAG 覆盖 90% 场景，LangGraph 仅当需要"Agent 自主决策下一步"时引入。

#### Dify — P4 Web UI 阶段考虑

- Dify 是面向非开发者的 LLM 应用编排平台，提供可视化 Workflow 编排
- 当前项目用户为测试开发工程师，CLI + VSCode 已满足需求
- 当需要让测试业务人员（非开发者）使用 AI 测试能力时，Dify 的 Web UI 有价值

#### A2A (Agent-to-Agent Protocol) — P4 远期

- Google 的 A2A 协议解决跨系统/跨团队 Agent 通信
- 当前 8 Agent 在同一项目内协作，不需要跨系统通信
- 当需要与外部 Agent 系统（如开发团队的代码审查 Agent）协作时引入

#### 多 Agent 协作 — P2 在 Workflow Engine 中实现

不建议引入外部多 Agent 框架（如 AutoGen、CrewAI），而是在自研 Workflow Engine 中实现：
- **确定性协作**：Workflow 定义的 Agent DAG，适合 90% 的测试场景
- **非确定性协作**：Agent Scheduler 根据事件动态触发，适合 Knowledge Agent 横向贯穿

### 8.3 扩展优先级路线

```
立即（第 1 个月）：
  └── MCP 接入：aitest-tools MCP Server + aitest-knowledge MCP Server

第 2-3 个月：
  └── 多 Agent 协作：Workflow Engine + Agent Scheduler + Event Bus

第 4-6 个月：
  ├── LangGraph 评估（如果自研 DAG 不够用）
  └── OpenAI Agent SDK 评估（如果需要多 LLM Provider）

第 7-12 个月：
  ├── Dify 评估（如果需要 Web UI）
  └── A2A 评估（如果需要跨团队协作）
```

---

## 九、第八部分：路线图规划

### 9.1 1 个月路线图（基础夯实）

**目标：消除已知问题，建立核心基础设施**

| 周次 | 任务 | 产出 | 验收标准 |
|------|------|------|----------|
| **W1** | Skill 合并（knowledge-extractor + knowledge-precipitation → knowledge-manager） | 合并后的 Skill + 注册表更新 | 2 个 Skill 合并为 1 个双模式 Skill |
| | Skill Primary Owner 明确化（excel-exporter / completeness-check） | skill-registry.yaml 更新 | 每个共享 Skill 标注 Primary Agent |
| | Agent 边界文档更新 | 8 Agent .md 文件更新 | 边界描述无歧义 |
| **W2** | MCP Server 原型 — aitest-tools | `aitest/mcp_server.py` | `check_code_quality` / `search_known_issues` 可通过 MCP 调用 |
| | MCP Server 原型 — aitest-knowledge | `aitest/knowledge_server.py` | `PROJECT_CONTEXT` / `known-issues` 可通过 `resource://` 按需加载 |
| **W3** | CURRENT_TASK 标准化 | `templates/current-task.template.md` + context-sync 适配 | 会话恢复只需读取 CURRENT_TASK.md |
| | Context 版本号机制 | PROJECT_CONTEXT + MODULE_INDEX 增加 version + last_updated | 版本号写入文件头部 |
| **W4** | 整合测试 + 文档更新 | 用新机制完成一个模块的完整 SOP（如 sales 模块） | 全流程无阻塞，Token 消耗对比基线 |

**1 个月后关键指标：**
- Skill 数量：26 → 25
- MCP Tool 数量：0 → 5+
- 会话恢复时间：人工描述 → 读取 CURRENT_TASK.md（< 30s）
- Token 节省：基线对比（目标 -15%）

---

### 9.2 3 个月路线图（体系升级）

**目标：完成 RAG + Workflow Engine + Agent Scheduler**

| 月次 | 任务 | 产出 | 验收标准 |
|------|------|------|----------|
| **M2** | ChromaDB 搭建 + 数据入库 | Vector Store（PROJECT_CONTEXT + known-issues + TECH_ANALYSIS 索引） | `search_known_issues("el-cascader 定位失败")` 返回 EP-001 |
| | RAG Engine 接入 bug-analysis Skill | bug-analysis Skill 自动匹配已知问题 | 失败分析时自动展示 Top-3 匹配的 known-issue |
| | test-summary + progress-report → report-generator 合并 | 合并后的 report-generator Skill | 3 种模式（test-summary / progress / excel-export）通过参数切换 |
| **M3** | Workflow Engine — YAML DAG 定义 + 执行器 | `aitest workflow run module-onboarding --module=lab` | module-onboarding 的 5 个步骤自动顺序执行 |
| | Workflow Engine — 断点续跑 | 中断后 `--resume` 从断点继续 | 执行到第 3 步中断，resume 后从第 3 步开始 |
| | Agent Scheduler — 前置条件检测 + 自动触发 | `aitest agent auto --module=lab` | 自动检测 MODULE_CONTEXT 存在 → 跳过 Requirement Agent → 触发 Test Design Agent |
| **M4** | Knowledge Agent 事件驱动改造 | Event Bus + AgentCompleted / BugClosed 事件监听 | Bug Analysis Agent 完成后 Knowledge Agent 自动触发 |
| | RAG 扩展：Page Object 代码索引 | 所有 Page Object .py 索引入库 | "怎么写 el-cascader 的定位器" → 返回已有代码示例 |
| | Memory 激活：跨会话决策/偏好记录 | Claude Memory 文件 | 跨会话自动记住"tank 模块使用自定义框架"等决策 |

**3 个月后关键指标：**
- 已知问题自动匹配率：> 70%
- Workflow 自动化率：人工驱动 → 引擎驱动（80% 步骤自动）
- Agent 自动触发率：> 60%
- Token 节省：基线对比（目标 -30%）

---

### 9.3 6 个月路线图（平台化 + 智能化）

**目标：平台雏形 + 持续学习闭环**

| 月次 | 任务 | 产出 | 验收标准 |
|------|------|------|----------|
| **M5** | CLI 统一入口（`aitest`） | `aitest check/sync/run/report/agent/workflow` 子命令 | 所有测试操作通过 `aitest` CLI 完成 |
| | API Gateway（FastAPI） | `/api/agent/trigger`, `/api/workflow/run`, `/api/report/generate` | Jenkins Webhook 可触发 AI 工作流 |
| | Jenkins 集成：CI 失败 → 自动触发 Bug Analysis Agent | Jenkinsfile 更新 + Webhook | CI 构建失败后 5 分钟内自动生成 BUG_ANALYSIS |
| **M6** | 历史 Bug 库建设 | SQLite bug_history 表 + 结构化导入脚本 | BUG_ANALYSIS_*.md 批量结构化入库 |
| | Bug 趋势 Dashboard（CLI 版） | `aitest report trends --module=equipment` | 模块 Bug 趋势 + Top-5 高频失败 + 修复率 |
| | Page Object 注册表（RAG 增强） | "find similar page objects" 检索接口 | 输入页面描述 → 返回 Top-5 最相似的已有 Page Object |
| **M7** | tech-analysis 拆分评估 | 基于 6 个月使用数据判断是否拆分 | 如 Tech Analysis Skill 体量 > 500 行 → 执行拆分 |
| | 测试案例跨模块推荐 | RAG 检索 "类似测试场景的已有用例" | 设计新页面测试用例时推荐可复用用例 |
| | 持续学习闭环验证 | Bug → 分析 → 修复 → 沉淀 → 预防 → 验证 | 同一 Bug 重复出现率下降 50% |

**6 个月后关键指标：**
- 平台 CLI 命令完整度：100%（所有操作可通过 CLI 执行）
- Bug 自动分析率：> 80%（CI 失败自动触发 Bug Analysis）
- 知识库沉淀数：> 50 条（known-issues + pitfalls + bug_history）
- 新模块入场时间：Tank 模块 13 步骤 → 目标 < 5 步骤（自动化编排）
- 代码红线违规率：→ 0（pre-commit + code-consistency-checker 全覆盖）

---

### 9.4 路线图总览

```
Month 1          Month 2          Month 3          Month 4          Month 5          Month 6
├────────────────┼────────────────┼────────────────┼────────────────┼────────────────┼────────────┤
│ Skill合并       │                │                │                │                │            │
│ Agent边界明确   │ RAG原型        │ Workflow Engine│                │                │            │
│ MCP 接入       │ RAG接入Bug分析  │ Agent Scheduler│ Event Bus      │ CLI 统一入口   │ Bug历史库   │
│ CURRENT_TASK   │ Skill合并(报告) │ 断点续跑        │ RAG扩展(PO代码) │ API Gateway   │ Dashboard   │
│ Context版本号   │                │                │ Memory激活      │ Jenkins集成    │ PO注册表    │
│                │                │                │                │                │ 持续学习闭环│
├────────────────┼────────────────┼────────────────┼────────────────┼────────────────┼────────────┤
│ ▲ 基础夯实      │ ▲ 体系升级      │ ▲ 体系升级      │ ▲ 智能化        │ ▲ 平台化       │ ▲ 持续学习  │
│ 复用率: +15%   │ 复用率: +30%   │ 自动化率: +40% │ 知识率: +50%   │ 效率: +60%    │ 效率: +80%  │
└────────────────┴────────────────┴────────────────┴────────────────┴────────────────┴────────────┘
```

---

## 十、风险评估

### 10.1 实施风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| **过度设计** — 平台化过早导致维护负担 | 中 | 高 | 严格遵循"MVP 优先"原则：CLI 优先 Web UI，YAML DAG 优先自研引擎 |
| **MCP 接入失败** — Python MCP SDK 不稳定 | 低 | 中 | 降级方案：MCP 失败时回退到直接函数调用 |
| **RAG 质量不足** — 检索结果不准导致误导 | 中 | 高 | 先小范围试点（仅 known-issues 索引），验证准确率后再扩展 |
| **Workflow Engine 复杂度失控** — 自研 DAG 引擎功能膨胀 | 中 | 中 | 硬约束：仅支持 3 种节点（顺序/条件/并行），不做通用引擎 |
| **Context 版本号机制被忽略** — 团队成员不更新版本号 | 高 | 低 | 自动化检测：`aitest check --stale` 检测过期 Context |
| **Token 优化反效果** — 分层加载导致信息缺失 | 低 | 中 | 渐进式：先做 RAG 检索增强，不做强分层 |
| **人员变动导致知识断层** | 中 | 高 | 知识全部文件化（非人脑），CLAUDE.md 作为唯一入口 |

### 10.2 不做什么（明确边界）

为了避免过度设计，明确**不在 6 个月内做**的事情：

| 不做 | 理由 |
|------|------|
| ❌ 自研 LLM Agent 框架 | Claude Code + MCP 已足够 |
| ❌ Web UI / Dashboard（图形化） | CLI Dashboard（`aitest report trends`）满足需求 |
| ❌ 多租户/权限系统 | 当前单团队使用 |
| ❌ 测试数据工厂（全自动生成） | 业务差异大，ROI 低 |
| ❌ 视觉回归测试（AI 截图对比） | 不属于当前核心痛点 |
| ❌ 性能测试自动化 | 需求不明确 |
| ❌ 安全测试自动化 | 非当前优先级 |
| ❌ 微服务化 | 单体应用足够（单机即可运行全部组件） |

### 10.3 关键成功因素

1. **MCP 先行**：MCP 是所有后续优化的基础设施（Tool 标准化 + Context 资源化）
2. **RAG 第二**：RAG 直接解决 Token 浪费 + 知识碎片化两大痛点
3. **Workflow Engine 第三**：从"人工推动流程"到"引擎驱动流程"
4. **渐进式交付**：每月有可验收的产出，不一味堆功能
5. **数据驱动决策**：用 Token 消耗统计、Bug 匹配率、自动化率等指标指导下一步优化

---

## 附录

### A. 术语表

| 术语 | 说明 |
|------|------|
| Context | 项目/模块/页面级稳定事实文档 |
| Skill | 可复用的 AI 能力单元（Prompt 模板 + 规则 + 输入/输出） |
| Agent | Skill 集合 + 编排规则 + 角色定义 |
| Workflow | 多 Agent/多 Skill 的协作流程定义 |
| MCP | Model Context Protocol — LLM 工具/资源标准化协议 |
| RAG | Retrieval-Augmented Generation — 检索增强生成 |
| DAG | Directed Acyclic Graph — 有向无环图，Workflow 的数学表示 |
| SOP | Standard Operating Procedure — 标准作业流程（Phase 0→9） |

### B. 参考文件清单

| 文件 | 路径 |
|------|------|
| 项目入口 | `CLAUDE.md` |
| 事实源规则 | `governance/context/source-of-truth.md` |
| Skill 注册表 | `governance/skills/skill-registry.yaml` |
| Workflow 注册表 | `governance/workflows/workflow-registry.yaml` |
| Agent 全景 | `governance/agents/README.md` |
| 已知问题库 | `governance/context/known-issues.yaml` |
| Web 项目上下文 | `governance/context/projects/web-automation/PROJECT_CONTEXT.md` |
| 模块索引 | `governance/context/projects/web-automation/MODULE_INDEX.md` |
| 环境信息 | `governance/context/environments.yaml` |
| 迁移计划 | `governance/docs/operations/PHASE_PLAN.md` |

### C. 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2026-06-11 | 初始版本：8 部分完整架构审计 + 优化方案 |

---

> **下一步行动：** 建议按 §九 路线图从 **MCP 接入（W2）** 和 **CURRENT_TASK 标准化（W3）** 开始执行。是否批准进入 MCP Server 原型开发阶段？
