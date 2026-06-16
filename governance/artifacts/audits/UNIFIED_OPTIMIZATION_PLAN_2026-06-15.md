# 统一优化方案 — SOP 体系 + Context Cost 交叉审计

> 基于: [SOP_SYSTEM_AUDIT_2026-06-15.md](SOP_SYSTEM_AUDIT_2026-06-15.md) + [CONTEXT_COST_AUDIT_2026-06-15.md](CONTEXT_COST_AUDIT_2026-06-15.md)
> 方法: 交叉引用两份审计的发现，识别共同根因，合并为单一优先级排序

---

## 根因分析: 两份审计的共同病灶

两份审计独立发现了不同层面的症状，但指向三个共同根因:

```
┌─────────────────────────────────────────────────────────────────┐
│                    三个根因 → 两份审计的症状                      │
├──────────────────────────┬──────────────────────────────────────┤
│ 根因                      │ SOP 审计症状    │ Cost 审计症状       │
├──────────────────────────┼──────────────────┼────────────────────┤
│ ① Phase/SOP 定义无       │ 3 套 CANONICAL   │ Agent pipeline     │
│    单一事实源             │ PHASES 并存      │ 4 处重复定义       │
│                           │ resume 模式失效  │ 循环源引用声明     │
├──────────────────────────┼──────────────────┼────────────────────┤
│ ② 状态存储无收敛策略      │ 6 个并发状态源   │ SOP_STATUS         │
│                           │ source-of-truth  │ 双份存储           │
│                           │ 自相矛盾         │                    │
├──────────────────────────┼──────────────────┼────────────────────┤
│ ③ Token 优化停留在        │ PAGE_INTERFACE   │ PAGE_INTERFACE     │
│    文档层面，未验证        │ 被列为"结构化    │ 实际 2,223 tok/页  │
│                           │  接口门控"       │ vs 宣称 200 tok    │
│                           │                  │ 比 PAGE_CONTEXT    │
│                           │                  │ 大 3-10×           │
└──────────────────────────┴──────────────────┴────────────────────┘
```

---

## 统一优化建议 (按优先级排序)

### Tier 0 — 🔴 阻断级: 修复即可立即止损

这些项目独立、无依赖冲突、修复成本低、收益明确。

| # | 建议 | 来源 | 涉及文件 | 预计节省 |
|---|------|------|---------|---------|
| **U1** | **删除 active 目录中与 _deprecated/ 重复的 4 个 Skill 文件** | Cost §五.3 | `skills/knowledge/knowledge-extractor.md`, `skills/knowledge/knowledge-precipitation.md`, `skills/reporting/progress-report.md`, `skills/reporting/test-summary.md` | ~3,435 tokens 纯冗余消除 |
| **U2** | **修复 CLAUDE.md 路径** — `tools/check_sop_gate.py` → `ZJSN_Test-master526/tools/check_sop_gate.py` | SOP §E3 | [CLAUDE.md](../../../CLAUDE.md) | 消除错误引用 |
| **U3** | **SOP_STATUS 位置统一** — 仅保留 `artifacts/sop-status/`，删除 modules/ 下的副本 | SOP §B2 + Cost §五.4 | `context/projects/web-automation/modules/<m>/SOP_STATUS_*.json` | ~1,500 tokens + 消除歧义 |
| **U4** | **删除 `source-of-truth.md` 第 17 行或第 15 行** — 两者互斥，必须选择: JSON 还是 SQLite 是权威状态源 | SOP §B3 | [source-of-truth.md](source-of-truth.md) | 消除文档自相矛盾 |

> ⚠️ **U4 决策点**: 建议保留 LangGraph checkpoint (SQLite) 为权威源，SOP_STATUS JSON 降级为人类可读导出。理由: checkpoint 支持时间旅行、自动写入、完整 State 序列化。SOP 审计 F4.18 与此一致。

---

### Tier 1 — 🟠 高优先级: 解决一个根因，同时修复两份审计的多个症状

这些项目虽然改动范围更大，但一次修改同时解决 SOP 和 Cost 两方面的问题。

