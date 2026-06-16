# 项目结构优化分析报告

> 生成日期：2026-06-11 | 分析范围：WorkStudy 全项目 | 目标演进：Prompt → Workflow → Skill → Agent

---

# 第一部分：项目结构分析

## 当前结构全景

```
WorkStudy/                                    ← 工作区根目录
├── governance/                               ← AI 治理骨架（新建，0.1 版本）
│   ├── README.md                             ← 治理层总入口
│   ├── context/                              ← 事实源管理
│   │   ├── project-index.yaml                ← 项目索引（2 个项目）
│   │   ├── source-of-truth.md                ← 事实源规则
│   │   ├── README.md                         ← SOP Phase 映射 + 文档归属规则
│   │   └── projects/
│   │       ├── web-automation/               ← Web 项目上下文树
│   │       │   ├── PROJECT_CONTEXT.md
│   │       │   ├── MODULE_INDEX.md
│   │       │   ├── modules/
│   │       │   │   ├── equipment/            ← 设备管理（4 页面已映射）
│   │       │   │   ├── system-user/          ← 用户管理（2 页面已映射）
│   │       │   │   ├── system-role/          ← 角色管理（1 页面已映射）
│   │       │   │   └── system-management/    ← 系统管理（1 页面已映射）
│   │       │   └── summaries/
│   │       └── miniapp-automation/           ← 小程序项目（骨架，无模块）
│   ├── skills/                               ← 20 个 Skill 定义 + 注册表
│   ├── workflows/                            ← 8 个 Workflow 定义 + 注册表
│   ├── templates/                            ← 10 个文档模板
│   ├── docs/                                 ← 治理文档（迁移计划、命名规范、阶段计划）
│   └── artifacts/                            ← 过程产物存放区
│
├── ZJSN_Test-master526/                      ← Web 自动化测试代码（主力工程）
│   ├── base/              (7 .py)            ← 基础层：BasePage、BrowserDriver、ElementPlusHelper
│   ├── page/              (25 .py)           ← Page Object 层：7 个子模块
│   ├── script/            (60+ .py)          ← 测试脚本层
│   ├── config/            (5 .py)            ← 环境配置
│   ├── data/              (1 .py)            ← 测试数据
│   ├── conftest.py                           ← 根级 fixture
│   └── tools/             (40+ .py)          ← debug/inspect/fix/report/seed 工具
│
├── TestIntern_library/                       ← 文档/知识库（旧体系）
│   ├── 01-学习笔记/        (README + 4 方向)  ← 学习材料
│   ├── 02-项目文档/                           ← 核心知识资产
│   │   ├── AI辅助测试开发_标准作业流程（SOP）.md
│   │   ├── AUTOMATION_ARCHITECTURE.md
│   │   ├── PROJECT_KNOWLEDGE.md
│   │   ├── REFACTOR_PLAN.md
│   │   ├── 测试进度追踪.md
│   │   ├── _templates/     (4 模板)
│   │   ├── contexts/       (模块级上下文，旧体系)
│   │   ├── testcases/      (5 份测试用例)
│   │   └── scripts/        (2 个工具脚本)
│   ├── 03-工作日志/        (日报/周报/问题记录)
│   ├── 04-测试报告/        (执行报告/总结/缺陷)
│   └── 05-资源与参考/
│       └── AI提示词库.md   ← 27 个 Prompt 的核心文件
│
├── mp-weixin-automator/                      ← 小程序自动化（Node.js）
│   └── src/ (pages/flows/roles/utils/config)
│
├── mp-weixin/                                ← 微信小程序源码
│
└── docs/                                     ← 零散文档（小程序操作手册）
```

---

## 1.1 当前结构优点

### ✅ 治理层与代码层分离
`governance/` 作为一层薄治理骨架，不侵入 `ZJSN_Test-master526/` 和 `TestIntern_library/`，做到了"协作层先行，代码层后移"。新 AI 进入时可以先读 governance 再深入工程。

### ✅ SOP Phase 模型成熟
从 Phase 0（项目初始化）到 Phase 9（知识沉淀）的 10 阶段模型完整且可操作，每个 Phase 都有明确的输入、输出、产物位置。这是全项目最珍贵的结构资产。

### ✅ 文档-模板-Skill-Workflow 四层映射完整
`context/README.md` 中的 SOP Phase 映射表把 Phase、产出文档、存放位置、模板一一对应，这是 AI 长期协作的"骨架地图"。

### ✅ Skill 注册表轻量且可扩展
`skill-registry.yaml` 按 category 分组（governance/qa-design/automation/qa-debug/ci），每个 Skill 绑定 Workflow，形成了能力矩阵。

### ✅ 事实源规则明确
`source-of-truth.md` 定义了"同一类事实只能有一个主维护位置"，禁止跨文件重复。

### ✅ 渐进式迁移策略
`PHASE_PLAN.md` 分 1天/1周/1月 三个阶段，`MIGRATION_MAP.md` 逐页面追踪旧→新映射状态，不推倒重来。

### ✅ 自动化工程分层合理
`ZJSN_Test-master526/` 的分层（base → page → script + conftest）符合标准 Page Object 模式，BasePage 封装较完善。

---

## 1.2 当前结构问题

### ❌ 双 Context 体系并存（最大问题）
同一个模块的事实资产同时存在于两处：
- **旧体系**：`TestIntern_library/02-项目文档/contexts/equipment/`
- **新体系**：`governance/context/projects/web-automation/modules/equipment/`

虽然 `MIGRATION_MAP.md` 追踪了映射状态，但两套文件谁才是"source of truth"对 AI 而言是歧义的。部分旧文件已映射，部分未映射，新旧内容仍在各自演化，迟早出现分叉。

### ❌ AI提示词库.md 是巨型单体
一个 1347 行的文件承载了全部 27 个 Prompt（从 Phase 0 到 Phase 9 + 8 个跨场景 Prompt）。每个 Prompt 包含"前置输入 + 提示词 + 预期产出"，形成了"Prompt 中的 Prompt"。当需要修改某一个 Phase 的 Prompt 时，需要操作这个巨型文件。

### ❌ Skill 定义停留在骨架层
20 个 Skill 文件绝大多数只有 20-40 行的结构定义（目标/输入/输出/规则/依赖/边界），缺乏：
- 实际 prompt 模板
- 检查清单
- 示例输入输出
- 失败边界的处理逻辑

AI 读了 Skill 文件后只知道"做什么"，不知道该"怎么做"。

### ❌ Workflow 定义缺少阶段性操作指引
8 个 Workflow 定义了阶段和产物，但缺少：
- 每个阶段的具体 prompt
- 阶段间如何衔接（一个阶段的输出如何变成下一个阶段的输入）
- 失败/异常的降级策略

### ❌ 模板过于骨架化
`templates/page-context.template.md` 只有 38 行的字段名骨架，缺乏示例填充值。AI 容易产生格式漂移——同一个模板，不同会话产出风格迥异。

### ❌ 旧 contexts/ 目录缺少一致性
- `equipment/pages/key-param/` 缺少 `PAGE_CONTEXT.md`（治理层补位）
- `system-role/` 页面层级不规范（`ROLE_CONTEXT.md` 未按 page 拆解）
- `system-management/MODULE_CONTEXT.md` 是汇总层，包含多个子模块（用户管理/角色管理已迁出，其余未迁）
- 大量模块（储罐管理、DCS数据、化验室取样、人员管理、生产管理、销仓管理）只有旧体系目录，治理层无映射

### ❌ 工具脚本分散且命名混乱
`ZJSN_Test-master526/tools/` 下有 40+ 个 `.py` 文件：
- `debug/` 有 10+ 个，命名模式 `debug_*.py`
- `inspect/` 有 15+ 个，命名模式 `inspect_*.py`
- 许多是一轮会话用完即弃的一次性脚本，如 `inspect_role_perm_v2.py` → `inspect_role_perm_v3.py` → `inspect_role_perm_final.py`

这些本质上是 artifacts，却混在代码工程中。

