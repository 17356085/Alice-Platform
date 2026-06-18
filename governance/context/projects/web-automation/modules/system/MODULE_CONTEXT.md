# MODULE_CONTEXT — system

> ℹ️ 本文为 system 模块（被测系统"系统管理"菜单组）的模块级上下文。详细页面分析已下沉至各页面目录。
> ⚠️ **结构纠正 (2026-06-15)**: system 是被测系统中的**模块**，system-management 只是其中一个页面。此前治理层错误地将 system-management 提升为模块级别，现予纠正。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 模块ID | system |
| 模块名称 | 系统管理（System Management） |
| 所属项目 | web-automation |
| 测试目录 | `ZJSN_Test-master526/script/system/` |
| PO 目录 | `ZJSN_Test-master526/page/system_page/` |
| 基准 URL | `https://aiwechatminidemo.cimc-digital.com/#/system/user` |
| 权限要求 | `system:*` 前缀权限点，核心页面需 admin / commonAdmin 角色 |
| 存量来源 | `TestIntern_library\02-项目文档\contexts\system-management\MODULE_CONTEXT.md` |
| 版本 | V2.0 (2026-06-15) — 结构纠正版 |

## 模块定位

系统管理是全平台的 **RBAC 权限管控中枢**和**基础配置中心**，覆盖 **12 个独立页面**（5 个工作流页面已独立为 [workflow](../workflow/MODULE_CONTEXT.md) 模块），共享同一测试目录 `script/system/` 和 PO 目录 `page/system_page/`。

## 子页面清单

| 序号 | 页面名称 | 路由 | 页面类型 | 测试用例 | Page Object | 治理状态 |
| :---: | --- | --- | --- | :---: | :---: | :---: |
| 1 | **用户管理** | `#/system/user` | 列表页 + 多弹窗 | ✅ 15条 | UserManagePage.py | ✅ pages/user-list/ + pages/user-form/ |
| 2 | **角色管理** | `#/system/role` | 列表页 + 多弹窗 | ✅ ~12条 | RoleManagePage.py | 🔀 独立模块 → [system-role](../system-role/MODULE_CONTEXT.md) |
| 3 | **菜单管理** | `#/system/menu` | 树形表格 | ✅ 18条 | MenuManagePage.py | ✅ pages/menu-management/ |
| 4 | **组织管理（部门）** | `#/system/dept` | 树形列表 + 弹窗 | ✅ 14条 | OrgManagePage.py | ⏳ 待独立建模 |
| 5 | **字典管理** | `#/system/dict` | 列表页 + 明细页 + 弹窗 | ✅ 部分 | DictManagePage.py | ⏳ 待独立建模 |
| 6 | **参数设置** | `#/system/config` | 列表页 + 弹窗 | ✅ 14条 | ParamsManagePage.py | ⏳ 待独立建模 |
| 7 | **通知管理** | `#/system/notice` | 列表页 + 弹窗 | ✅ 8条 | NoticeManagePage.py | ⏳ 待独立建模 |
| 8 | **定时任务** | `#/system/job` | 列表页 + 弹窗 | ✅ 部分 | TimedTaskPage.py | ⏳ 待独立建模 |
| 9 | **接口管理** | `#/system/api` | Swagger UI 嵌入页 | ✅ 4条 | ApiManagePage.py | ✅ pages/api-management/ |
| 10 | **系统监控** | `#/system/monitor` | 监控仪表盘 | ✅ 4条 | MonitorManagePage.py | ✅ pages/monitor-management/ |
| 11 | **登录日志** | `#/system/log/login-log` | 列表页（只读） | ✅ 9条 | LoginLogPage.py | ⏳ 待独立建模 |
| 12 | **操作日志** | `#/system/log/oper-log` | 列表页（只读） | ✅ 11条 | OperationLogPage.py | ⏳ 待独立建模 |
| 13 | **系统日志** | `#/system/log/system-log` | 列表页（只读） | ✅ 9条 | SystemLogPage.py | ⏳ 待独立建模 |

> 🔀 = 已拆分出独立模块（system-role、workflow），本文件仅保留交叉引用。
> 图例：✅ 已建模 | ⏳ 待建模 | ⚠️ 基本完成但有已知问题

## 独立模块交叉引用

| 独立模块 | 治理位置 | 拆分原因 |
|---------|---------|---------|
| **system-role** | [modules/system-role/](../system-role/MODULE_CONTEXT.md) | RBAC 特殊性：角色管理涉及多角色切换、权限分配、数据范围配置，测试复杂度远超普通 CRUD 页面，需独立模块级治理 |
| **workflow** | [modules/workflow/](../workflow/MODULE_CONTEXT.md) | 业务枢纽：工作流管理是跨模块审批引擎，被 warehouse/sales 依赖，不应埋在系统配置下。含 5 页面（审批链配置/待我审批/我已审批/我发起的/SAP推送日志） |
| **RBAC 测试方案** | [modules/system-role/RBAC_TEST_PLAN.md](../system-role/RBAC_TEST_PLAN.md) | 多角色切换的 10 个测试场景及自动化策略 |