| # | 建议 | 解决的 SOP 问题 | 解决的 Cost 问题 | 涉及文件 |
|---|------|----------------|-----------------|---------|
| **U5** | **统一 Phase 定义单一事实源** — 将 `state.py` 的 `CANONICAL_PHASES` 作为唯一定义，`sop_validator.py` 从 `state.py` import，`agent-definitions.yaml` 引用相同名称。同时更新 `sop-summary.md` 或将其归档 | SOP §B1 (3 套名称), SOP §D1 (8 个无效 Phase), SOP §F1.1 | Cost §五.2 (4-way pipeline 重复), Cost §二 | `state.py`, `sop_validator.py`, `agent-definitions.yaml`, `sop-summary.md` |
| **U6** | **修复 resume 模式 + SOP_STATUS 格式迁移** — `preflight_node` 加载 SOP_STATUS 时添加旧格式→新格式名称映射 (如 `"Phase 0 (Project Init)"` → `"Project Init"`)。同时运行一次性脚本将 4 个旧格式文件标准化 | SOP §C1 (6 文件漂移), SOP §C2 (resume 失效), SOP §F1.2, §F1.3 | — | `sop_graph.py:149-150`, `artifacts/sop-status/*.json` |
| **U7** | **PAGE_INTERFACE.yaml: 修复或移除** — 两个方向二选一: (a) 修改 `page-interface-generator` 提取规则，限制 elements≤5、test_scenarios≤5、不重复 PAGE_CONTEXT 已有内容，使 YAML 真正 ≤200 tokens；或 (b) 废弃 PAGE_INTERFACE.yaml，让 automation-agent 直接读 PAGE_CONTEXT.md。无论选哪个，**更新 `source-of-truth.md` 第 16 行**的"替代下游 Agent 通读 Markdown"声明 | SOP §E1 (PAGE_INTERFACE 被列为门控但实际膨胀) | Cost §五.1 (平均 2,223 tok vs 宣称 200 tok, 9.4× 更大), Cost §七 (最大单项节省 ~140K tok) | `skills/test-design/page-interface-generator.md`, `source-of-truth.md:16`, `page-analysis.md` (如果合并于此) |

> ⚠️ **U7 决策点**: 选项 (a) 保留 PAGE_INTERFACE 作为结构化接口的理念但修复实现。选项 (b) 更彻底 — Cost 审计数据显示 15/15 个检查案例中 PAGE_INTERFACE.yaml 均比 PAGE_CONTEXT.md 更大。如果 PAGE_INTERFACE 不能实现其声称的 token 优化目标，其存在理由就不成立。

---

### Tier 2 — 🟡 中优先级: 架构层面改进

| # | 建议 | 来源 | 涉及文件 |
|---|------|------|---------|
| **U8** | **Gate 检查前置到 CLI 入口** — 在 `aitest graph run` 命令中，先调用 `check_sop_gate.py`，gate blocked → 拒绝执行并给出建议。SOP §F4.17 | SOP §E2 (5 个断裂点) | `aitest/cli/` (graph run 命令), `check_sop_gate.py` |
| **U9** | **统一两条执行路径** — `full-sop.workflow.js` (Claude Code Skill) 改为直接调用 `aitest graph run` CLI，而非独立实现编排逻辑。或反之，保留 JS workflow 但废弃 LangGraph 路径 | SOP §A2 (双路径), SOP §F4.16 | `full-sop.workflow.js`, `.claude/skills/full-sop/SKILL.md` |
| **U10** | **code-consistency-checker 两阶段执行** — 保留 mechanical 模式作为快速门禁，但在 mechanical 通过后新增可选的 LLM review 调用路径（通过 AgentLoop.plan 中的规则触发）。失败应写入 artifacts/ 并标记到 SOP_STATUS | SOP §D2 (review 模式死代码), SOP §F2.6, §F2.7 | `agent_runner.py:1063, 1177-1224` |
| **U11** | **Agent pipeline 文档自动生成** — 让 `agents/README.md` 和 `project-index.yaml` 的 Agent 段从 `agent-definitions.yaml` 自动生成（而非手工维护 4 份独立副本） | SOP §B1 + Cost §五.2 + Cost §八.🔧2 | `agents/README.md`, `project-index.yaml`, 新增生成脚本 |

