# SOP 欠债清单

**生成日期**: 2026-06-13  
**图例**: PC=PAGE_CONTEXT, TC=TEST_CASES, TD=TEST_DESIGN, RM=RISK_MODEL, TA=TECH_ANALYSIS, AS=AUTO_STRATEGY, PI=PAGE_INTERFACE, PO=PageObject, TEST=测试脚本  
**标准**: docs 7/7 + code 2/2 = SOP 闭环

---

## 已完成（无需操作）

| 模块 | 页面 | 状态 |
|------|------|:--:|
| equipment | alarm-config | ✅ |
| equipment | key-param | ✅ |
| personnel | certificate, course, employee, exam, paper, plan, post, question, practice, study-record, wrong-question | ✅ 11p |
| production | business-type-config, daily-report, shift-team-config | ✅ |
| sales | customer, contract, sales-order, daily-report | ✅ |
| tank | monitor, report | ✅ |

---

## 第一批：文档齐全，只缺代码（7 个页面）

> 对会话说：`帮我测 {模块} 模块的 {页面} 页面`

| # | 模块 | 页面 | 缺 | 会话口令 |
|:--:|------|------|:--:|---------|
| 1 | equipment | camera | PO TEST | `帮我测 equipment 模块的 camera 页面` |
| 2 | equipment | maintenance | TEST | `帮我测 equipment 模块的 maintenance 页面` |
| 3 | system-management | menu-management | PO TEST | `帮我测 system-management 模块的 menu-management 页面` |
| 4 | system-role | role-list | PO TEST | `帮我测 system-role 模块的 role-list 页面` |
| 5 | system-user | user-list | PO TEST | `帮我测 system-user 模块的 user-list 页面` |
| 6 | system-user | user-form | TA AS PO TEST | `帮我测 system-user 模块的 user-form 页面` |
| 7 | production | monthly-report | PI | `帮我测 production 模块的 monthly-report 页面` |

---

## 第二批：缺测试设计，有 PAGE_CONTEXT（13 个页面）

> 对会话说：`帮我测 {模块} 模块的 {页面} 页面`
> 缺 RISK_MODEL + TEST_CASES + TEST_DESIGN，preflight 会自动从 Test Design 阶段开始

| # | 模块 | 页面 | 缺 | 会话口令 |
|:--:|------|------|:--:|---------|
| 8 | system-management | api-management | TC RM TA AS PO TEST | `帮我测 system-management 模块的 api-management 页面` |
| 9 | system-management | approval-chain | TC RM TA AS PO TEST | `帮我测 system-management 模块的 approval-chain 页面` |
| 10 | system-management | approval-history | TC RM TA AS PO TEST | `帮我测 system-management 模块的 approval-history 页面` |
| 11 | system-management | approval-todo | TC RM TA AS PO TEST | `帮我测 system-management 模块的 approval-todo 页面` |
| 12 | system-management | monitor-management | TC RM TA AS PO TEST | `帮我测 system-management 模块的 monitor-management 页面` |
| 13 | system-management | my-application | TC RM TA AS PO TEST | `帮我测 system-management 模块的 my-application 页面` |
| 14 | system-management | sap-push-log | TC RM TA AS PO TEST | `帮我测 system-management 模块的 sap-push-log 页面` |
| 15 | warehouse | hazard-in-order | TC RM TA AS TEST | `帮我测 warehouse 模块的 hazard-in-order 页面` |
| 16 | warehouse | hazard-out-order | TC RM TA AS PO TEST | `帮我测 warehouse 模块的 hazard-out-order 页面` |
| 17 | warehouse | spare-in-order | TC RM TA AS | `帮我测 warehouse 模块的 spare-in-order 页面` |
| 18 | warehouse | spare-out-order | TC RM TA AS | `帮我测 warehouse 模块的 spare-out-order 页面` |
| 19 | warehouse | spare-requisition | TC TA AS | `帮我测 warehouse 模块的 spare-requisition 页面` |
| 20 | warehouse | spare-stock | TC RM TA AS | `帮我测 warehouse 模块的 spare-stock 页面` |

---

## 第三批：缺 PAGE_CONTEXT，需从页面分析开始（18 个页面）

> 对会话说：`帮我测 {模块} 模块，从页面分析开始`  
> 或逐个页面：`帮我测 {模块} 模块的 {页面} 页面`

| # | 模块 | 页面 | 缺 | 会话口令 |
|:--:|------|------|:--:|---------|
| 21 | dcs | all-data | PC TC TD RM PI | `帮我测 dcs 模块的 all-data 页面` |
| 22 | dcs | common-data | PC TC TD RM PI | `帮我测 dcs 模块的 common-data 页面` |
| 23 | dcs | monitor | PC TC TD RM PI | `帮我测 dcs 模块的 monitor 页面` |
| 24 | dcs | point-config | PC TC TD RM PI | `帮我测 dcs 模块的 point-config 页面` |
| 25 | dcs | upload-log | PC TC TD RM PI | `帮我测 dcs 模块的 upload-log 页面` |
| 26 | lab | water-compare | TC TD RM TA AS | `帮我测 lab 模块的 water-compare 页面` |
| 27 | lab | water-indicator | TC TD RM TA AS | `帮我测 lab 模块的 water-indicator 页面` |
| 28 | warehouse | hazard-io-record | PC TC TD RM TA AS | `帮我测 warehouse 模块的 hazard-io-record 页面` |
| 29 | warehouse | hazard-item | PC TC TD RM TA AS | `帮我测 warehouse 模块的 hazard-item 页面` |
| 30 | warehouse | hazard-stock | PC TC TD RM TA AS | `帮我测 warehouse 模块的 hazard-stock 页面` |
| 31 | warehouse | reagent-fill | PC TC TD RM TA AS | `帮我测 warehouse 模块的 reagent-fill 页面` |
| 32 | warehouse | reagent-item | PC TC TD RM TA AS | `帮我测 warehouse 模块的 reagent-item 页面` |
| 33 | warehouse | spare-io-record | PC TC TD RM TA AS | `帮我测 warehouse 模块的 spare-io-record 页面` |
| 34 | warehouse | spare-item | PC TC TD RM TA AS | `帮我测 warehouse 模块的 spare-item 页面` |
| 35 | warehouse | spare-stock-adjust | PC TC TD RM TA AS | `帮我测 warehouse 模块的 spare-stock-adjust 页面` |
| 36 | warehouse | spare-stocktake | PC TC TD RM TA AS | `帮我测 warehouse 模块的 spare-stocktake 页面` |
| 37 | warehouse | hazard-quick | PC TC TD RM TA AS PI PO TEST | `帮我测 warehouse 模块的 hazard-quick 页面` |
| 38 | warehouse | spare-quick | PC TC TD RM TA AS PI PO TEST | `帮我测 warehouse 模块的 spare-quick 页面` |

---

## 统计

| 状态 | 页面数 |
|------|:-----:|
| ✅ 已完成 | ~30 |
| 🔴 第一批（缺代码） | 7 |
| 🟡 第二批（缺测试设计） | 13 |
| 🟠 第三批（缺页面分析） | 18 |
| **总欠债** | **38** |

---

## 批量执行建议

每个会话可以处理多个页面。CLAUDE.md 的 `/full-sop` 支持 `--pages` 参数一次性处理多个页面：

```
帮我测 system-management 模块，页面：api-management, approval-chain, approval-history, approval-todo
```

一个会话建议最多提交 4-5 个页面，超出可能超时或 token 耗尽。