### ❌ governance 与旧模板库重复建设
`governance/templates/` 有 10 个模板，`TestIntern_library/02-项目文档/_templates/` 有 4 个模板（`BUG_ANALYSIS_template.md`、`MODULE_CONTEXT_template.md`、`PAGE_CONTEXT_template.md`、`TEST_DESIGN_template.md`）。后者是前者的一个子集，命名风格也不统一。

---

## 1.3 哪些内容耦合过高

| 耦合点 | 当前状态 | 风险 |
|--------|----------|------|
| AI提示词库.md ↔ SOP | 全部 Phase Prompt 在一个文件 | 修改任一 Phase 都需操作同一文件 |
| 旧 contexts ↔ 新 context/projects | 双份并存，渐进映射 | 事实源歧义，AI 不确定读哪个 |
| Skill ↔ Prompt 库 | Skill 只做索引，Prompt 在旧文件 | Skill 调用时需跨文件查找 |
| PAGE_ELEMENT_POSITION ↔ TECH_ANALYSIS | 两个文件定位器职责重叠 | 更新定位器需双写 |
| tools/ ↔ artifacts/ | 一次性工具脚本留在代码工程 | 代码仓库被 artifacts 污染 |
| MODULE_CONTEXT ↔ MODULE_INDEX | 模块清单在两处维护 | 模块变更时需双写 |

---

## 1.4 哪些文件未来会成为维护瓶颈

| 文件 | 当前规模 | 瓶颈原因 |
|------|----------|----------|
| `AI提示词库.md` | 1347 行，27 个 Prompt | 单体膨胀，缺少模块化，每次 Prompt 调优需编辑巨型文件 |
| `MIGRATION_MAP.md` | 50 行 | 映射表持续增长，旧→新映射逐个手动维护 |
| `context/README.md` | 83 行 | SOP Phase 映射表是硬编码，新增 Phase 需修改表结构 |
| `ZJSN_Test-master526/tools/` | 40+ .py | 每次调试生成新脚本，无自动清理，持续膨胀 |
| `context/project-index.yaml` | 21 行 | 模块清单硬编码，新增模块需手动维护 |
| `TestIntern_library/02-项目文档/测试进度追踪.md` | 未知 | 跨会话手动更新，容易遗漏 |

---

## 1.5 哪些 Prompt 存在重复建设

| Prompt 对 | 重复内容 | 建议 |
|-----------|----------|------|
| P1-02（基于HTML分析定位器）↔ P3-01（Element Plus组件识别与定位器设计） | 定位器设计逻辑高度重叠 | 合并为 1 个 tech-analysis Prompt |
| P4-04（代码审查）↔ S-03（代码审查测试脚本） | 审查维度几乎相同 | P4-04 做生成后自查，S-03 做独立审查，保留但标注差异 |
| P2-01（页面级测试设计）↔ P2.5-01（生成详细测试用例表） | 测试场景与用例有 60% 内容重复 | P2.5-01 应只做展开，不重述场景 |
| S-01（上下文恢复）↔ S-02（上下文同步） | 共享上下文加载/存档逻辑 | 提取为 1 个 context-sync Skill 的双向操作 |

---

# 第二部分：AI 可接管性分析

## 2.1 AI 接管难点

| 难点 | 严重程度 | 说明 |
|------|----------|------|
| 双 Context 体系选择 | 🔴 高 | 新 AI 进入后，读 `source-of-truth.md` 得知旧体系是主资产，但 `governance/context/` 又是推荐写入位置——写哪边？ |
| Prompt 散落 | 🔴 高 | Skill 文件只做了指向 `AI提示词库.md` 的索引，但 Skill 自身不含可执行 Prompt。AI 调用 Skill 时需要跳转到旧文件。 |
| 旧资产命名不统一 | 🟡 中 | `ROLE_CONTEXT.md`（旧）vs `PAGE_CONTEXT.md`（新）vs `ANALYSIS.md`（混合），同一语义不同命名 |
| 工具脚本爆炸 | 🟡 中 | 40+ 临时脚本无使用说明，新 AI 无法判断哪些可复用、哪些是一次性的 |
| 模块迁移状态不透明 | 🟡 中 | 哪些模块是"已完整迁移"、"仅骨架"、"未迁移"，需逐页面追溯 MIGRATION_MAP |
| 小程序项目几乎空白 | 🟡 中 | `miniapp-automation/` 只有 3 个文件，模块清单为空，实际代码在 `mp-weixin-automator/` |

---

## 2.2 缺失上下文

### 需要补充的关键信息

1. **项目级 CLAUDE.md 缺失** — 没有项目级 AI 入口文档。新 AI 不知道该先读什么。建议创建 `CLAUDE.md` 作为 AI 启动的第一份文档。

2. **模块迁移状态矩阵缺失** — `MIGRATION_MAP.md` 按页面粒度追踪，但缺少"迁移完成度百分比"和"AI 可安全使用的阈值"（如：≥ 80% 完成的模块 AI 可以自主写入）。

3. **环境信息散落** — 测试 URL (`http://8.136.215.171:8081/`)、测试账号、Jenkins 地址分散在 Prompt 占位符和 `.env` 中，缺少统一的环境上下文文件。

4. **代码与上下文的关联缺失** — `governance/context/projects/web-automation/modules/equipment/pages/key-param/PAGE_ELEMENT_POSITION.md` 没有指向 `page/equipment_page/KeyParamPage.py` 的链接。AI 无法从上下文直接跳转到对应代码。

5. **测试数据生命周期说明缺失** — `data/alarm_config_data.py` 等测试数据文件没有说明谁负责维护、何时失效、如何清理。

6. **已知失败模式缺失** — 没有`已知问题.md` 或 flaky test 清单。新 AI 接手自动化失败时只能从零诊断。

---

## 2.3 哪些信息重复

| 重复内容 | 位置 1 | 位置 2 | 影响 |
|----------|--------|--------|------|
| 模块清单 | `MODULE_INDEX.md` | `project-index.yaml` | 模块变更需双写 |
| 模板定义 | `governance/templates/` | `TestIntern_library/02-项目文档/_templates/` | 两个模板库，AI 选哪个？ |
| 页面定位器 | `PAGE_ELEMENT_POSITION.md` | `TECH_ANALYSIS.md` § 定位器设计表 | 定位器更新时需同步 |
| 测试用例 | `governance/context/.../TEST_CASES.md` | `TestIntern_library/.../testcases/` | 两份用例文件 |
| Phase 映射 | `context/README.md` | `sop-summary.md` | 同一 Phase 结构两份描述 |
| 自动化架构 | `AUTOMATION_ARCHITECTURE.md`（独立文件） | `PROJECT_CONTEXT.md` 不维护架构 | 架构信息散落 |

---

## 2.4 哪些上下文应该固化

| 上下文 | 当前状态 | 建议固化为 |
|--------|----------|------------|
| **CLAUDE.md** | ❌ 不存在 | 创建 `d:/Desktop/WorkStudy/CLAUDE.md`，作为 AI 第一入口，包含项目概述、目录导航、启动步骤、常用命令 |
| **环境上下文** | 散落在 Prompt 占位符 | `governance/context/environments.yaml` — 统一管理 URL/账号/CI地址 |
| **模块迁移状态** | 文字追踪在 MIGRATION_MAP | `governance/context/migration-status.yaml` — 结构化追踪 |
| **代码-上下文映射** | 散落 | 每个 PAGE_CONTEXT 加 `自动化代码:` 字段指向对应 PageObject/测试脚本 |
| **已知问题清单** | 无 | `governance/context/known-issues.yaml` — flaky test / 已知环境问题 |
| **Prompt→Skill 映射** | 已索引但不在 Skill 内 | 将每个 Skill 的核心 Prompt 内联到 Skill 文件中 |

---

# 第三部分：Prompt 工程分析

## 3.1 项目中共识别出 27 个 Prompt

来源：`TestIntern_library/05-资源与参考/AI提示词库.md`（1347 行）