> ⚠️ **U9 决策点**: 两条路径各有优势 — JS workflow 可在 Claude Code 环境中直接运行 (无需 Python 环境)，LangGraph 支持 checkpoint/时间旅行。如果选择保留 LangGraph，需要解决 "Claude Code 如何触发 Python LangGraph"；如果选择保留 JS workflow，需要为 JS 版本补齐 checkpoint 和 HITL 能力。

---

### Tier 3 — 🟢 清理与优化

| # | 建议 | 来源 | 涉及文件 |
|---|------|------|---------|
| **U12** | **删除 deprecated 顶层状态字段** — `state.py` 中 `current_skill`, `completed_skills`(顶层), `trace_events` 标注 @deprecated 但仍占用状态空间 | SOP §D2 | `state.py:252-253, 273` |
| **U13** | **移除 `use_subgraphs=False` 分支** — 所有 Agent 已统一使用 `make_agent_loop_node` | SOP §D2 | `sop_graph.py:704, 760-761` |
| **U14** | **sop_validator.py 移除 Bug/Report 互斥规则** — 与 `sop_graph.py` 实际执行逻辑矛盾 | SOP §D2 | `sop_validator.py:266-274` |
| **U15** | **excel-exporter.md 拆分** — 22,819 chars → 核心指令 (~5K) + 示例表格 (外置引用) | Cost §四.2, §八.✂️ | `skills/execution/excel-exporter.md` |
| **U16** | **Preflight cache 添加 mtime 失效检查** — 产物变更后缓存自动失效 | SOP §E1 | `sop_graph.py:58-61` |
| **U17** | **check_agent_drift.py 集成 CI** — 在 Jenkinsfile 或 pre-commit hook 中运行 | SOP §F2.9 | `Jenkinsfile`, `.pre-commit-config.yaml` (新建) |
| **U18** | **归档 sop-summary.md** — 18 Phase 定义与实际 9 Phase 代码严重不一致，替换为从 agent-definitions.yaml 自动生成的文档 | SOP §D1 + Cost §五.2 | `workflows/sop-summary.md` |
| **U19** | **标记未连接 Skill** — `api-testing`, `miniapp-testing`, `jenkinsfile-generator` 标记为 experimental 或添加 `status: inactive` | SOP §D3 | `skill-registry.yaml` |
| **U20** | **清理僵尸文件** — `agents/_deprecated/` (4 files), `skills/_deprecated/` (8 files), `_archived/` (10 files) 保留 2 周后删除 | Cost §六 | 多个文件 |
| **U21** | **遍历 .gitignore 确保大文件不提交** — 确认 `trace_log.jsonl` (5.6MB), `.chroma/`, `.graph_state/` 在 .gitignore 中 | Cost §六 | `.gitignore` |

---

## 执行顺序建议

```
Week 1 (止损):
  U1 (删重复文件) → U2 (修路径) → U3 (SOP_STATUS 去重) → U4 (source-of-truth 修正)
  预计: 4 个纯文件操作，无代码逻辑变更，低风险

Week 1-2 (根因修复):
  U5 (统一 Phase 定义) → U6 (修复 resume + 格式迁移)
  └→ 同步进行: U7 (PAGE_INTERFACE 修复/废弃)
  预计: 中度代码变更，需回归测试 resume 模式

Week 2-3 (架构改进):
  U8 (Gate 前置) → U9 (统一执行路径) → U10 (code-consistency reviewer) → U11 (文档自动生成)
  预计: 涉及 CLI 和编排逻辑变更，需充分测试

Week 3+ (清理):
  U12-U21: 低风险清理，可穿插进行
```

---

## 冲突与权衡

### 已识别的冲突

