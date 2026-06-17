# 测试进度追踪

> 全局测试进度管理看板。按模块追踪测试工作各阶段完成状态。
> 迁移自 `TestIntern_library/02-项目文档/测试进度追踪.md`（2026-06-11）

<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: progress-table -->
<!-- Source: governance/artifacts/sop-status/SOP_STATUS_*.json + script/ test file counts -->
<!-- Regenerate: python tools/sync_progress.py -->
> 最后更新：2026-06-17 16:53 (auto-sync)

---

## 进度总览

| 模块 | Phase 0.5<br>模块建模 | Phase 1<br>页面分析 | Phase 1.5<br>风险建模 | Phase 2<br>测试设计 | Phase 2.5<br>用例表 | Phase 3<br>技术分析 | Phase 3.5<br>自动化策略 | Phase 4<br>自动化开发 | Phase 8<br>测试总结 | 整体进度 |
|------|------|------|------|------|------|------|------|------|------|------|
| system-user | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⏳ | 89% |
| system-role | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⏳ | 89% |
| system-management | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | 0% |
| equipment | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⏳ | 89% |
| **tank** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| personnel | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⏳ | 89% |
| sales | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⏳ | 89% |
| **lab** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **100%** |
| production | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⏳ | 89% |
| dcs | ✅ | ⏳ | ⏳ | ⏳ | ✅ | ✅ | ✅ | ✅ | ⏳ | 56% |
| warehouse | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⏳ | 89% |
| workflow | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ⏳ | 89% |

> 图例：✅ 已完成 | 🔄 进行中 | ⚠️ 已完成但质量不足（部分页面覆盖） | ⏳ 待开始 | ❌ 阻塞 | — 不适用
<!-- ⚠️ AUTO-GENERATED SECTION END: progress-table -->

---

## 自动化用例统计

<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: test-stats -->
| 模块 | 测试文件 | Page Object | 治理文档 | 备注 |
|------|:-------:|:----------:|:------:|------|
| system (user+role+mgmt) | 23 | 16 | 47 | 16+6+1 test files; system-management 已重置 |
| equipment | 8 | 7 | 30 | TECH=4; AUTO=4; RISK=4; unit/device/sensor/alarm/maint/camera/keyparam + unit-manage |
| tank | 6 | 4 | 21 | TECH=3; AUTO=3; RISK=3; monitor/report/alarm-config |
| personnel | 18 | 17 | 99 | TECH=16; AUTO=12; RISK=11; 16 页面全覆盖 |
| sales | 20 | 4 | 29 | TECH=4; AUTO=4; RISK=4; customer/contract/order/daily-report |
| lab | 9 | 9 | 40 | TECH=5; AUTO=5; RISK=5; gas/water 全覆盖 |
| production | 5 | 4 | 27 | TECH=4; AUTO=4; RISK=4; daily/monthly/business/shift |
| dcs | 5 | 5 | 11 | TECH=5; AUTO=5; all-data/common-data/monitor/point-config/upload-log; 无 SOP_STATUS |
| warehouse | 16 | 14 | 29 | TECH=3; AUTO=2; RISK=4; hazard/spare/reagent 系列 |
| workflow | 6 | 5 | 21 | TECH=2; AUTO=2; RISK=3; approval-chain/history/todo/my-application/sap-push-log |

<!-- ⚠️ AUTO-GENERATED SECTION END: test-stats -->

> 统计口径：测试文件 = `script/<module>/test_*.py`；Page Object = `page/<module>_page/` 下 .py 文件；治理文档 = `governance/context/projects/web-automation/modules/<module>/` 下 .md 文件

---

## 架构与治理健康度

> 数据来源：ARCH_REVIEW_FULL-2026-06-17 (74/100 B级)

| 维度 | 评分 | 关键发现 |
|------|:----:|---------|
| Component Boundary | 75 | Agent/Skill 分离清晰；meta-agent 接线待修复 |
| Data Flow | 70 | Event bus 设计合理；SQLite↔JSON↔FS 状态同步有缝隙 |
| Coupling | 65 | agent_runner.py 1450行单体；共享状态跨 graph |
| Scalability | 78 | 加模块≈4文件；Agent 上限~50 |
| Consistency | 72 | Test/Dev SOP 同模式；Skill 注册表格式分歧 |
| Technical Debt | 60 | SKILL_OUTPUT_MAP 硬编码；bu_adapter.py 空；check_sop_gate.py 过期 |

### Event Bus 覆盖

| 状态 | 数量 | 详情 |
|------|:---:|------|
| ✅ 已接线 | 12/17 | AgentCompleted, StateDrift, SOPViolation, CostAnomaly, AuditCompleted, ContextUpdated, 3×L3Validator |
| 🔴 无消费者 | 5/17 | ArchitectureRiskDetected, GovernanceGapDetected, TechnicalDebtDetected, ProductionRiskDetected, ReviewCompleted |
| 🟡 定义未触发 | 3/17 | BugClosed, CycleEnd, PromptChanged, EvalRegressed |

### 审计报告

| 类型 | 数量 | 最近更新 |
|------|:---:|---------|
| State Audit | 11 modules | 2026-06-16 |
| SOP Audit | 11 modules | 2026-06-16 |
| Architecture Review | 17 份 | 2026-06-17 (FULL + 16 sub-dimensions) |
| **总计** | **55** | — |

---

## 下阶段计划

| 优先级 | 模块 | 计划内容 | 预计开始 |
|:------:|------|---------|---------|
| P0 | system-management | 全量 SOP 重跑 — 已重置，等待 batch 4 | 立即 |
| P0 | warehouse | Phase 3/3.5 深度追补：2 TECH→17 pages, 1 AUTO→17 pages | 本周 |
| P0 | dcs | Phase 1–2.5 补齐：PAGE_CONTEXT×5 + RISK_MODEL + TEST_DESIGN | 本周 |
| P0 | governance | C02 已修复，验证 5 meta-review events 消费者接线 | 立即 |
| P1 | system-role | 修复 6 failed tests (s/wait_table_ready/wait_page_ready) | 本周 |
| P1 | equipment | 补 unit-manage + sensor-manage 页面深度文档 | 本周 |
| P1 | dev-platform | W03: DEV_SKILL_OUTPUT_MAP 32 dev skills 输出持久化 | 本周 |
| P2 | all (×8) | Phase 8 测试总结 — 8 模块缺少 TEST_SUMMARY | 待排期 |
| P2 | personnel | 补 contractor-* 子模块 RISK_MODEL + PEP + AUTO_STRATEGY | 待排期 |
| P2 | governance | W01: agent_runner.py 拆分 (1450→~400 lines) | 待排期 |
| P2 | governance | W02: skill-registry-dev.yaml 统一为 flat 格式 | 待排期 |

---

## 同步机制

进度数据由 `tools/sync_progress.py` 自动生成，读取以下数据源：
1. `governance/artifacts/sop-status/SOP_STATUS_*.json` → Phase 完成状态
2. `ZJSN_Test-master526/script/<module>/test_*.py` → 测试文件计数
3. `ZJSN_Test-master526/page/<module>_page/` → PO 文件计数
4. `governance/context/projects/web-automation/modules/<module>/` → 治理文档计数

**触发方式**：
- 手动：`python tools/sync_progress.py`
- 自动：每次 `aitest graph run` 完成时调用 (SOP runner post-hook)
- 门禁：`check_sop_gate.py --check-progress-sync` 检测过期

<!-- FOOTER: last_sync=2026-06-17T16:53:40+0800 sync_source=auto -->