### Phase 级 Prompt（19 个）
P0-01, P0.5-01, P0.5-02, P0.8-01, P1-01, P1-02, P1.5-01, P2-01, P2.5-01, P3-01, P3.5-01, P4-01, P4-02, P4-03, P4-04, P4.5-01, P5-01, P6-01, P7-01, P8-01, P9-01

### 跨场景 Prompt（8 个）
S-01 ~ S-08

---

## 3.2 保留 Prompt

大部分 Prompt 质量高、结构化好。建议保留（含小幅优化）：

| Prompt | 保留理由 | 优化建议 |
|--------|----------|----------|
| P0-01 项目初始化 | 一次性使用，但结构可作为模板 | 提取为 `skills/project-context-manager` 的实操 Prompt |
| P0.5-01 模块建模 | 高频使用，每个新模块一次 | ✅ 保留，与 `module-modeling` Skill 合并 |
| P1-01 基于截图分析页面 | 高频使用 | ✅ 保留，与 `page-analysis` Skill 合并 |
| P1.5-01 风险建模 | 每个页面一次，6 维度模板完善 | ✅ 保留 |
| P2-01 测试设计 | 高频使用 | ✅ 保留 |
| P2.5-01 测试用例表 | 高频使用 | ✅ 保留 |
| P3-01 技术分析 | 高频，与 P1-02 合并 | 合并后保留 |
| P3.5-01 自动化策略 | 高频使用 | ✅ 保留 |
| P4-01/P4-02/P4-03 代码生成 | 核心价值 Prompt | ✅ 保留，与 `code-generation` Skill 合并 |
| P4.5-01 Bug 分析 | 高频使用 | ✅ 保留 |
| S-05 Element Plus 疑难定位 | 高频专用场景 | ✅ 保留 |
| S-06 小程序测试 | 专用场景 | ✅ 保留 |

---

## 3.3 模板化 Prompt

以下 Prompt 适合提取为模板，用 `{{ }}` 占位符参数化：

| Prompt | 模板化方式 | 存放位置 |
|--------|------------|----------|
| P0.5-01 模块建模 | `templates/module-modeling.prompt.md` | `skills/module-modeling.md` 内联 |
| P1-01 页面分析 | `templates/page-analysis.prompt.md` | `skills/page-analysis.md` 内联 |
| P1.5-01 风险建模 | `templates/risk-modeling.prompt.md` | `skills/risk-modeling.md` 内联 |
| P2-01 测试设计 | `templates/test-design.prompt.md` | `skills/testcase-design.md` 内联 |
| P2.5-01 测试用例表 | `templates/test-cases.prompt.md` | `skills/testcase-design.md` 内联 |
| P3-01 技术分析 | `templates/tech-analysis.prompt.md` | `skills/tech-analysis.md` 内联 |
| P4-01 PageObject 生成 | `templates/code-generation.prompt.md` | `skills/code-generation.md` 内联 |
| P4.5-01 Bug 分析 | `templates/bug-analysis.prompt.md` | `skills/bug-analysis.md` 内联 |
| S-01 上下文恢复 | `templates/context-restore.prompt.md` | `skills/context-sync.md` 内联 |
| S-02 上下文同步 | `templates/context-sync.prompt.md` | `skills/context-sync.md` 内联 |

---

## 3.4 候选 Skill（从 Prompt 中提取）

以下 Prompt 已经从"纯 Prompt"演化出"Skill 特征"（有明确输入/输出/规则/边界/依赖），可以升级为独立 Skill：

| 当前 Prompt | 候选 Skill | 成熟度 | 动作 |
|-------------|------------|--------|------|
| P0-01 | `project-context-manager` | ✅ 已有 Skill | 将 Prompt 内联到 Skill 文件 |
| P0.5-01 | `module-modeling` | ✅ 已有 Skill | 同上 |
| P0.8-01 | `requirement-analysis` | ✅ 已有 Skill | 同上 |
| P1-01 + P1-02 | `page-analysis` | ✅ 已有 Skill | 合并两个 Prompt |
| P1.5-01 | `risk-modeling` | ✅ 已有 Skill | 同上 |
| P2-01 + P2.5-01 | `testcase-design` | ✅ 已有 Skill | 同上 |
| P3-01 | `tech-analysis` | ✅ 已有 Skill | 同上 |
| P3.5-01 | `auto-strategy` | ✅ 已有 Skill | 同上 |
| P4-01~04 | `code-generation` | ✅ 已有 Skill | 同上 |
| P4.5-01 | `bug-analysis` | ✅ 已有 Skill | 同上 |
| P5-01 | 可合并到 `bug-analysis` | 🟡 需评估 | 批量分析是单 Bug 分析的扩展 |
| P6-01 | `api-testing` | ✅ 已有 Skill | 同上 |
| P7-01 | `ci-pipeline-analysis` | ✅ 已有 Skill | 同上 |
| P8-01 | `test-summary` | ✅ 已有 Skill | 同上 |
| P9-01 | `knowledge-precipitation` | ✅ 已有 Skill | 同上 |
| S-01 + S-02 | `context-sync` | ✅ 已有 Skill | 同上 |
| S-04 | `test-data-generation` | ✅ 已有 Skill | 同上 |
| S-05 | `element-plus-locator` | ✅ 已有 Skill | 同上 |
| S-06 | `miniapp-testing` | ✅ 已有 Skill | 同上 |
| S-07 | `progress-report` | ✅ 已有 Skill | 同上 |
| S-08 | `completeness-check` | ✅ 已有 Skill | 同上 |

**结论：所有 Prompt 的 Skill 映射骨架已建立。当前工作不是"新建 Skill"，而是"将 Prompt 填充到 Skill 骨架中"。**

---

## 3.5 废弃建议

| Prompt | 动作 | 理由 |
|--------|------|------|
| P1-02（基于HTML源码分析页面元素定位） | 合并到 P3-01 | 与 TECH_ANALYSIS 定位器设计重叠，尾部内容可作为 P3-01 的一个子节 |
| P0.5-02（批量模块建模） | 降级为 `module-modeling` Skill 的可选参数 | 批量模式本质上是指定多个模块名调用 module-modeling |
| S-03（代码审查） | 删除或改为指向 Claude Code 内置 `code-review` | 已有系统内置能力 |

---

# 第四部分：Workflow 设计

## 4.1 标准 10 阶段 Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AI 辅助测试开发标准 Workflow                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Phase 0 ──→ Phase 0.5 ──→ Phase 0.8 ──→ Phase 1 ──→ Phase 1.5     │
│  (项目初始化)  (模块建模)   (需求分析)   (页面分析)   (风险建模)      │
│      │             │             │            │             │        │
│      ▼             ▼             ▼            ▼             ▼        │
│  PROJECT_       MODULE_       REQ_         PAGE_         RISK_       │
│  CONTEXT.md     CONTEXT.md    ANALYSIS.md  CONTEXT.md     MODEL.md   │
│                                                                      │
│  Phase 2 ──→ Phase 2.5 ──→ Phase 3 ──→ Phase 3.5 ──→ Phase 4       │
│  (测试设计)   (用例编写)    (技术分析)   (自动化策略)   (代码生成)    │
│      │             │             │            │             │        │
│      ▼             ▼             ▼            ▼             ▼        │
│  TEST_         TEST_         TECH_         AUTO_         PageObj     │
│  DESIGN.md     CASES.md      ANALYSIS.md   STRATEGY.md   test_*.py   │
│                                                                      │
│  Phase 4.5 ──→ Phase 8 ──→ Phase 9                                   │
│  (Bug分析)    (测试总结)   (知识沉淀)                                 │
│      │             │             │                                    │
│      ▼             ▼             ▼                                    │
│  BUG_          TEST_         知识库                                    │
│  ANALYSIS.md   SUMMARY.md    更新                                     │
│                                                                      │
│  ┌─── 横向支撑 Phase ───────────────────────────────────────┐        │
│  │ Phase 5 (失败分析) │ Phase 6 (接口测试) │ Phase 7 (CI)    │        │
│  │ 按需触发           │ 按需触发           │ 按需触发        │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
│  ┌─── 持续阶段 ────────────────────────────────────────────┐        │
│  │ Session Start (上下文恢复) ↔ Session End (上下文同步)    │        │
│  └─────────────────────────────────────────────────────────┘        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4.2 各 Phase 详细设计

