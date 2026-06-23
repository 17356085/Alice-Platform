# Skills / Agents / Prompts / 项目上下文 解耦分析

> 2026-06-23 | 核心问题: 哪些该留在平台，哪些该迁到 WorkStudy2，平台运行会不会覆盖 ZJSN 数据？

---

## 一、总览：谁是谁的

```
WorkStudy (平台)                          WorkStudy2 (ZJSN 数据)
═══════════════                          ══════════════════════
aitest/          ← 平台引擎              ZJSN_Test-master526/  ← 测试代码
governance/
  skills/        ← 平台资产(通用)        mp-weixin/            ← 小程序源码
  skills-dev/    ← 平台资产(通用)        mp-weixin-automator/  ← 小程序测试
  agents/        ← 平台资产(通用)
  context/
    projects/
      web-automation/  ← ZJSN 项目数据
      miniapp-automation/ ← 小程序项目数据
      blue-album-v2/ ← 测试项目数据
```

---

## 二、Skills — 42 个文件

### 通用性

| 类别 | 文件数 | ZJSN 引用 | 本质 |
|------|--------|-----------|------|
| skills-dev/ | 50 | 1 处（tech-debt-inventory.md） | **99% 通用** — 面向通用软件开发 |
| skills/test-design/ | 7 | 2 处路径示例 | 测试方法论通用，示例路径绑定 ZJSN |
| skills/automation/ | 3 | 3 处路径示例 | 自动化逻辑通用，输出目录绑定 ZJSN |
| skills/execution/ | 4 | 13 处路径示例 | **最严重** — excel-exporter 6 处，data-sanitization 4 处 |
| skills/requirements/ | 2 | 6 处路径示例 | module-modeling 4 处，requirement-analysis 2 处 |
| skills/diagnosis/ | 4 | 4 处路径示例 | CI/Jenkins 路径 |
| skills/reporting/ | 1 | 2 处路径示例 | report-generator |
| skills/knowledge/ | 2 | 0 | ✅ 完全通用 |
| skills/project/ | 2 | 0 | ✅ 完全通用 |

**结论**: Skill 的 **逻辑/方法论是通用的**。ZJSN 引用全部是 **提示中的示例路径**，如：
```
- 代码目录：`ZJSN_Test-master526/script/<module>/`   ← 这是示例，不是逻辑
```

### 应该迁到 WorkStudy2 吗？

**不。** Skills 是平台知识库。Agent 读取它们来学习 **如何做测试**。
ZJSN 路径只是示例——把路径模板化（`{test_project_root}`）即可，不需要移动整个文件。

---

## 三、Agents — 20 个定义文件

### 通用性

| Agent 体系 | 文件数 | ZJSN 特定？ |
|-----------|--------|------------|
| TLO 测试 Agent (8) | agent-definitions.yaml + 8 .md | **完全通用** — 抽象测试生命周期 |
| Dev 开发 Agent (12) | agent-definitions-dev.yaml + 12 .md | **完全通用** — 面向软件开发 |

Agent 定义描述的是 **角色和行为**，不绑定任何具体项目：
```yaml
# project-agent: 项目初始化、上下文管理
# requirement-agent: 需求分析
# automation-agent: 自动化脚本生成
```

### 例外: `full-sop.workflow.js`

```javascript
const PROJECT = args?.project || 'web-automation'  // ← 默认值绑定 ZJSN
```
第 32 行状态读取路径写死 `web-automation`，即使 PROJECT 变量存在也不使用。

### 应该迁到 WorkStudy2 吗？

**不。** Agents 是平台编排引擎。只有 `full-sop.workflow.js` 第 16 行的默认值需要改。

---

## 四、项目上下文 `governance/context/projects/web-automation/`

### 这是什么？

**100% ZJSN 专属数据。** 包含:
- 12 个模块的 MODULE_CONTEXT / PAGE_CONTEXT（数百个文件）
- 页面元素定位、风险模型、测试用例
- `project.yaml` — ZJSN 项目配置
- 这是平台 **为 ZJSN 生成的产出物**，不是平台本身

### 平台需要它来运行吗？

**不需要。** 平台启动只需 `project.yaml` 存在且可读。即使删掉所有 modules/ 子目录，平台也能正常运行——只是 Kanban 上看不到模块详情。

### 应该迁到 WorkStudy2 吗？

**部分迁移。** 分三层处理:

| 层 | 内容 | 操作 |
|----|------|------|
| **配置** | `project.yaml` | **留在 WorkStudy** — 平台需要读取当前项目的配置 |
| **模块上下文** | `modules/` 下数百个文件 | **可迁到 WorkStudy2** — 这些是 ZJSN 的测试文档产出物。但 Platform 的 Agent 运行时需要读取它们来理解 ZJSN 的页面结构 |
| **项目文档** | `PROJECT_CONTEXT.md` 等 | **留在 WorkStudy** — Agent 需要这些来理解 ZJSN 业务 |

