# MODULE_CONTEXT — workflow

> **版本**: 1.0 | **创建日期**: 2026-06-15 | **维护者**: AI
> **来源**: 从 system 模块提取 — 工作流管理原为 system 下子模块，因业务枢纽特性独立为顶层模块

---

## 基本信息

| 字段 | 值 |
|------|-----|
| 模块ID | workflow |
| 模块名称 | 工作流管理 (Workflow Management) |
| 所属项目 | web-automation |
| 入口菜单 | 原 系统管理 → 工作流管理 (独立后待前端调整) |
| 基础路由 | `#/system/workflow/*` (前端路由暂未变更) |
| 测试目录 | `ZJSN_Test-master526/script/workflow/` |
| PO 目录 | `ZJSN_Test-master526/page/workflow_page/` |
| 基准 URL | `https://aiwechatminidemo.cimc-digital.com/#/system/workflow/todo` |
| 权限要求 | `system:workflow:*` 前缀权限点 |
| 存量来源 | 从 `governance/.../modules/system/` 提取 (原 system-management 子模块) |

---

## 模块定位

工作流管理是全平台的 **审批引擎中枢**，承担业务流程的审批调度、状态追踪和 SAP 集成推送。

**为什么独立**: 不同于系统管理的纯配置页面，工作流管理是**业务中游**——warehouse、sales 等模块提交业务单据后，路由到此处审批。它是跨模块业务链路的核心节点，不应埋在"系统配置"下。

---

## 模块边界

| 维度 | 说明 |
|------|------|
| **包含** | 审批链配置、待我审批、我已审批、我发起的、SAP推送日志 |
| **不包含** | 业务单据提交（→ warehouse/sales）、用户权限配置（→ system-role）、审批人管理（→ system/user-list） |
| **关联上游** | warehouse（环保入库/出库提交）、sales（合同审批）、备品领用 |
| **关联下游** | SAP 系统（审批结果推送） |

---

## 🔗 跨模块关联链路

### 审批流程全链路

```
业务模块 (warehouse/sales)               工作流管理 (workflow)
─────────────────────────               ─────────────────────
环保出库/环保入库/备品领用                  审批链配置 (approval-chain)
     │                                      ↑
     │  ① 提交业务单据                        │  前置配置
     │  ② ──── 工作流引擎路由 ────→           │  
     │                                      │  待我审批 (todo) ← 审批人看到任务
     │                                      │  审批通过 / 审批驳回
     │                                      │  我已审批 (history) — 记录归档
     │  ③ ←─── 审批结果回写 ←────────        │  我发起的 (my-applications) — 状态更新
     │                                      │
     │                                      │  SAP推送日志 (sap-push-log)
     │                                      │  审批完成 → SAP推送 → 日志记录
```

### 关联模块详情

| 关联模块 | 关联类型 | 具体关联点 | 测试影响 |
|----------|----------|-----------|----------|
| **warehouse (库管管理)** | 🔗 强依赖 | 环保出库/入库 → 提交 → 审批链 → 待我审批 → 审批通过/驳回 | 端到端测试需跨越 warehouse + workflow 两个模块 |
| **system-role (角色管理)** | 🔗 配置依赖 | 审批链中的审批人角色配置、工作流页面菜单可见性 | RBAC 测试计划覆盖工作流页面权限 |
| **system/user-list (用户管理)** | 🔗 数据依赖 | 审批链中的审批人来自用户列表 | 审批流测试需准备审批人账号 |
| **sales (销售管理)** | 🔗 潜在关联 | 合同管理页面也有审批/工作流路径 | 未来扩展 |

---

## 子页面清单

| 序号 | 页面名称 | 路由 | 页面类型 | 测试用例 | Page Object | 治理路径 |
|:---:|------|------|------|:---:|------|------|
| 1 | **审批链配置** | `#/system/workflow/approval-chain` | CRUD + 弹窗表单 | 9 | ApprovalChainPage.py | pages/approval-chain/ |
| 2 | **待我审批** | `#/system/workflow/todo` | 工作流列表页 | 8 | ApprovalTodoPage.py | pages/approval-todo/ |
| 3 | **我已审批** | `#/system/workflow/history` | 工作流列表页 | 7 | ApprovalHistoryPage.py | pages/approval-history/ |
| 4 | **我发起的** | `#/system/workflow/my-applications` | 工作流列表页 | 8 | MyApplicationPage.py | pages/my-application/ |
| 5 | **SAP推送日志** | `#/system/workflow/sap-push-log` | 日志列表页 | 6 | SapPushLogPage.py | pages/sap-push-log/ |

---

## 已建模页面 (5/5 全覆盖)

| 页面 | 治理路径 | 文档资产 |
|------|---------|---------|
| approval-chain | [pages/approval-chain/](pages/approval-chain/) | PAGE_CONTEXT + TEST_DESIGN + PAGE_INTERFACE |
| approval-todo | [pages/approval-todo/](pages/approval-todo/) | PAGE_CONTEXT + TEST_DESIGN + PAGE_INTERFACE |
| approval-history | [pages/approval-history/](pages/approval-history/) | PAGE_CONTEXT + TEST_DESIGN + PAGE_INTERFACE |
| my-application | [pages/my-application/](pages/my-application/) | PAGE_CONTEXT + TEST_DESIGN + PAGE_INTERFACE |
| sap-push-log | [pages/sap-push-log/](pages/sap-push-log/) | PAGE_CONTEXT + TEST_DESIGN + PAGE_INTERFACE |

---

## 治理策略

- 本文件为 workflow 模块的**汇总层**，维护 5 页面清单与交叉引用
- 各页面细节下沉至 `pages/<page>/` 目录
- SOP 状态追踪: `governance/artifacts/sop-status/SOP_STATUS_workflow.json`

## 映射状态

- [x] 模块摘要层 — 从 system/MODULE_CONTEXT.md 提取
- [x] 子页面清单 — 5 页面全覆盖
- [x] 交叉引用 — warehouse + system-role + system/user-list
- [x] 5/5 页面已独立建模
- [x] 工作流 5 页面测试完成 — 38 cases, 3 轮修复后稳定
- [ ] 前端菜单结构调整 — 待 Vue 项目配合


<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: module-stats -->
<!-- Source: tools/sync_progress.py — regenerated on each SOP run -->
## 自动统计数据 (更新于 2026-06-17 21:52)

| 指标 | 数值 |
|------|:---:|
| 测试文件 | 6 (script/workflow/test_*.py) |
| Page Object | 5 (page/workflow_page/*.py) |
| 治理文档 | 21 .md 文件 |
| TECH_ANALYSIS | 2 |
| AUTO_STRATEGY | 2 |
| RISK_MODEL | 3 |
| PAGE_CONTEXT | 6 |
| SOP 状态 | completed |
| Phase 完成 | Automation, Bug Analysis, Data Sanitization, Execute & Debug, Knowledge, Project Init, Report, Requirement, Test Design |

> 此段由 sync_progress.py 自动更新。手动编辑会被覆盖。
<!-- ⚠️ AUTO-GENERATED SECTION END: module-stats -->