### Phase 0 — 项目初始化

| 维度 | 内容 |
|------|------|
| **输入** | 项目目录、技术栈说明、测试账号、旧资产路径 |
| **处理** | 识别项目范围 → 建立模块清单 → 建立事实源映射 → 识别重复与缺失 |
| **输出** | `PROJECT_CONTEXT.md`、`project-index.yaml`、`MODULE_INDEX.md` |
| **产物** | 项目级上下文 + 模块骨架索引 |
| **依赖** | 无（项目启动入口） |
| **模型** | Opus（高复杂度、一次性） |
| **完成标准** | 新 AI 能在一轮会话内定位项目入口和模块树 |

### Phase 0.5 — 模块建模

| 维度 | 内容 |
|------|------|
| **输入** | `PROJECT_CONTEXT.md`、模块入口 URL、页面截图（如有） |
| **处理** | 边界确认 → 子页面清单 → 权限要求 → 模块级风险 → 自动化价值评估 |
| **输出** | `MODULE_CONTEXT.md` |
| **产物** | 模块级上下文文档 |
| **依赖** | Phase 0（PROJECT_CONTEXT 必须先存在） |
| **模型** | Sonnet |
| **完成标准** | 页面清单完整、状态明确、风险标注 P0/P1/P2 |

### Phase 0.8 — 需求分析（按需触发）

| 维度 | 内容 |
|------|------|
| **输入** | PRD/原型图/产品说明、`MODULE_CONTEXT.md`（如有） |
| **处理** | 需求理解 → 业务规则提取 → 测试范围界定 → 风险识别 → 策略建议 |
| **输出** | 需求分析文档 |
| **产物** | `context/projects/*/modules/*/REQUIREMENT_ANALYSIS.md` |
| **依赖** | Phase 0.5（推荐） |
| **模型** | Sonnet |
| **完成标准** | 业务规则完整提取，模糊点标注"待产品确认" |

### Phase 1 — 页面分析

| 维度 | 内容 |
|------|------|
| **输入** | 页面截图（1-3 张）或 HTML 源码、页面名称/URL、`MODULE_CONTEXT.md` |
| **处理** | 布局分析 → 搜索区 → 表格区 → 弹窗/对话框 → 页面状态 → 权限点 |
| **输出** | `PAGE_CONTEXT.md`、`PAGE_ELEMENT_POSITION.md`（初版） |
| **产物** | 页面级元素清单 + 初步定位器 |
| **依赖** | Phase 0.5（MODULE_CONTEXT 推荐） |
| **模型** | Sonnet |
| **完成标准** | 所有可见元素有 ID、类型、所属区域、定位策略 |

### Phase 1.5 — 风险建模

| 维度 | 内容 |
|------|------|
| **输入** | `PAGE_CONTEXT.md`、`MODULE_CONTEXT.md`、历史缺陷、权限矩阵 |
| **处理** | 6 维度扫描（业务/权限/数据/接口/UI-UX/性能）→ 等级标注 → 缓解措施 |
| **输出** | `RISK_MODEL.md` |
| **产物** | 页面级风险矩阵 |
| **依赖** | Phase 1（PAGE_CONTEXT 必须先存在） |
| **模型** | Sonnet |
| **完成标准** | P0 风险有缓解措施，高风险场景标注自动化覆盖缺口 |

### Phase 2 — 测试设计

| 维度 | 内容 |
|------|------|
| **输入** | `PAGE_CONTEXT.md`、`RISK_MODEL.md`、业务规则、需求文档 |
| **处理** | 场景设计（加载/搜索/CRUD/权限/异常）→ 优先级 → 手工/自动化判断 |
| **输出** | `TEST_DESIGN.md` |
| **产物** | 页面级测试设计方案 |
| **依赖** | Phase 1 + Phase 1.5 |
| **模型** | Sonnet |
| **完成标准** | 每个测试点有编号、场景、优先级、前置条件、步骤、预期结果 |

### Phase 2.5 — 测试用例编写

| 维度 | 内容 |
|------|------|
| **输入** | `TEST_DESIGN.md`、已有用例格式参考 |
| **处理** | 场景展开 → 编号分配 → 填充步骤/数据 → 标注自动化状态 |
| **输出** | `TEST_CASES.md` |
| **产物** | 可执行的详细测试用例表 |
| **依赖** | Phase 2 |
| **模型** | Haiku（结构化展开、模式化操作） |
| **完成标准** | P0 100% 覆盖，P1 ≥ 80% 覆盖，数据字段可执行 |

### Phase 3 — 技术分析

| 维度 | 内容 |
|------|------|
| **输入** | HTML 源码、PAGE_CONTEXT.md、已知技术栈信息 |
| **处理** | Element Plus 组件识别 → DOM 结构 → 定位器设计（A/B/C 三级）→ 等待策略 |
| **输出** | `TECH_ANALYSIS.md`（含定位器设计表） |
| **产物** | 技术实现分析 + 完整定位器设计 |
| **依赖** | Phase 1（PAGE_CONTEXT） |
| **模型** | Sonnet |
| **完成标准** | 每个元素有三级定位策略 + 稳定性评级 + 等待策略 |

### Phase 3.5 — 自动化策略

| 维度 | 内容 |
|------|------|
| **输入** | `TEST_CASES.md`、`TECH_ANALYSIS.md`、BasePage 能力清单 |
| **处理** | 覆盖矩阵 → PageObject 拆分 → 复用分析 → ROI 计算 |
| **输出** | `AUTO_STRATEGY.md` |
| **产物** | 自动化覆盖策略 + ROI 分析 |
| **依赖** | Phase 2.5 + Phase 3 |
| **模型** | Sonnet |
| **完成标准** | P0 用例全标注为自动化，PoC 拆分方案具名 |

### Phase 4 — 代码生成

| 维度 | 内容 |
|------|------|
| **输入** | `TECH_ANALYSIS.md`、`AUTO_STRATEGY.md`、BasePage.py、参考 conftest |
| **处理** | 逐个生成 Page Object → 生成 test_*.py → 生成 conftest.py |
| **输出** | PageObject 文件、测试脚本、conftest.py |
| **产物** | 可运行的自动化测试代码 |
| **依赖** | Phase 3 + Phase 3.5 |
| **模型** | Sonnet（代码生成） |
| **完成标准** | pytest 可执行通过，P0 用例全覆盖，无 time.sleep |

### Phase 4.5 — Bug 分析（按需触发）

| 维度 | 内容 |
|------|------|
| **输入** | 失败日志、截图、HTML、Console 日志、代码上下文 |
| **处理** | 现象 → 复现分析 → 根因定位（5 层排查）→ 责任归属 → 修复建议 → 回归影响 |
| **输出** | `BUG_ANALYSIS.md` |
| **产物** | 标准化 Bug 分析报告 |
| **依赖** | Phase 4（需有自动化代码上下文） |
| **模型** | Sonnet |
| **完成标准** | 根因明确或标注"待验证"，有回归范围 |

### Phase 5 — 批量失败分析（按需触发）

| 维度 | 内容 |
|------|------|
| **输入** | Allure 报告、pytest 执行摘要 |
| **处理** | 失败分类 → 模式识别 → 优先级排序 → 修复计划 |
| **输出** | 批量失败分析报告 |
| **产物** | `artifacts/` 下的分析报告 |
| **依赖** | Phase 4.5（每个失败可引用 Bug 分析模式） |
| **模型** | Sonnet |

### Phase 6 — 接口测试（按需触发）

| 维度 | 内容 |
|------|------|
| **输入** | API 文档/Network 抓包、PAGE_CONTEXT 中的接口依赖 |
| **处理** | 接口清单 → 参数边界 → Token 校验 → 权限校验 → 安全测试 → 异常测试 |
| **输出** | `API_TEST_DESIGN.md` |
| **产物** | 接口测试设计方案 |
| **依赖** | Phase 1（接口依赖信息） |
| **模型** | Sonnet |