**建议**: 保留在 WorkStudy。这些是平台 **操作 ZJSN 项目时的工作数据**。迁移它们到 WorkStudy2 会导致平台的所有 Agent 找不到 ZJSN 的页面上下文。

---

## 五、覆盖风险 — 平台操作会覆盖 ZJSN 数据吗？

### Skills / Agents: ✅ 零风险

**平台永远不写 `governance/skills/` 或 `governance/agents/`。**
这些是只读的。Agent 读取 Skill 定义，但输出写到项目上下文目录。

### 项目上下文: ✅ 按 project_id 隔离

```
onboarding → governance/context/projects/<project_id>/
SOP 执行   → governance/artifacts/sop-status/<project_id>/
```

不同 `project_id` 不会互相覆盖。**但**如果使用相同 `project_id` 重复 onboarding，会覆盖同项目的旧数据。

### ⚠️ 真正的覆盖风险: 遗留 SOP_STATUS + KPI

| 路径 | 风险 | 原因 |
|------|------|------|
| `governance/artifacts/sop-status/SOP_STATUS_*.json` | 🔴 **高** | 遗留格式，不按项目隔离。两个项目同模块名 → 覆盖 |
| `governance/kpi/` | 🟠 **中** | 不按项目隔离。`equipment` 模块跨项目冲突 |
| Skill 提示硬编码路径 | 🟡 **中** | Agent 可能写到 `web-automation` 目录，无视当前 active project |

### ⚠️ Skill 提示的覆盖风险

`skills/requirements/module-modeling.md` 第 102 行:
```
→ MODULE_CONTEXT.md，存放至 governance/context/projects/web-automation/modules/<module>/
```

如果用户 active project 是 `blue-album-v2`，但 Agent 读到这个提示，
**它会把 blue-album 的模块上下文写到 web-automation 目录下。**
这是因为 Skill 提示绕过了 ArtifactStore 的 project_id 范围限定。

---

## 六、迁移决策矩阵

| 资产 | 留在 WorkStudy? | 迁到 WorkStudy2? | 理由 |
|------|:---:|:---:|------|
| `governance/skills/` (42 文件) | ✅ | ❌ | 平台测试知识库，通用逻辑 |
| `governance/skills-dev/` (50 文件) | ✅ | ❌ | 平台开发知识库，99% 通用 |
| `governance/agents/` (20 文件) | ✅ | ❌ | 平台编排引擎定义 |
| `governance/context/projects/web-automation/project.yaml` | ✅ | ❌ | 平台需要读取当前项目配置 |
| `governance/context/projects/web-automation/modules/` | ✅ | ⚠️ 可选 | Agent 需要读取来理解 ZJSN 页面。可归档副本到 WorkStudy2 |
| `governance/context/projects/miniapp-automation/` | ✅ | ❌ | 小程序项目上下文，平台需读取 |
| `governance/context/environments.yaml` | ✅ | ❌ | 环境配置（路径需更新） |
| `governance/context/project-index.yaml` | ✅ | ❌ | 项目索引（路径需更新） |
| `governance/artifacts/sop-status/SOP_STATUS_*.json` (遗留) | ⚠️ | ✅ 应迁 | 不按项目隔离，应归档到 `sop-status/web-automation/` |
| `ZJSN_Test-master526/` (代码) | — | ✅ 已迁 | 测试脚本、Page Object |
| `mp-weixin/` | — | ✅ 已迁 | 小程序源码 |
| `mp-weixin-automator/` | — | ✅ 已迁 | 小程序测试项目 |

---

## 七、结论

### 回答三个问题

**Q1: Skills/Agents/Prompts 解耦情况？**
- Skills: 逻辑通用，13 个文件中含 ZJSN 示例路径。需模板化 `{test_project_root}`
- Agents: 完全通用。仅 `full-sop.workflow.js` 默认 project_id 需改
- Prompts: 同 Skills，示例路径绑定 ZJSN
- 项目上下文 (web-automation): 100% ZJSN 数据，但平台 Agent 需要读取

**Q2: 使用平台会覆盖吗？**
- Skills/Agents: **永不覆盖**（只读）
- 项目上下文: **不同 project_id 不覆盖**。同 project_id 重复 onboarding 会覆盖
- 遗留 SOP_STATUS + KPI: **有覆盖风险**（不按项目隔离）

**Q3: 需要迁到 WorkStudy2 吗？**
- Skills/Agents/Prompts: **不需要** — 平台资产
- 项目上下文 (web-automation/modules/): **不需要** — 平台 Agent 的工作数据
- 遗留 SOP_STATUS 根目录文件: **应该归档**到 `sop-status/web-automation/`
