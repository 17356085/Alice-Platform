# 文档完整性报告 — Web Automation

> **生成日期**: 2026-06-15 | **生成者**: project-agent | **下次检查**: 有新模块加入或 Phase 推进时
> **检查范围**: `governance/context/projects/web-automation/modules/` 全部 11 个模块 + 1 个空模块

---

## 总览

| 指标 | 数值 |
|------|:---:|
| 模块总数 | 12 (含空模块 system) |
| 页面总数 | ~78 |
| 文档总数 | ~300 (2026-06-17 校正：原 ~350，实际 web-automation context ~250 + skills/templates ~50) |
| 模块覆盖率 (有 MODULE_CONTEXT) | 11/12 (92%) |
| 页面覆盖率 (有 PAGE_CONTEXT) | ~55/78 (71%) |
| SOP Phase 完整闭环模块 | 3 (lab, sales, equipment/alarm-config+camera) |

---

## 文档类型分布

| 文档类型 | 存在数 | 应有数 | 覆盖率 |
|----------|:-----:|:-----:|:-----:|
| MODULE_CONTEXT.md | 11 | 12 | 92% |
| PAGE_CONTEXT.md | 55 | 78 | 71% |
| PAGE_INTERFACE.yaml | 64 | 78 | 82% |
| RISK_MODEL.md | 37 | 78 | 47% |
| TEST_DESIGN.md | 44 | 78 | 56% |
| TEST_CASES.md | 40 | 78 | 51% |
| TECH_ANALYSIS.md | 44 | 78 | 56% |
| PAGE_ELEMENT_POSITION.md | 37 | 78 | 47% |
| AUTO_STRATEGY.md | 45 | 78 | 58% |

---

## 逐模块检查

### 1. equipment — 设备管理 (7页/4上下文页)

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |
| TEST_SUMMARY | ✅ |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| alarm-config | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| camera | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| key-param | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| maintenance | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| **unit** (装置台账) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **0%** 🔴 |
| **device** (设备台账) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **0%** 🔴 |
| **sensor** (传感器) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **0%** 🔴 |

> ⚠️ unit/device/sensor 有 Page Object + 测试脚本但无上下文文档 — P0 阻塞

---

### 2. dcs — DCS数据管理 (5页)

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| all-data | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | 25% |
| common-data | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | 25% |
| monitor | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | 25% |
| point-config | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | 25% |
| upload-log | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | 25% |

> ⚠️ scaffold-only 模块 — 仅 TECH_ANALYSIS + AUTO_STRATEGY，缺全部基础文档 (P0)

---

### 3. lab — 化验室取样 (7页) ✅ SOP闭环

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |
| TEST_SUMMARY | ✅ |
| CURRENT_TASK | ✅ (完成) |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| gas-analysis-report | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| gas-compare | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| gas-indicator | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| water-report | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| water-compare | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 25% 🟡 |
| water-indicator | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 25% 🟡 |
| water-analysis-report | — | — | — | — | — | — | — | — | 见 water-report |

> ⚠️ water-compare/water-indicator 缺深度文档 (P1) — gas/water 对称可基于 gas 版本推断

---

### 4. personnel — 人员管理 (14页)

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| certificate | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| course | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| employee | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| exam | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| paper | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| plan | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| post | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| practice | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| question | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| study-record | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| wrong-question | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| **contractor-personnel** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | 50% 🟡 |
| **contractor-unit** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | 50% 🟡 |
| **entry-approval** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | 50% 🟡 |
| **entry-record** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | 50% 🟡 |
| **entry-confirm** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | 50% 🟡 |

> ⚠️ contractor/entry 5 页面缺 RISK_MODEL + PAGE_ELEMENT_POSITION + AUTO_STRATEGY + PAGE_INTERFACE (P1)。entry-confirm 为 2026-06-15 新增页面，含 5 治理文档。

---

### 5. production — 生产管理 (4页)

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |
| TEST_SUMMARY | ✅ |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| business-type-config | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | 88% |
| daily-report | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| monthly-report | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | 75% |
| shift-team-config | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | 88% |

> ⚠️ 缺 PAGE_ELEMENT_POSITION ×3 + PAGE_INTERFACE ×1 (P2)

---