### Phase 7 — CI 分析（按需触发）

| 维度 | 内容 |
|------|------|
| **输入** | Jenkinsfile、构建日志、测试报告 |
| **处理** | 失败原因定位 → 与上次成功差异分析 → 失败类型判断 → 修复建议 |
| **输出** | CI 分析报告 |
| **产物** | `artifacts/` 下的 CI 分析 |
| **依赖** | Jenkins 配置 |
| **模型** | Sonnet |

### Phase 8 — 测试总结

| 维度 | 内容 |
|------|------|
| **输入** | 多份执行报告、Bug 统计、自动化结果、遗留问题 |
| **处理** | 数据汇总 → 统计拆分 → Bug 分析 → 结论判断 → 下阶段建议 |
| **输出** | `TEST_SUMMARY.md` |
| **产物** | 测试周期总结报告 |
| **依赖** | Phase 4 + Phase 4.5 |
| **模型** | Haiku |
| **完成标准** | 测试结论明确（建议上线/有条件上线/不建议上线） |

### Phase 9 — 知识沉淀

| 维度 | 内容 |
|------|------|
| **输入** | 本轮全部产出、进度追踪、踩坑记录 |
| **处理** | 更新 `PROJECT_CONTEXT.md` → 更新进度追踪 → 更新 MODULE_CONTEXT 状态 → 沉淀 Bug/经验 |
| **输出** | 更新后的知识文件 |
| **产物** | 知识库增量更新 |
| **依赖** | Phase 8 |
| **模型** | Sonnet |
| **完成标准** | 高频 Bug 和踩坑经验已记录，进度追踪已更新 |

### Session Start / Session End（持续阶段）

| 维度 | Session Start | Session End |
|------|---------------|-------------|
| **输入** | 上次会话摘要、当前进度追踪 | 本次会话变更摘要 |
| **处理** | 加载上下文链 → 确认理解 → 建议入口 | 分流事实/产物 → 更新进度 → 生成摘要 |
| **输出** | 上下文理解摘要 + 建议入口 | 上下文更新 + 下次会话摘要 |
| **依赖** | Phase 产物链路 | 所有已执行 Phase |

---

# 第五部分：Skill 拆分设计

## 5.1 核心发现

当前 20 个 Skill 的**骨架已完整**，问题不在于"缺少哪些 Skill"，而在于"Skill 内容空洞"。每个 Skill 需要补充：**内联 Prompt模板、检查清单、示例、失败边界处理**。

以下按推荐优先级输出：

---

## Skill 1: project-context-manager

- **名称**：项目上下文管理
- **职责**：识别测试项目、建立模块索引、映射事实源、输出缺失上下文清单
- **输入**：项目结构、项目级上下文、旧 assets 路径
- **输出**：`project-index.yaml`、`MODULE_INDEX.md`、缺失清单
- **规则**：
  - 优先引用旧资产，不急于复制
  - 模块是治理核心单元
  - 项目级只保留稳定共性
- **依赖**：`context/source-of-truth.md`
- **触发 Workflow**：`project-takeover`
- **推荐目录**：`governance/skills/project-context-manager.md`（已存在，需填充 Prompt）

---

## Skill 2: module-modeling

- **名称**：模块建模
- **职责**：从项目上下文出发为指定模块建立完整的模块级上下文
- **输入**：`PROJECT_CONTEXT.md`、模块入口 URL、模块名称、截图（可选）
- **输出**：`MODULE_CONTEXT.md`
- **规则**：
  - 必须先有 PROJECT_CONTEXT
  - 每个模块独立输出
  - 页面状态统一标记 ✅/🔄/⏳
  - 风险必须标注 P0/P1/P2 + 缓解措施
- **依赖**：`templates/module-context.template.md`
- **触发 Workflow**：`module-onboarding`
- **推荐目录**：`governance/skills/module-modeling.md`（已存在，需填充 Prompt）

---

## Skill 3: page-analysis

- **名称**：页面分析
- **职责**：通过页面截图或 HTML 源码分析页面结构、元素清单和元素定位器
- **输入**：页面截图（1-3张）或 HTML 源码、页面名称/URL、所属模块、MODULE_CONTEXT
- **输出**：`PAGE_CONTEXT.md`、`PAGE_ELEMENT_POSITION.md`（初版）
- **规则**：
  - 元素清单用表格呈现（元素ID/描述/类型/区域/备注）
  - 定位器优先级 A > B > C
  - Element Plus 组件需识别具体类型
  - 异步等待场景标注 WebDriverWait 策略
- **依赖**：`templates/page-context.template.md`、`module-modeling`
- **触发 Workflow**：`module-onboarding`
- **推荐目录**：`governance/skills/page-analysis.md`（已存在，需填充 Prompt）

---

## Skill 4: risk-modeling

- **名称**：风险建模
- **职责**：从页面上下文出发识别 6 维度风险，输出页面级风险模型
- **输入**：`PAGE_CONTEXT.md`、`MODULE_CONTEXT.md`、历史缺陷、权限矩阵
- **输出**：`RISK_MODEL.md`
- **规则**：
  - 6 维度：业务/权限/数据/接口/UI-UX/性能
  - P0（阻塞上线）/P1（影响核心体验）/P2（边缘场景）
  - P0 必须给缓解措施
  - 关联已有自动化覆盖率，标注未覆盖的高风险场景
- **依赖**：`templates/risk-model.template.md`、`page-analysis`
- **触发 Workflow**：`module-onboarding`
- **推荐目录**：`governance/skills/risk-modeling.md`（已存在，需填充 Prompt）

---

## Skill 5: testcase-design

- **名称**：测试用例设计
- **职责**：从上下文和风险出发，输出高质量测试设计与测试用例草案
- **输入**：`MODULE_CONTEXT.md`、`PAGE_CONTEXT.md`、`RISK_MODEL.md`、需求说明、历史缺陷
- **输出**：`TEST_DESIGN.md`、`TEST_CASES.md`、自动化优先级建议
- **规则**：
  - 先场景后步骤
  - 先风险后覆盖
  - 区分手工/自动化/混合
  - 明确不建议自动化的场景
  - P0 100% 覆盖，P1 ≥ 80%
- **依赖**：`templates/test-design.template.md`、`templates/test-cases.template.md`
- **触发 Workflow**：`module-test-design`
- **推荐目录**：`governance/skills/testcase-design.md`（已存在，需填充 Prompt）

---

## Skill 6: tech-analysis

- **名称**：技术实现分析
- **职责**：从 HTML 源码和截图分析前端技术实现，设计定位器和等待策略
- **输入**：HTML 源码、截图、`PAGE_CONTEXT.md`、已知技术栈
- **输出**：`TECH_ANALYSIS.md`（含定位器设计表 + 等待策略）
- **规则**：
  - 先识别 Element Plus 组件类型
  - 定位器 A/B/C 三级递进
  - 每个定位器标注稳定性评级
  - 等待策略覆盖：页面加载/表格刷新/弹窗开关/loading 消失
- **依赖**：`templates/tech-analysis.template.md`、`page-analysis`
- **触发 Workflow**：`automation-implementation`
- **推荐目录**：`governance/skills/tech-analysis.md`（已存在，需填充 Prompt）

---

## Skill 7: auto-strategy

- **名称**：自动化策略
- **职责**：制定自动化覆盖策略、PageObject 拆分方案和 ROI 分析
- **输入**：`TEST_CASES.md`、`TECH_ANALYSIS.md`、BasePage 能力清单
- **输出**：`AUTO_STRATEGY.md`
- **规则**：
  - P0 必须自动化
  - 定位器不稳定的用例标注风险
  - 一次性操作不建议自动化
  - 必须给出 ROI 计算
- **依赖**：`templates/auto-strategy.template.md`、`tech-analysis`、`testcase-design`
- **触发 Workflow**：`automation-implementation`
- **推荐目录**：`governance/skills/auto-strategy.md`（已存在，需填充 Prompt）

---

## Skill 8: code-generation