| 冲突 | 涉及建议 | 说明 |
|------|---------|------|
| **JSON vs SQLite 权威源** | U4 ↔ SOP §F4.18 | 两份审计一致建议: SQLite 为主，JSON 为导出。`source-of-truth.md` 应明确声明 checkpoint 为权威源 |
| **PAGE_INTERFACE: 修 vs 废** | U7 | 如果选"废"，则 `page-interface-generator` Skill (skill-registry 中标记为 deprecated 但仍在 page-analysis 后处理中使用) 需要同步更新 |
| **执行路径: JS vs Python** | U9 | 如果选 LangGraph (Python)，`full-sop.workflow.js` 变成薄 wrapper；如果选 JS workflow，需补齐 checkpoint 能力。推荐 LangGraph (已有 checkpoint + HITL) |
| **sop-summary.md 归档时机** | U18 | 依赖 U5 (Phase 定义统一) 先完成，否则归档的是错误文档 |
| **agent-definitions.yaml 作为单一事实源** | U5 + U11 ↔ Cost §五.6 | Cost 审计 §五.6 指出 YAML 与 SKILL.md 内容"完全不同" — U5/U11 解决的是 Phase 定义层，Skill 列表层已有 `check_agent_drift.py` 监控 |

### 无冲突的协同项

这些建议互相增强，无副作用:
- **U5 + U6 + U11**: 统一 Phase 定义 → 修复 resume → 自动生成文档，形成闭环
- **U1 + U3 + U20**: 删除重复 + 统一位置 + 清理僵尸 = 磁盘 + token 双重减负
- **U8 + U10**: Gate 前置到 CLI + code-consistency 报告持久化 → 完整的门禁链路
- **U7 选 (b) + U19**: 废弃 PAGE_INTERFACE + 标记未连接 Skill → 统一清理无效资产

---

## 量化收益预估

| 指标 | 当前 | 优化后 | 来源 |
|------|------|--------|------|
| CANONICAL_PHASES 定义 | 3 套 (state.py, sop_validator.py, YAML) | 1 套 | U5 |
| SOP_STATUS 格式 | 3 种 (新格式/旧格式/混合) | 1 种 | U6 |
| 状态存储源 | 6 个 | 2 个 (checkpoint 主 + JSON 导出) | U4 + U3 |
| resume 模式可用模块 | 0/6 | 6/6 | U6 |
| Agent pipeline 维护副本 | 4 份 | 1 份 (YAML) + 2 自动生成 | U11 |
| 每页面 interface 读取 token | ~2,223 | ~200 (U7a) 或直接读 CONTEXT (U7b) | U7 |
| 纯冗余 Skill 文件 | 4 个 (10,304 chars) | 0 | U1 |
| 死代码路径 | 5 个 (见 SOP §D2) | 0 | U12-U14 |
| 未连接 Skill | 4 个 | 0 (标记 experimental) | U19 |
| 执行编排路径 | 2 条 (JS + Python) | 1 条 | U9 |

---

## 附录: 两份审计的完整交叉引用

| SOP 审计发现 | 对应的 Cost 审计发现 | 关系 |
|-------------|---------------------|------|
| §B1: 3 套 CANONICAL_PHASES | §五.2: 4-way pipeline 重复 | **同一根因**: 无单一事实源 |
| §B2: 6 个并发状态源 | §五.4: SOP_STATUS 双份存储 | **同一根因**: 状态存储无收敛 |
| §B3: source-of-truth 自相矛盾 | §五.2: 循环源引用声明 | **同一根因**: 文档未跟随代码演进 |
| §D3: excel-exporter 未使用 | §四.2: excel-exporter 7,606 tok 大户 | **叠加**: 大且不用 |
| §D1: sop-summary 18 Phase | §五.2: Agent pipeline 4 重定义 | **叠加**: 最旧 + 最冗余的定义 |
| §C1: 6/6 SOP_STATUS 漂移 | §五.4: 双份 SOP_STATUS | **叠加**: 两份都不对 |
| §D2: 5 个死代码路径 | §六: 僵尸文件 29,900 tok | **同位**: 不同层级的废弃资产 |
| §E1: PAGE_INTERFACE 门控声明 | §五.1: PAGE_INTERFACE 9.4× 膨胀 | **矛盾**: SOP 审计记录了设计意图, Cost 审计证明其失败 |

---

*本方案综合了两份独立审计的发现。实施时应按 Tier 顺序推进，每个 Tier 完成后运行现有回归测试 (`pytest script/<m>/test_*.py -v`) 验证无破坏。*
