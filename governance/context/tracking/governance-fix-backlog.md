# Governance Fix Backlog

> 来源：GOVERNANCE_FULL_AUDIT-2026-06-17 (57 findings)
> 最后更新：2026-06-17

## 进度统计

| 优先级 | 总数 | ✅ 完成 | 🔄 进行中 | ⏳ 待开始 |
|:------:|:---:|:------:|:--------:|:--------:|
| P0 | 6 | 6 | 0 | 0 |
| P1 | 8 | 7 | 0 | 1 |
| P2 | 18 | 18 | 0 | 0 |
| P3 | 12 | 11 | 0 | 1 |

---

## P0 — 立即修复 (数据完整性 / 假阳性阻断)

<!-- ⚠️ AUTO-GENERATED SECTION BEGIN: p0-items -->
<!-- Source: governance/artifacts/sop-status/ + manual audit -->
<!-- Regenerate: python tools/sync_progress.py --check-governance -->

| ID | 文件 | 问题描述 | 修复措施 | 验证方法 | 工作量 | 状态 |
|----|------|---------|---------|---------|:-----:|:----:|
| P0-01 ✅ | `artifacts/sop-status/SOP_STATUS_*.json` | batch 3 覆盖丢失 50%+ 字段 (execution_results, sub_pages, phase_details, fix_logs) | 从 `backup-20260617/` 恢复，调查写入逻辑 | diff backup vs live 确认字段完整 | M | ⏳ |
| P0-02 ✅ | `kpi/timeseries/sop-*-2026-06-17.jsonl` | 11 模块全部 drift_count=0, compliance_score=1.0 — KPI 伪造数据 | 修复 KPI 生成器读取真实 SOP_STATUS；有 drift 的模块如实报告 | 抽查 3 模块 KPI vs SOP_STATUS 一致性 | M | ⏳ |
| P0-03 ✅ | `kpi/timeseries/sop-system-management-*.jsonl` | 声称 9/9 完成，实际 pending 0 pages | KPI 生成器：status=pending 时 skip 或标记 skipped | 重新生成后 system-management KPI = skipped | S | ⏳ |
| P0-04 ✅ | `context/tracking/migration-status.yaml` | tank=15% (实际 100%), lab/人员/生产/销仓=0% (实际 89-100%), 中文键重复 | 基于 SOP_STATUS 全量重写，统一英文键 | 所有模块百分比与 SOP_STATUS 一致 | M | ⏳ |
| P0-05 ✅ | `artifacts/sop-status/` (DCS) | DCS 零 SOP_STATUS — 5 pages, 11 gov docs, 5 test files 无追踪 | 基于现有 TECH_ANALYSIS×5 + AUTO_STRATEGY×5 生成 SOP_STATUS_dcs.json | SOP_STATUS_dcs.json 存在且字段完整 | S | ⏳ |
| P0-06 ✅ | `tools/p1_verify_review_agent.py:16` | assert len(skills)==5, YAML 实际 16 — 假阳性 CI 阻断 | 改为 assert len(skills)==16 (lines 16, 79) | pytest tools/p1_verify_review_agent.py 通过 | S | ⏳ |

<!-- ⚠️ AUTO-GENERATED SECTION END: p0-items -->

---

## P1 — 本周修复 (文档与代码脱节)

| ID | 文件 | 问题描述 | 修复措施 | 验证方法 | 工作量 | 状态 |
|----|------|---------|---------|---------|:-----:|:----:|
| P1-01 ✅ | `context/project-index.yaml` | 缺 workflow 模块 (列 10 实际 12)，claim "9模块" | 添加 workflow + system-management；更新注释 | grep workflow project-index.yaml 命中 | S | ⏳ |
| P1-02 ✅ | `context/.../modules/lab/MODULE_CONTEXT.md` | water-compare/indicator 声称 8 文档 (实际仅 3: PAGE_CONTEXT, PEP, PAGE_INTERFACE) | 修正表：标记 RISK_MODEL/TEST_DESIGN/TEST_CASES/TECH_ANALYSIS/AUTO_STRATEGY 为 ⏳ | 表格与实际 `ls pages/water-*/` 一致 | S | ⏳ |
| P1-03 ✅ | `context/.../COMPLETENESS_REPORT.md` | 声称 system 为"空模块" (实际 5 pages: user-list, user-form, menu-mgmt, api-mgmt, monitor-mgmt) | 重写 system 模块段，列出 5 pages + 文档状态 | system 段 pages 数与 MODULE_CONTEXT 一致 | M | ⏳ |
| P1-04 ✅ | `context/.../modules/warehouse/MODULE_CONTEXT.md` | 声称 "PO 待创建" "测试脚本待创建" (实际 14 PO, 16 test files) | 更新自动化代码规划段为实际状态 | 段中 PO/test 计数 = progress-tracking 统计 | S | ⏳ |
| P1-05 ✅ | `context/.../modules/dcs/MODULE_CONTEXT.md` | 声称 "0 PO, 0 测试" (实际 6 PO, 5 test files) | 更新为实际代码状态 + 标注缺失 Phase | PO/test 计数与 disk 一致 | S | ⏳ |
| P1-06 | `artifacts/reviews/` | 17 份 review 全部 system-only — 零业务模块 architecture review | equipment/warehouse/personnel 各生成 1 份 architecture review | 3 新 review 文件存在于 business module 目录 | L | ⏳ |
| P1-07 ✅ | `kpi/` | `reports/` 目录缺失 (README 声称存在) | 创建 `reports/{module}/` 骨架目录 或更新 README | `ls kpi/reports/` 存在 | S | ⏳ |
| P1-08 ✅ | `context/.../modules/equipment/MODULE_CONTEXT.md` | key-param 行无状态标注 (实际 8 文档 100% 完成) | 为 key-param 添加状态："已完成全部 8 文档" | key-param 行有状态标注 | S | ⏳ |

