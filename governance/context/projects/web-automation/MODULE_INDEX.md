# Web Automation Module Index

> **版本**: 2.1 | **最后更新**: 2026-06-15 | **维护者**: Project Agent
> ⚠️ 新增模块时更新此表；模块状态变更时同步更新 last_updated。

## 说明
本项目上下文按测试模块组织，模块是协作与治理的核心单位。

## 当前模块清单

| 模块ID | 模块名称 | SOP Phase | 状态 | 页面数 | PO | 测试 | 治理路径 |
|------|------|:---:|------|:---:|:---:|:---:|------|
| equipment | 设备管理 | Phase 2–3 | 🔄 进行中 | 7 (4上下文) | 7 | 7 | modules/equipment/ |
| dcs | DCS数据管理 | scaffold | ⏳ 仅骨架 | 5 | 5 | 5 | modules/dcs/ |
| lab | 化验室取样 | Phase 9 ✅ | ✅ SOP闭环 | 7 | 9 | 10 | modules/lab/ |
| personnel | 人员管理 | Phase 2–3 | 🔄 进行中 | 14 | 15 | 15 | modules/personnel/ |
| production | 生产管理 | Phase 2 | 🔄 进行中 | 4 | 4 | 4 | modules/production/ |
| sales | 销售管理 | Phase 3 ✅ | ✅ 全页面覆盖 | 4 | 4 | 19 | modules/sales/ |
| system | 系统管理 | Phase 4.5 | 🔄 进行中 | 12 (5已建模) | 11 | 15 | modules/system/ |
| system-role | 角色管理 (RBAC独立) | Phase 4.5 | 🔄 Bug修复中 | 1 | 1 | 20 | modules/system-role/ |
| tank | 储罐管理 | Phase 8 ✅ | ✅ 3/3页 | 3 | 3 | 3 | modules/tank/ |
| warehouse | 库管管理 | Phase 2 | 🔄 治理追补中 | 17 | 14 | 13 | modules/warehouse/ |
| workflow | 工作流管理 | Phase 4.5 | ✅ 5/5页 | 5 | 5 | 6 | modules/workflow/ |

> 图例：✅ 完成 | 🔄 进行中 | ⏳ 待开始 | ⚠️ 治理缺口
> 注：2026-06-15 — workflow(工作流管理)和 system-role(角色职权分配)从 system 模块独立为顶层模块

### 🛠️ 结构纠正 (2026-06-15)

- **system** 是被测系统中的顶层模块（对应"系统管理"菜单组），含 12 个页面（5 个工作流页面 + 1 个角色管理页面已独立）。
- **system-user** (用户管理) 实为 system 模块下的两个页面 (user-list, user-form)，已回归 system/pages/。
- **system-role** 独立模块：RBAC 特殊性（多角色切换、权限分配、数据范围配置），测试复杂度远超普通 CRUD 页面。物理文件已独立 (`page/system_role_page/`, `script/system-role/`)。
- **workflow** 独立模块 (2026-06-15 新增)：工作流管理为跨模块审批引擎，被 warehouse 强依赖，含 5 页面。

## 模块状态详情

### ✅ SOP 闭环
| 模块 | 完成日期 | 测试结果 | 备注 |
|------|---------|----------|------|
| lab | 2026-06-12 | 32P/0F | 6/6 页面全覆盖，全量回归通过 |
| tank | 2026-06-11 | 16P | 3/3 页面覆盖，alarm-config 缺 TEST_DESIGN |
| sales | — | 20+ cases | 4/4 页面 100% SOP 文档覆盖 |

### 🔄 进行中
| 模块 | 当前 Phase | 剩余工作 | 阻塞项 |
|------|:---:|------|------|
| equipment | Phase 2–3 | unit/device/sensor 3 页面缺全部上下文文档 | 需浏览器访问诊断 |
| personnel | Phase 2–3 | contractor/entry 4 页面缺深度文档 | — |
| production | Phase 2 | 缺 PAGE_ELEMENT_POSITION ×3 | — |
| system | Phase 4.5 | 5/12 页面已建模；workflow+system-role 已独立 | approval_chain/SAP/API/监控 已迁出 |
| system-role | Phase 4.5 | 6 failed → 待修复 (s/wait_table_ready/wait_page_ready)；物理文件已独立 | — |
| warehouse | Phase 2 | 10 页面仅 PAGE_INTERFACE，缺 PAGE_CONTEXT + TEST_DESIGN | 需浏览器诊断 |
| workflow | Phase 4.5 | 5/5 页面全覆盖，38 cases，3轮修复后稳定 | — |

### ⚠️ 治理缺口
| 模块 | 问题 | 建议 |
|------|------|------|
| system (8 待建模页面) | org/dict/params/notice/job/log-management 有 PO + 测试但无上下文文档 | requirement-agent → PAGE_CONTEXT + TEST_DESIGN |
| equipment/unit, device, sensor | 有 PO + 测试但无任何上下文文档 | requirement-agent → PAGE_CONTEXT + TEST_DESIGN |
| dcs/* | 5 页面仅 TECH_ANALYSIS + AUTO_STRATEGY | requirement-agent → PAGE_CONTEXT → 完整 SOP |

## 模块治理规则
- 每个模块至少应具备 MODULE_CONTEXT
- 页面级资产按 pages/<page>/ 组织
- 页面下应逐步沉淀：
  - PAGE_CONTEXT.md (Phase 1)
  - PAGE_INTERFACE.yaml (token 优化)
  - RISK_MODEL.md (Phase 1.5)
  - TEST_DESIGN.md (Phase 2)
  - TEST_CASES.md (Phase 2.5)
  - TECH_ANALYSIS.md (Phase 3)
  - PAGE_ELEMENT_POSITION.md (Phase 3)
  - AUTO_STRATEGY.md (Phase 3.5)

## 迁移策略
- 阶段 1：仅建立模块索引，不搬文件 ✅ (已完成)
- 阶段 2：新增文档优先写入治理层 🔄 (进行中)
- 阶段 3：稳定后再决定是否将旧资产逐步归档或迁移 ⏳

## 相关资源
- 完整性报告: `COMPLETENESS_REPORT.md`
- 项目上下文: `PROJECT_CONTEXT.md`
- 进度追踪: `governance/context/tracking/progress-tracking.md`
- 已知问题库: `governance/context/known-issues.yaml`