### 多角色切换关联度

依据旧资产分析，各页面与 RBAC 多角色切换的关联度分类如下：

| 分类 | 页面 | 优先级 |
|:---:|------|:-----:|
| 🔴 **直接涉及** | 用户管理、角色管理 | P0 |
| 🟡 **间接关联** | 菜单管理 | P1 |
| ⚪ **不涉及** | 组织管理、字典管理、参数设置、通知管理、定时任务、接口管理、系统监控、登录日志、操作日志、系统日志 | P3 |

> 详细 RBAC 业务流程、数据流图、测试数据准备、执行顺序等见 [RBAC_TEST_PLAN.md](../system-role/RBAC_TEST_PLAN.md)

## 已建模页面（5/12）

| 页面 | 治理路径 | 文档资产 |
|------|---------|---------|
| user-list | [pages/user-list/](pages/user-list/) | PAGE_CONTEXT + ANALYSIS + RISK_MODEL + TEST_DESIGN + TEST_CASES + TECH_ANALYSIS + AUTO_STRATEGY + PAGE_ELEMENT_POSITION + PAGE_INTERFACE |
| user-form | [pages/user-form/](pages/user-form/) | PAGE_CONTEXT + RISK_MODEL + TEST_DESIGN + TEST_CASES + PAGE_ELEMENT_POSITION + PAGE_INTERFACE |
| menu-management | [pages/menu-management/](pages/menu-management/) | PAGE_CONTEXT + RISK_MODEL + TEST_DESIGN + TEST_CASES + TECH_ANALYSIS + AUTO_STRATEGY + PAGE_ELEMENT_POSITION + PAGE_INTERFACE |
| api-management | [pages/api-management/](pages/api-management/) | PAGE_CONTEXT + TEST_DESIGN + PAGE_INTERFACE |
| monitor-management | [pages/monitor-management/](pages/monitor-management/) | PAGE_CONTEXT + TEST_DESIGN + PAGE_INTERFACE |

## 待建模页面（7/12）

| 页面 | 页面数 | 已有自动化覆盖率 | 优先建议 |
|-------|:-----:|:--------------:|:--------:|
| org-management | 1 | ✅ 14条 | P2 — 标准树形CRUD |
| dict-management | 1 | ✅ 部分 | P2 — 标准CRUD |
| params-management | 1 | ✅ 14条 | P2 — 标准CRUD |
| notice-management | 1 | ✅ 8条 | P2 — 标准CRUD |
| job-management (timed-task) | 1 | ✅ 部分 | P2 — 标准CRUD |
| login-log | 1 | ✅ 9条 | P1 — 审计关键数据 |
| operation-log | 1 | ✅ 11条 | P1 — 审计关键数据 |
| system-log | 1 | ✅ 9条 | P1 — 审计关键数据 |

## 治理策略

- 本文件为 system 模块的**汇总层**，维护 12 页面清单与交叉引用
- **system-role 独立模块**: 因 RBAC 特殊性（多角色切换、权限校验、数据范围），角色管理拆分为独立治理模块
- **workflow 独立模块**: 工作流管理（5 页面）为跨模块审批引擎，已独立为 [workflow](../workflow/MODULE_CONTEXT.md) 模块
- **用户管理** (user-list, user-form) 已回归 system 模块，作为普通页面治理
- 其余 7 页面待逐步按优先级建模

## 映射状态

- [x] 模块摘要层 — 从旧 `contexts/system-management/MODULE_CONTEXT.md` 提取
- [x] 子页面清单 — 12 页面全覆盖
- [x] 交叉引用 — system-role + workflow 独立模块 + RBAC_TEST_PLAN
- [x] 多角色关联度分类 — 保留模块级分析
- [x] 5/12 页面已独立建模
- [x] **结构纠正 (2026-06-15)** — system-management 降级为 system 模块下的页面组概念，system-user 页面回归 system 模块
- [x] **模块拆分 (2026-06-15)** — workflow（5页面）+ system-role（1页面）独立为顶层模块
- [ ] 其余 7 页面独立建模 — 按优先级逐步推进


<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-17 21:52)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 16 (script/system/test_*.py) |
| Page Object | 15 (page/system_page/*.py) |
| 治理文档 | 32 .md 文件 |
| TECH_ANALYSIS | 3 |
| AUTO_STRATEGY | 3 |
| RISK_MODEL | 5 |
| PAGE_CONTEXT | 6 |
| SOP 状态 | completed |
| Phase 完成 | Automation, Bug Analysis, Data Sanitization, Execute & Debug, Knowledge, Project Init, Report, Requirement, Test Design |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->