---

## P2 — 待排期 (模板/计数/孤立文件/过期引用)

| ID | 文件 | 问题描述 | 修复措施 | 验证方法 | 工作量 | 状态 |
|----|------|---------|---------|---------|:-----:|:----:|
| P2-01 ✅ | `templates/test-design.template.md:3,24` | 声称"8 个测试维度"，Agent 定义要求 9 (缺业务场景验证) | 改为 9 维度，添加业务场景验证行 | 模板维度数 = agent-definitions 要求 | S | ⏳ |
| P2-02 ✅ | `skills/execution/data-sanitization.md` | 孤立 Skill — 不在 registry 也不被任何 Agent 引用 | 注册到 skill-registry.yaml 或删除孤立文件 | 文件在 registry 中有条目 or 文件被删除 | S | ⏳ |
| P2-03 [OK] | `skills/test-design/page-analysis-v0.9-degraded.md` | 孤立旧版 stub 文件 (TODO placeholder) | 移至 `_deprecated/` 或删除 | 文件不在活跃 skills/ 目录 | S | ⏳ |
| P2-04 ✅ | `workflows/automation-implementation.md:34,36` | 引用已废弃 conftest-generator + element-plus-locator | 替换为合并后 Skill: test-script-generator + tech-analysis | grep 无废弃名 | S | ⏳ |
| P2-05 ✅ | `artifacts/reviews/system/` | 6/17 review 内部 created 日期造假 (2024, 2025, 未来 2026-06-25) | 修正 frontmatter `created:` 字段为 2026-06-16 | 每个文件 created ≈ filename date | S | ⏳ |
| P2-06 | `artifacts/bug-analysis/` | 仅 4 文件 (tank, personnel, equipment, cross-module)，6 天未更新，覆盖 2/12 模块 | bug-analysis 集成到 SOP execution post-hook；为剩余 10 模块各生成 1 份 | bug-analysis/ 下 ≥12 文件 | L | ⏳ |
| P2-07 [OK] | `artifacts/code-review/` | equipment + dcs 缺 code-review | 对 equipment (8 PO) + dcs (6 PO) 运行 code-consistency-checker | code-review/equipment/ + code-review/dcs/ 存在 | M | ⏳ |
| P2-08 [OK] | `docs/architecture/ARCHITECTURE_REVIEW_V2*.md` | 声称"20 活跃 Skill + 6 废弃" (实际 25 active + 2 deprecated) | 更新计数：25 active, 2 experimental, 2 deprecated | 文档计数 = skill-registry.yaml 实际 | S | ⏳ |
| P2-09 [OK] | `docs/architecture/governance-layer-design-review.md:730` | 声称当前 Agent(17) Skill(56) — 实际 Agent(8) Skill(25) (2-5× 膨胀) | 标注为"目标状态" 或修正为实际数字 | 文档数字匹配实际 | S | ⏳ |
| P2-10 [OK] | `docs/plans/IMPROVEMENT_PLAN_v2.1.md:69-75` | `aitest/agent_runner.py` 路径错误 (实际 `aitest/agents/agent_runner.py`) | 修正所有引用路径 | grep 旧路径无命中 | S | ⏳ |
| P2-11 [OK] | `docs/plans/DEFERRED_PATHS_PLAN.md` vs `PLATFORM_INDEPENDENCE_ROADMAP.md` | 两份文档都声称 LangGraph 移植"✅ 完成" — 自相矛盾 | 统一完成状态标注 + 日期戳 | 两份文档中同一事项状态一致 | S | ⏳ |
| P2-12 ✅ | `skills-dev/skill-registry-dev.yaml:563` | 注释声称 review (14) + (9) = 23，实际 5+10=15 | 修正注释：`review (15) — P0(5) + P1(10)` | 注释数字 = 实际条目数 | S | ⏳ |
| P2-13 [OK] | `agents/` | 9 test agents 有 .md 文档，11 dev/meta agents 零 .md | 运行 `python -m aitest.check_agent_drift` 生成或手动创建骨架 | agents/ 下每个 Agent 有对应 .md | M | ⏳ |
| P2-14 [OK] | `templates/sop-gate.template.md` | 缺 BU + PE check flags 文档 (`--check-bu-imports`, `--check-pe-template` 等) | 添加 BU/PE 检查段到模板 | 模板覆盖所有 check_sop_gate.py flags | S | ⏳ |
| P2-15 ✅ | `context/shared-language.md` | 缺 workflow, dcs, system-role 业务术语段 | 为 3 模块各添加 1 段业务术语定义 | shared-language 有 workflow/dcs/system-role 条目 | S | ⏳ |
| P2-16 [OK] | `artifacts/audits/` | system-management 零 state-audit + sop-audit (其他 11 模块都有) | 为 system-management 生成 audit pair | audits/ 下 system-management 有 2 文件 | S | ⏳ |
| P2-17 ✅ | `artifacts/sop-status/` | system-management SOP_STATUS 缺 artifact_count, note 字段 (与其他 11 模块不一致) | 补齐字段使 schema 一致 | diff schema 与其他模块一致 | S | ⏳ |
| P2-18 [OK] | `kpi/timeseries/cost-all-2026-06-17.jsonl` | 全零成本 (total_tokens=0, cost=0.0) + 无历史 cost 数据 | 确认 E2E 执行确实零成本，或实施 cost 跟踪 | cost 数据非零或文档说明为何为零 | S | ⏳ |

