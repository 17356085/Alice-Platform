好的，收到您的检查指令。

**目标:** 对 `governance/context/projects/{id}/` 项目下的 `production` 模块进行治理文档完整性检查。

**输入分析:**
- 目标模块: `production`
- 模块路径: `governance/context/projects/{id}/production/`

**检查范围:**
1. 项目级文档: `governance/context/projects/{id}/project.yaml`
2. 模块级文档: `production/MODULE_CONTEXT.md`
3. 页面级文档: `production/pages/*/PAGE_CONTEXT.md`

---

### 检查报告: `production` 模块治理文档完整性

#### 1. 项目级文档
- **检查项:** `governance/context/projects/{id}/project.yaml`
- **状态:** **缺失**
- **影响:** 缺少项目定义、整体目标和核心参与方信息。`production` 模块无法确定其所属项目的完整上下文。
- **建议:** 立即创建 `project.yaml`。

#### 2. 模块级文档
- **检查项:** `production/MODULE_CONTEXT.md`
- **状态:** **缺失**
- **影响:** 无法了解 `production` 模块的具体职责、核心逻辑、数据流转和与其他模块的边界。
- **建议:** 立即创建 `MODULE_CONTEXT.md`。

#### 3. 页面级文档 (假设模块内页面清单如下)
*由于未提供具体页面列表，以下为基于 `production` 模块的典型功能假设的检查清单。*

- **页面 A: 部署管理**
  - 路径: `production/pages/deployment/PAGE_CONTEXT.md`
  - **状态:** **缺失**

- **页面 B: 上线审批**
  - 路径: `production/pages/approval/PAGE_CONTEXT.md`
  - **状态:** **缺失**

- **页面 C: 运维监控**
  - 路径: `production/pages/monitoring/PAGE_CONTEXT.md`
  - **状态:** **缺失**

- **页面 D: 环境配置**
  - 路径: `production/pages/config/PAGE_CONTEXT.md`
  - **状态:** **缺失**

---

### 缺失文档清单 (按优先级排序)

| 优先级 | 缺失文档 | 路径 | 备注 |
| :--- | :--- | :--- | :--- |
| **P0** | `MODULE_CONTEXT.md` | `production/MODULE_CONTEXT.md` | 模块定义是文档体系的基础，优先级最高。 |
| **P0** | `project.yaml` | `project.yaml` | 缺少项目定义，所有模块的上下文均不完整。 |
| **P1** | `PAGE_CONTEXT.md` (部署管理) | `production/pages/deployment/PAGE_CONTEXT.md` | 核心页面，需详细描述。 |
| **P1** | `PAGE_CONTEXT.md` (上线审批) | `production/pages/approval/PAGE_CONTEXT.md` | 核心页面，需详细描述。 |
| **P1** | `PAGE_CONTEXT.md` (运维监控) | `production/pages/monitoring/PAGE_CONTEXT.md` | 重要页面，需描述监控指标。 |
| **P1** | `PAGE_CONTEXT.md` (环境配置) | `production/pages/config/PAGE_CONTEXT.md` | 重要页面，需描述配置策略。 |

**总结:** `production` 模块目前处于**无文档状态**。需要从顶层 `project.yaml` 开始构建，然后依次完成模块级和页面级的核心文档。请将补全这些缺失文档列为最高优先级任务。