- **名称**：自动化代码生成
- **职责**：基于技术分析和策略生成符合规范的 Page Object 和 pytest 测试脚本
- **输入**：`TECH_ANALYSIS.md`、`AUTO_STRATEGY.md`、BasePage.py、参考代码
- **输出**：PageObject .py、test_*.py、conftest.py
- **规则**：
  - 一次只生成一个文件
  - Page Object 继承 BasePage，Locator 声明为类属性元组
  - 操作方法不含 assert / time.sleep(≥0.5s) / return self 支持链式调用
  - 测试用 @allure 完整注解 + with allure.step()
  - 禁止在测试用例中直接使用 driver.find_element
- **依赖**：`tech-analysis`、`auto-strategy`
- **触发 Workflow**：`automation-implementation`
- **推荐目录**：`governance/skills/code-generation.md`（已存在，需填充 Prompt）

---

## Skill 9: bug-analysis

- **名称**：Bug 分析
- **职责**：将失败现象转化为标准化 Bug 分析结论
- **输入**：失败日志、截图、复现步骤、代码上下文、CI 结果
- **输出**：Bug 分析报告（现象/根因/修复/回归）、根因分类
- **规则**：
  - 区分现象、证据、根因、建议
  - 不能确认的标记"待验证"
  - 必须输出影响范围与回归范围
  - 5 层排查：定位器失效→等待不足→数据问题→环境问题→产品Bug
- **依赖**：`templates/bug-analysis.template.md`
- **触发 Workflow**：`automation-failure-closure`
- **推荐目录**：`governance/skills/bug-analysis.md`（已存在，需填充 Prompt）

---

## Skill 10: context-sync

- **名称**：上下文同步
- **职责**：会话开始恢复上下文 + 会话结束同步变更
- **输入**（Start）：上次会话摘要、进度追踪
- **输入**（End）：本次变更摘要
- **输出**（Start）：理解摘要 + 建议入口
- **输出**（End）：上下文更新建议 + 产物归档 + 下一步待办
- **规则**：
  - 稳定事实 → `context/`
  - 过程产物 → `artifacts/`
  - 迁移 → `MIGRATION_MAP.md`
- **依赖**：`project-context-manager`
- **触发 Workflow**：`session-sync`
- **推荐目录**：`governance/skills/context-sync.md`（已存在，需填充 Prompt）

---

## 补充 Skill（按需）

| Skill 名称 | 职责 | 优先级 | 状态 |
|-----------|------|--------|------|
| `requirement-analysis` | 需求分析（PRD→测试策略） | P1 | 已有骨架 |
| `api-testing` | 接口测试设计+脚本生成 | P1 | 已有骨架 |
| `element-plus-locator` | Element Plus 疑难定位 | P2 | 已有骨架 |
| `test-data-generation` | 测试数据生成 | P2 | 已有骨架 |
| `test-summary` | 测试周期总结报告 | P1 | 已有骨架 |
| `knowledge-precipitation` | 知识沉淀 | P2 | 已有骨架 |
| `progress-report` | 进度报告生成 | P2 | 已有骨架 |
| `ci-pipeline-analysis` | CI 流水线分析 | P2 | 已有骨架 |
| `miniapp-testing` | 小程序测试设计 | P2 | 已有骨架 |
| `completeness-check` | 文档完整性检查 | P3 | 已有骨架 |

---

# 第六部分：目标结构设计

## 6.1 推荐项目结构

```
WorkStudy/
│
├── CLAUDE.md                              ← ★ AI 第一入口（新建）
│
├── governance/                            ← AI 治理骨架（当前优先填充）
│   ├── README.md                          ← 治理总入口
│   │
│   ├── context/                           ← 📁 事实源（Stable Facts）
│   │   ├── README.md                      ←   事实源管理规则
│   │   ├── source-of-truth.md             ←   事实源分工与禁止事项
│   │   ├── project-index.yaml             ←   项目注册表
│   │   ├── environments.yaml              ← ★ 环境信息（新建：URL/账号/CI地址）
│   │   ├── known-issues.yaml              ← ★ 已知问题清单（新建）
│   │   ├── migration-status.yaml          ← ★ 迁移状态矩阵（新建，替代文字追踪）
│   │   └── projects/
│   │       ├── web-automation/
│   │       │   ├── PROJECT_CONTEXT.md
│   │       │   ├── MODULE_INDEX.md
│   │       │   ├── modules/               ←   每个模块一个目录
│   │       │   │   ├── equipment/
│   │       │   │   │   ├── MODULE_CONTEXT.md
│   │       │   │   │   └── pages/         ←   每个页面一个目录
│   │       │   │   │       ├── alarm-config/
│   │       │   │   │       ├── camera/
│   │       │   │   │       ├── key-param/
│   │       │   │   │       └── maintenance/
│   │       │   │   ├── system-user/
│   │       │   │   ├── system-role/
│   │       │   │   └── system-management/
│   │       │   └── summaries/
│   │       └── miniapp-automation/
│   │
│   ├── skills/                            ← 📁 可复用能力（Skills）
│   │   ├── README.md
│   │   ├── skill-registry.yaml            ←   能力注册表
│   │   ├── project-context-manager.md     ←   ★ 需填充内联 Prompt
│   │   ├── module-modeling.md
│   │   ├── page-analysis.md
│   │   ├── risk-modeling.md
│   │   ├── testcase-design.md
│   │   ├── tech-analysis.md
│   │   ├── auto-strategy.md
│   │   ├── code-generation.md
│   │   ├── bug-analysis.md
│   │   ├── context-sync.md
│   │   ├── requirement-analysis.md
│   │   ├── api-testing.md
│   │   ├── element-plus-locator.md
│   │   ├── test-data-generation.md
│   │   ├── test-summary.md
│   │   ├── knowledge-precipitation.md
│   │   ├── progress-report.md
│   │   ├── ci-pipeline-analysis.md
│   │   ├── miniapp-testing.md
│   │   └── completeness-check.md
│   │
│   ├── workflows/                         ← 📁 标准流程（Workflows）
│   │   ├── README.md
│   │   ├── workflow-registry.yaml
│   │   ├── project-takeover.md
│   │   ├── module-onboarding.md
│   │   ├── module-test-design.md
│   │   ├── automation-implementation.md
│   │   ├── automation-failure-closure.md
│   │   ├── test-cycle-closure.md
│   │   ├── session-sync.md
│   │   ├── api-test-design.md
│   │   └── sop-summary.md
│   │
│   ├── templates/                         ← 📁 文档模板（Templates）
│   │   ├── README.md
│   │   ├── module-context.template.md
│   │   ├── page-context.template.md
│   │   ├── risk-model.template.md
│   │   ├── test-design.template.md
│   │   ├── test-cases.template.md
│   │   ├── tech-analysis.template.md
│   │   ├── auto-strategy.template.md
│   │   ├── bug-analysis.template.md
│   │   ├── test-summary.template.md
│   │   └── session-sync.template.md
│   │
│   ├── docs/                              ← 📁 治理文档（Governance Docs）
│   │   ├── README.md
│   │   ├── MIGRATION_MAP.md
│   │   ├── PHASE_PLAN.md
│   │   └── NAMING_CONVENTIONS.md
│   │
│   └── artifacts/                         ← 📁 过程产物（Temporary）
│       ├── README.md
│       └── PROJECT_STRUCTURE_ANALYSIS_2026-06-11.md  ← 本报告
│
├── ZJSN_Test-master526/                   ← Web 自动化测试代码（不动）
│   ├── base/
│   ├── page/
│   ├── script/
│   ├── config/
│   ├── data/
│   ├── conftest.py
│   ├── run_all.py
│   ├── Jenkinsfile
│   └── tools/                             ← ⚠ 需清理：一次性脚本 → artifacts/
│
├── TestIntern_library/                    ← 文档库（旧体系，逐步收敛）
│   ├── 01-学习笔记/
│   ├── 02-项目文档/
│   │   ├── AI辅助测试开发_标准作业流程（SOP）.md
│   │   ├── AUTOMATION_ARCHITECTURE.md
│   │   ├── PROJECT_KNOWLEDGE.md
│   │   ├── 测试进度追踪.md
│   │   ├── contexts/                      ← ⚠ 双体系问题：逐步指向 governance
│   │   ├── testcases/
│   │   └── scripts/
│   ├── 03-工作日志/
│   ├── 04-测试报告/
│   └── 05-资源与参考/
│       └── AI提示词库.md                  ← ⚠ 需拆解：Prompt → Skill 文件
│
├── mp-weixin-automator/                   ← 小程序自动化项目
├── mp-weixin/                             ← 小程序源码
└── docs/                                  ← 项目外部文档
```