---

## P3 — 低优先级 (优化/清理/未来防护)

| ID | 文件 | 问题描述 | 修复措施 | 工作量 |
|----|------|---------|---------|:-----:|
| P3-01 ✅ | `artifacts/audits/` | equipment 有 6 sop-audit + 7 state-audit 变体 (只保留最新即可) | 清理：每个模块只保留最新 2026-06-16 版本 | S |
| P3-02 ✅ | `artifacts/audits/state-audit-personnel-*` | personnel 在 11 秒内生成 3 份相同 state-audit (17586 bytes identical) | 去重，保留 1 份 | S |
| P3-03 ✅ | `knowledge/pitfalls/README.md` | 引用不存在的 `project-specific/` 目录 | 删除该行 或 创建目录 | S |
| P3-04 [OK] | `knowledge/pitfalls/*/` | 3 文件 `最近出现` 均为 2026-06-10 (7 天前) | 如问题仍活跃则更新日期 | S |
| P3-05 [OK] | `context/.../COMPLETENESS_REPORT.md` | 声称 ~350 文档 (实际 ~250) | 修正计数 | S |
| P3-06 [OK] | `context/.../COMPLETENESS_REPORT.md` (personnel) | 缺 entry-confirm 页面 (5 治理文档存在但报告未列) | 添加 entry-confirm 行 | S |
| P3-07 [OK] | `context/.../modules/system/pages/user-list/ANALYSIS.md` | 非标准文档名 (标准为 PAGE_CONTEXT/RISK_MODEL/TEST_DESIGN 等) | 重命名或整合到标准文档 | S |
| P3-08 [OK] | `context/environments.yaml` | dev/test/staging 三个环境同 URL | 如单环境则添加注释说明 | S |
| P3-09 [OK] | `artifacts/reviews/system/ARCH_REVIEW_FULL*.md` | 声称 15 review skills (实际 16), 71 total skills (实际 83), 17 event types (实际 18) | 更新 ARCH_REVIEW 中的计数 | S |
| P3-10 [OK] | `artifacts/execution-reports/` | 仅 1 文件 (system-management 6/12), 零其他模块 | 为最近执行过的模块生成 execution reports | M |
| P3-11 [OK] | `artifacts/test-summaries/` | 仅 4 文件覆盖 lab/system-mgmt/workflow/cross，缺 8 模块 | 补齐 Phase 8 test summaries | L |
| P3-12 [OK] | `governance/.review_queue/` | 空目录 — review queue 机制未使用 | 实现或移除目录引用 | S |

---

## 执行顺序

```
P0-06 (假阳性CI) → P0-04 (migration-status) → P0-01 (SOP_STATUS恢复)
→ P0-05 (DCS SOP_STATUS) → P0-02 (KPI修复) → P0-03 (KPI skip pending)
→ P1-01→P1-05 (MODULE_CONTEXT修正) → P1-03 (COMPLETENESS_REPORT)
→ P1-06 (业务模块reviews) [parallel with P2]
→ P2-01→P2-18 (模板/孤立文件/计数修正)
→ P3 cleanup
```

---

## 结构防护 (防止再生)

| 措施 | 状态 | 描述 |
|------|:----:|------|
| A. sync_progress.py 扩展 | ⏳ | 覆盖 migration-status.yaml, project-index.yaml, MODULE_CONTEXT 验证 |
| B. KPI 生成器修复 | ⏳ | 从 SOP_STATUS 读真实数据，pending 模块 skip |
| C. `--check-doc-consistency` gate | ⏳ | 验证 MODULE_CONTEXT 声明 vs 磁盘实际 |

<!-- FOOTER: last_sync=2026-06-17T19:00:00+08:00 source=GOVERNANCE_FULL_AUDIT -->