### 6. sales — 销售管理 (4页) ✅

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| contract | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| customer | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| daily-report | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| sales-order | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |

> ✅ 全页面 100% SOP 文档覆盖

---

### 7. system-user — 用户管理 (2页)

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| user-list | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| user-form | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | 75% |

---

### 8. system-role — 角色管理 (1页)

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |
| CURRENT_TASK | ✅ (进行中) |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| role-list | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |

---

### 9. system-management — 系统管理 (8页)

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |
| CURRENT_TASK | ✅ (进行中) |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| menu-management | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| api-management | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% 🟡 |
| approval-chain | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% 🟡 |
| approval-history | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% 🟡 |
| approval-todo | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% 🟡 |
| monitor-management | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% 🟡 |
| my-application | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% 🟡 |
| sap-push-log | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% 🟡 |

> ⚠️ 7 个工作流页面仅 PAGE_CONTEXT + PAGE_INTERFACE + TEST_DESIGN，缺 RISK_MODEL/TEST_CASES/TECH_ANALYSIS/PEP/AUTO_STRATEGY (P1)

---

### 10. system — 系统管理 (5 pages) 🟡

> 2026-06-17 更新：system 模块非空 — 包含 user-list, user-form, menu-management, api-management, monitor-management 5 pages + 32 治理文档。

| 页面 | PAGE_CONTEXT | PAGE_INTERFACE | RISK_MODEL | TEST_DESIGN | TEST_CASES | TECH_ANALYSIS | PEP | AUTO_STRATEGY | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| user-list | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 100% 🟢 |
| user-form | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | 38% 🟡 |
| menu-management | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | 50% 🟡 |
| api-management | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% 🟡 |
| monitor-management | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% 🟡 |

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ (含 RISK_MODEL + TEST_DESIGN) |
| 测试文件 | 16 个 test_*.py (system 聚合) |
| Page Object | 17 个 (system_page/) |
| 治理文档 | 32 个 .md (module-level 4 + pages 28) |

> **说明**: system-user (user-list, user-form) 和 system-management (menu/api/monitor) 页面在治理层归属 system 模块，但脚本层共享 `script/system/` 目录。system-role 独立为单独模块。

---

### 11. tank — 储罐管理 (3页)

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |
| TEST_SUMMARY | ✅ |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| monitor | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| report | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| alarm-config | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | 75% 🟡 |

> ⚠️ alarm-config 缺 TEST_DESIGN + PAGE_ELEMENT_POSITION (P0 — 阻塞自动化)

---

### 12. warehouse — 库管管理 (17页)

| 指标 | 状态 |
|------|:---:|
| MODULE_CONTEXT | ✅ |

| 页面 | PC | PI | RM | TD | TC | TA | PEP | AS | 完成度 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|
| hazard-in-order | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% |
| hazard-out-order | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% |
| spare-in-order | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% |
| spare-out-order | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% |
| spare-requisition | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | 50% |
| spare-stock | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 38% |
| hazard-quick | ⚠️¹ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 6% |
| spare-quick | ⚠️¹ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 6% |
| hazard-item | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 13% |
| hazard-io-record | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 13% |
| hazard-stock | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 13% |
| reagent-fill | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 13% |
| reagent-item | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 13% |
| spare-io-record | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 13% |
| spare-item | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 13% |
| spare-stock-adjust | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 13% |
| spare-stocktake | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 13% |

> ¹ hazard-quick/spare-quick 使用 PAGE_CONTEXT_SUMMARY.md (非标准命名)
> ⚠️ warehouse 模块治理追补中 — Phase 2，大量页面仅 PAGE_INTERFACE.yaml (P0)

---

## 优先级修复清单

### 🔴 P0 — 阻塞测试执行