---

## 6.2 各目录职责说明

### `context/` — 事实源
**一句话**：稳定项目事实的唯一存放位置。

- `project-index.yaml`：所有测试项目的注册表
- `environments.yaml`：环境信息（URL、账号、CI 地址）
- `known-issues.yaml`：flaky test、已知环境问题
- `migration-status.yaml`：迁移完成度追踪
- `projects/*/PROJECT_CONTEXT.md`：项目级稳定共性
- `projects/*/MODULE_INDEX.md`：模块清单
- `projects/*/modules/*/MODULE_CONTEXT.md`：模块级事实
- `projects/*/modules/*/pages/*/*.md`：页面级事实（PAGE_CONTEXT, RISK_MODEL, TEST_DESIGN 等）

**输入**：AI 会话开始时逐级加载  
**输出**：会话结束后稳定事实回写  
**维护者**：AI + 人双重确认（P0 文档变更需人确认）

### `workflows/` — 流程规则
**一句话**：多步骤协作任务的标准流程定义。

- 每个 Workflow 定义：目标、适用对象、阶段、产物、依赖 Skill、完成标准
- Workflow 不包含具体 Prompt（Prompt 在对应 Skill 中）
- 绑定 `skill-registry.yaml` 形成能力矩阵

**输入**：任务触发条件满足  
**输出**：按阶段产出文档/代码  
**使用方式**：AI 根据用户需求选择对应 Workflow 执行

### `skills/` — 可复用能力
**一句话**：AI 可独立执行的原子能力单元。

- 每个 Skill 包含：目标、输入、输出、规则、依赖、边界、**内联 Prompt 模板**
- 通过 `skill-registry.yaml` 注册并绑定 Workflow
- Skill 是可被 `Claude Code`、`Cursor`、`Codex`、`DeepSeek`、`Gemini` 等不同 AI 调用的最小契约单元

**关键设计**：Skill 文件是"AI 指令契约"——一个 Skill 文件应包含足够的信息，让任何 AI 在只读该文件的情况下完成该能力。

### `templates/` — 文档模板
**一句话**：统一输出格式的标准模板。

- 模板定义文档的 **字段结构**（What），Skill 中的 Prompt 定义 **生成方法**（How）
- 模板服务于 `context/` 模块树 — 每个模板对应一个文档文件名
- 旧 `TestIntern_library/02-项目文档/_templates/` 应废弃并指向这里

### `artifacts/` — 过程产物
**一句话**：一次性分析、测试报告、临时调查记录。

- 不替代事实源
- 不长期维护
- 适合存放：会话分析输出、失败日志摘录、截图索引、阶段性分析报告

### `docs/` — 治理文档
**一句话**：治理层自身的规则说明、迁移计划、命名规范。

- 不是项目事实，不是过程产物
- 是"如何治理"的说明文档

---

## 6.3 跨 AI 工具兼容性设计

| 设计元素 | Claude Code | Cursor | Codex | DeepSeek | Gemini |
|----------|-------------|--------|-------|----------|--------|
| **入口文件** | `CLAUDE.md` 自动加载 | `.cursor/rules/` 目录 | 自定义 rules | 自定义 system prompt | 自定义 system prompt |
| **Skill 文件** | 直接读取 `.md` | 直接读取 `.md` | 需要 `.json` 格式 | 直接读取 `.md` | 直接读取 `.md` |
| **workflow-registry.yaml** | YAML 原生支持 | 需解析 | JSON 更友好 | YAML 原生支持 | 需适配 |
| **模板占位符** | `{{ variable }}` | `{{ variable }}` | `{{ variable }}` | `{{ variable }}` | `{{ variable }}` |
| **Context 加载** | 逐级 `.md` 文件链 | 逐级 `.md` 文件链 | 需自定义 loader | 逐级 `.md` 文件链 | 逐级 `.md` 文件链 |

**推荐策略**：
1. 主格式使用 Markdown（所有工具原生支持）
2. YAML 用于结构化注册表（大部分工具支持）
3. 如需跨工具深度集成，增加 `skills/*.json` 作为 YAML 的镜像

---

# 第七部分：迁移计划

## 核心原则

1. **不推倒重来** — 所有现有资产保留在原始位置
2. **先填充，后废弃** — 新位置内容就绪后，旧位置加 `DEPRECATED.md` 指向新位置
3. **先核心 Skill，后边缘 Skill** — 优先填充高频使用的 Skill（前 10 个）
4. **每次只改一层** — 一次迁移只涉及一个层级（Skill / Template / Context）

---

## 第一阶段（1 天）：AI 入口 + 核心 Skill 填充

> 目标：新 AI 进入项目能在 10 分钟内定位关键资产并开始工作。

### Step 1.1 — 创建 CLAUDE.md（30 分钟）

**文件**：`d:/Desktop/WorkStudy/CLAUDE.md`

```markdown
# 鞍集涂源管理系统 — 测试开发 AI 协作项目

## 项目概述
- 被测系统：鞍集涂源管理系统（Vue 3 + Element Plus Web 端 + 微信小程序端）
- 测试框架：Python + pytest + Selenium + Allure + Jenkins
- 治理层：governance/ — AI 协作骨架
- 代码工程：ZJSN_Test-master526/ — Web 自动化
- 文档库：TestIntern_library/ — 旧知识资产（逐步收敛）

## 快速启动
1. 阅读 governance/README.md — 了解治理层结构
2. 阅读 governance/context/source-of-truth.md — 了解事实源规则
3. 阅读 governance/context/projects/web-automation/PROJECT_CONTEXT.md — 了解 Web 项目
4. 阅读 governance/docs/PHASE_PLAN.md — 了解当前迁移状态

## 常用命令
- `pytest script/equipment/test_alarm_config.py -v --alluredir=allure-results`

## 当前迁移阶段
处于第2阶段（治理骨架已建立，核心 Skill 填充中）

## 环境信息
→ 见 governance/context/environments.yaml
```

### Step 1.2 — 创建 environments.yaml（15 分钟）

```yaml
version: 0.1
web:
  base_url: http://8.136.215.171:8081/
  test_account:
    admin: {username: admin, password: "***"}
    # 其他角色待补充
  ci:
    jenkins_url: (待补充)
    job_name: ZJSN_Test
miniapp:
  app_id: (待补充)
  test_account: (待补充)
```

### Step 1.3 — 填充前 5 个核心 Skill 的 Prompt（2 小时）

从 `AI提示词库.md` 中提取 Prompt 模板，内联到以下 Skill 文件：
- `skills/page-analysis.md` — 内联 P1-01 Prompt
- `skills/testcase-design.md` — 内联 P2-01 + P2.5-01 Prompt
- `skills/tech-analysis.md` — 内联 P3-01 Prompt（合并 P1-02）
- `skills/code-generation.md` — 内联 P4-01~04 Prompt
- `skills/bug-analysis.md` — 内联 P4.5-01 Prompt

每份 Skill 文件增加：
- `## Prompt 模板` 节（包含可复制使用的 Prompt）
- `## 检查清单` 节（完成标准 checklist）
- `## 示例` 节（一个简短输入→输出示例）

### Step 1.4 — 为旧 contexts/ 添加指针文件（15 分钟）

在 `TestIntern_library/02-项目文档/contexts/README.md` 顶部添加：

```markdown
> ⚠️ **本目录为旧体系**。新模块上下文请写入 `governance/context/projects/web-automation/modules/`。
> 迁移映射见 `governance/docs/MIGRATION_MAP.md`。
```

