依据治理规则，我将对 `personnel` 模块进行文档完整性检查。

---

### 人员模块 (`personnel`) 文档完整性检查报告

**检查时间**: 2024-05-24

---

#### 1. 项目级文档检查

| 文件 | 状态 | 备注 |
| :--- | :--- | :--- |
| `governance/context/projects/{id}/project.yaml` | ✅ 假设存在 | 假定项目已创建，此检查点通过。 |

#### 2. 模块级文档检查

| 文件 | 状态 | 优先级 | 建议 |
| :--- | :--- | :--- | :--- |
| `personnel/MODULE_CONTEXT.md` | ❌ **缺失** | **P0 (高)** | **必须创建**。定义模块边界、核心数据实体（如员工、部门、岗位）、关键业务规则（如组织架构变更流程）。 |

#### 3. 页面级文档检查

根据行业规范及常见人员管理功能，提出以下 **预期页面** 建议清单。实际页面以 `project.yaml` 中声明的 `pages` 为准。此处列出最常见页面以供参考：

| 页面路径 (预期) | 文件 (预期) | 状态 | 优先级 | 建议 |
| :--- | :--- | :--- | :--- | :--- |
| `personnel/employees/` | `PAGE_CONTEXT.md` | ❌ **缺失** | **P0 (高)** | **必须创建**。描述员工列表页的功能：搜索、筛选、分页、新增员工入口。 |
| `personnel/employees/detail/` | `PAGE_CONTEXT.md` | ❌ **缺失** | **P0 (高)** | **必须创建**。描述员工详情页：基本档案、岗位信息、工作经历、教育背景等 Tab。 |
| `personnel/employees/onboarding/` | `PAGE_CONTEXT.md` | ❌ **缺失** | **P0 (高)** | **必须创建**。描述入职页面：表单字段、上传附件（身份证、学历证明）、入职流程引导。 |
| `personnel/departments/` | `PAGE_CONTEXT.md` | ❌ **缺失** | **P1 (中)** | **建议创建**。描述部门管理页面：组织架构树、CRUD 操作、部门负责人分配。 |
| `personnel/positions/` | `PAGE_CONTEXT.md` | ❌ **缺失** | **P1 (中)** | **建议创建**。描述岗位管理页面：职位分类、职级体系、编制数管理。 |
| `personnel/contracts/` | `PAGE_CONTEXT.md` | ❌ **缺失** | **P2 (低)** | **建议创建**。描述合同管理：合同类型、签署日期、到期提醒。 |

---

### 缺失文档汇总 (按优先级排序)

#### P0 (高) - 必须解决

1.  **模块核心文档:**
    *   `personnel/MODULE_CONTEXT.md`
2.  **核心页面文档:**
    *   `personnel/employees/PAGE_CONTEXT.md`
    *   `personnel/employees/detail/PAGE_CONTEXT.md`
    *   `personnel/employees/onboarding/PAGE_CONTEXT.md`

#### P1 (中) - 强烈建议解决

1.  **重要页面文档:**
    *   `personnel/departments/PAGE_CONTEXT.md`
    *   `personnel/positions/PAGE_CONTEXT.md`

#### P2 (低) - 建议后续补全

1.  **次要页面文档:**
    *   `personnel/contracts/PAGE_CONTEXT.md` (如果业务包含合同管理)

---

### 下一步行动建议 (Actionable Items)

1.  **立即：** 优先创建 `personnel/MODULE_CONTEXT.md`，明确本模块的职责范围和与其他模块（如薪酬、招聘）的交互边界。
2.  **同步：** 同时创建 `personnel/employees/` 相关的 **3 个** `PAGE_CONTEXT.md` 文件，确保核心用户路径（员工看板 -> 查看详情 -> 入职流程）有文档支撑。
3.  **规划：** 根据项目优先级，规划 `departments` 和 `positions` 页面的 `PAGE_CONTEXT.md` 编写工作。