| # | 模块 | 缺失项 | 获取方式 | 备注 |
|:--:|------|--------|----------|------|
| 1 | equipment/unit | 全部文档 | 需浏览器 | 有 PO + 测试，缺上下文 |
| 2 | equipment/device | 全部文档 | 需浏览器 | 有 PO + 测试，缺上下文 |
| 3 | equipment/sensor | 全部文档 | 需浏览器 | 有 PO + 测试，缺上下文 |
| 4 | dcs/* (5页) | PAGE_CONTEXT + TEST_DESIGN + RISK_MODEL + TEST_CASES + PEP | 需浏览器 | scaffold-only |
| 5 | warehouse (10页) | PAGE_CONTEXT + TEST_DESIGN | 需浏览器 | 仅 PAGE_INTERFACE |
| 6 | tank/alarm-config | TEST_DESIGN + PAGE_ELEMENT_POSITION | 可推断 | 有 PAGE_CONTEXT + TEST_CASES |

### 🟡 P1 — 影响质量

| # | 模块 | 缺失项 | 获取方式 |
|:--:|------|--------|----------|
| 7 | lab/water-compare | RISK_MODEL + TEST_DESIGN + TEST_CASES + TECH_ANALYSIS + PEP + AUTO_STRATEGY | 可推断 (对称 gas-compare) |
| 8 | lab/water-indicator | RISK_MODEL + TEST_DESIGN + TEST_CASES + TECH_ANALYSIS + PEP + AUTO_STRATEGY | 可推断 (对称 gas-indicator) |
| 9 | personnel/contractor-* (4页) | RISK_MODEL + PEP + AUTO_STRATEGY + PAGE_INTERFACE | 需浏览器 |
| 10 | system-management/7页 | RISK_MODEL + TEST_CASES + TECH_ANALYSIS + PEP + AUTO_STRATEGY | 可推断 (有 TEST_DESIGN) |

### 🟢 P2 — 锦上添花

| # | 模块 | 缺失项 |
|:--:|------|--------|
| 11 | production (3页) | PAGE_ELEMENT_POSITION |
| 12 | warehouse (全模块) | RISK_MODEL + TEST_CASES + TECH_ANALYSIS + PEP + AUTO_STRATEGY |

---

## 治理缺口汇总

| 类型 | 数量 | 明细 |
|------|:---:|------|
| 空模块目录 | 1 | `modules/system/` (有代码无上下文) |
| 有 PO 无上下文 | 3页 | equipment/unit, device, sensor |
| 仅 scaffold | 5页 | dcs/* |
| 仅 PAGE_INTERFACE | 10页 | warehouse 大部分页面 |
| CURRENT_TASK 过时 | 2 | system-management (6/12), system-role (6/11) |

---

## 建议下一动作

1. **立即**: requirement-agent 进入 equipment/unit, device, sensor — 补 PAGE_CONTEXT + TEST_DESIGN
2. **本周**: 补齐 dcs 5 页面基础文档 (PAGE_CONTEXT + RISK_MODEL + TEST_DESIGN)
3. **本周**: 推进 warehouse 治理追补 (已有 13 测试 + 14 PO，上下文严重落后)
4. **持续**: lab water-compare/indicator 可基于 gas 版本快速推断生成
5. **持续**: system-management 7 页面补深度文档

---

> **下次检查**: 有新模块加入或重大 Phase 推进时。建议每 2 周自动触发 completeness-check。






<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: completeness-stats -->
## Auto Stats (2026-06-17 21:52)

| Modules | 100% | Tests | Docs | Overall |
|:---:|:---:|:---:|:---:|:---:|
| 12 | 2 | 116 | 351 | 81% |

### Per-Module

| Module | SOP | Tests | Docs | TECH | AUTO | RISK | Progress |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| system-user | completed | 16 | 32 | 3 | 3 | 5 | 89% |
| system-role | completed | 6 | 15 | 1 | 1 | 2 | 89% |
| system-management | pending | 1 | 0 | 0 | 0 | 0 | 0% |
| equipment | completed | 8 | 30 | 4 | 4 | 4 | 89% |
| tank | completed | 6 | 21 | 3 | 3 | 3 | **100%** |
| personnel | completed | 18 | 99 | 16 | 12 | 11 | 89% |
| sales | completed | 20 | 29 | 4 | 4 | 4 | 89% |
| lab | completed | 9 | 40 | 5 | 5 | 5 | **100%** |
| production | completed | 5 | 27 | 4 | 4 | 4 | 89% |
| dcs | partial | 5 | 11 | 5 | 5 | 0 | 56% |
| warehouse | completed | 16 | 26 | 5 | 5 | 5 | 89% |
| workflow | completed | 6 | 21 | 2 | 2 | 3 | 89% |

> sync_progress.py
<!-- ⚠️ AUTO-GENERATED SECTION END: completeness-stats -->