---

## 第二阶段（1 周）：模板增强 + 双体系收敛 + Workflow 实战

### Step 2.1 — 模板填充示例值（1 小时）

为每个 `templates/*.template.md` 在注释中增加 1-2 个示例填充值。例如：

```markdown
# PAGE_CONTEXT Template

## 基本信息
- 页面ID：alarm-config       ← 示例: 使用英文短横线，与路由一致
- 页面名称：设备报警配置       ← 示例: 从菜单/面包屑获取
...
```

目的：减少 AI 产出格式漂移。

### Step 2.2 — 填充剩余 5 个核心 Skill（2 小时）

- `skills/module-modeling.md` — 内联 P0.5-01 Prompt
- `skills/risk-modeling.md` — 内联 P1.5-01 Prompt
- `skills/auto-strategy.md` — 内联 P3.5-01 Prompt
- `skills/context-sync.md` — 内联 S-01 + S-02 Prompt
- `skills/requirement-analysis.md` — 内联 P0.8-01 Prompt

### Step 2.3 — 去重：删除旧 _templates/（30 分钟）

在 `TestIntern_library/02-项目文档/_templates/` 下添加 `DEPRECATED.md`：

```markdown
# 此目录已废弃

模板已统一迁移至 `governance/templates/`。
- MODULE_CONTEXT_template.md → governance/templates/module-context.template.md
- PAGE_CONTEXT_template.md → governance/templates/page-context.template.md
- TEST_DESIGN_template.md → governance/templates/test-design.template.md
- BUG_ANALYSIS_template.md → governance/templates/bug-analysis.template.md
```

### Step 2.4 — 双体系收敛：迁移状态结构化（1 小时）

创建 `governance/context/migration-status.yaml`：

```yaml
version: 0.1
modules:
  web-automation:
    equipment:
      percentage: 60
      pages:
        alarm-config: mapped
        camera: mapped
        key-param: skeleton
        maintenance: mapped
        sensor-manage: not_started
        unit-manage: not_started
    system-user:
      percentage: 80
      ...
    system-role:
      percentage: 50
      ...
    system-management:
      percentage: 30
      ...
    储罐管理: {percentage: 0, status: not_started}
    DCS数据: {percentage: 0, status: not_started}
    化验室取样: {percentage: 0, status: not_started}
    人员管理: {percentage: 0, status: not_started}
    生产管理: {percentage: 0, status: not_started}
    销仓管理: {percentage: 0, status: not_started}
  miniapp-automation:
    percentage: 5
```

### Step 2.5 — 实战 Workflow：走通 module-onboarding（2 小时）

以"储罐管理"模块为例，用 `workflows/module-onboarding.md` 完整走一遍：
1. 使用 `module-modeling` Skill 生成 MODULE_CONTEXT
2. 使用 `page-analysis` Skill 生成 PAGE_CONTEXT（如有截图）
3. 使用 `risk-modeling` Skill 生成 RISK_MODEL

记录过程中遇到的所有偏差和问题。

---

## 第三阶段（1 个月）：工具清理 + AI提示词库拆解 + 全量覆盖

### Step 3.1 — tools/ 清理（2 小时）

```bash
# 分类临时工具脚本
for f in ZJSN_Test-master526/tools/debug/*.py ZJSN_Test-master526/tools/inspect/*.py; do
    # 判断是否一次性 → 移入 artifacts/
    # 判断是否可复用 → 保留并添加注释说明
done
```

- 一次性 debug/inspect 脚本 → `governance/artifacts/tools-archive/`
- 稳定工具（`generate_excel.py` / `apply_fixes.py`）→ 保留在 `tools/`，加注释头说明用途
- 在 `tools/README.md` 中列出所有可复用工具

### Step 3.2 — AI提示词库.md 拆解（3 小时）

将 `TestIntern_library/05-资源与参考/AI提示词库.md` 中的 Prompt 逐一内联到对应 Skill 文件后：

1. 在原文件顶部添加状态标记（哪些已拆解、哪些待拆解）
2. 每个 Prompt 内联完成后，在原 Prompt 处添加 `→ 已迁移至 skills/xxx.md`
3. 保留原文件作为"历史参考"和"快速查找"手册，标注 `DEPRECATED`

### Step 3.3 — 补充边缘 Skill 的 Prompt（2 小时）

- `skills/api-testing.md`
- `skills/test-data-generation.md`
- `skills/test-summary.md`
- `skills/knowledge-precipitation.md`
- `skills/progress-report.md`
- `skills/ci-pipeline-analysis.md`
- `skills/element-plus-locator.md`
- `skills/miniapp-testing.md`
- `skills/completeness-check.md`

### Step 3.4 — 建立代码↔上下文双向链接（1 小时）

在每个 `PAGE_CONTEXT.md` 增加：

```markdown
## 自动化代码
- Page Object: `page/equipment_page/KeyParamPage.py`
- 测试脚本: `script/equipment/test_key_param.py`
- conftest: `script/equipment/conftest.py`
```

### Step 3.5 — 创建 known-issues.yaml（1 小时）

收集所有已知 flaky test 和环境问题。

### Step 3.6 — 小程序项目补骨（2 小时）

```
governance/context/projects/miniapp-automation/
├── PROJECT_CONTEXT.md        ← 从旧 PROJECT_WX_CONTEXT.md 提炼
├── MODULE_INDEX.md           ← 建立模块清单
├── modules/                  ← 至少建 1-2 个核心模块骨架
└── summaries/
```

---

## 迁移优先级矩阵

```
                    收益
                低          高
           ┌──────────┬──────────┐
      低   │ 边缘Skill │ 模板增强 │  ← 第三阶段
风         │ 工具清理 │          │
险         ├──────────┼──────────┤
      高   │   ❌     │ CLAUDE.md│  ← 第一阶段
           │ 避免的操作│ 核心Skill│
           └──────────┴──────────┘
                          ↑ 第二阶段：双体系收敛
```

---

## Token 成本估算

| 操作 | 当前 Token 消耗 | 优化后 | 节省 |
|------|----------------|--------|------|
| 新会话上下文恢复 | ~8000（需读 AI提示词库 片段 + context 文件） | ~3000（读 CLAUDE.md + Skill + PAGE_CONTEXT） | ~62% |
| 执行 page-analysis | ~5000（手动拼 Prompt + 上下文） | ~2000（Skill 内嵌 Prompt + 模板） | ~60% |
| 跨文件查找 Prompt | ~2000（搜索 AI提示词库） | ~200（读 Skill 文件） | ~90% |
| 模块入场全流程 | ~25000（零散操作） | ~12000（Workflow 引导） | ~52% |

---

# 总结

## 当前演进位置

```
Prompt工程 ✅ 已完成 ──→ Workflow工程 🟡 骨架就绪 ──→ Skill工程 🔴 需填充 ──→ Agent工程 ⏳ 未开始
```

## 最关键的三个动作（本周内）

1. **创建 CLAUDE.md** — 30 分钟，解决"新 AI 盲飞"问题
2. **填充前 5 个核心 Skill 的 Prompt** — 2 小时，解决"Skill 骨架无肉"问题
3. **创建 environments.yaml** — 15 分钟，解决"环境信息散落"问题

这三个动作做完，AI 接管成本降低 60%+。

## 最关键的三个决策

1. **Skill 文件必须内联 Prompt**（不能只做索引）— 这是从 "Workflow 工程" 进阶到 "Skill 工程" 的门槛
2. **双 Context 体系用"指针文件 + 渐进废弃"收敛**（不能删除旧文件）— 保护已有资产的同时消除歧义
3. **Prompt 库拆解为 Skill 附件**（不能继续维持单体文件）— 降低 Token 消耗 + 提升复用率

---

> 本分析报告生成于 2026-06-11，覆盖 WorkStudy 全项目 5 个主要区域、27 个 Prompt、20 个 Skill、8 个 Workflow、10 个模板。
>
> 后续建议每 2 周更新一次 `migration-status.yaml`，每 1 个月审计一次 Skill 使用频率。
