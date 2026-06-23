# Governance Layer Architecture Design Review

> 版本: v1.0 | 日期: 2026-06-15 | 状态: Architecture Review
> 目标: 评估当前项目是否进入 Governance Engineering 阶段，设计治理层架构蓝图

---

## 执行摘要

**结论: 项目已进入 Governance Engineering 阶段。** 当前系统具备完整的 Capability Layer (Agent + Skill + Graph) 和 Knowledge Layer (Context + RAG + Memory)，但缺少系统化的治理闭环。

**核心发现:**
- 已有基础设施 (Trace/Checkpoint/EventBus/Validator) 足以支撑治理层建设
- 5 个治理子系统中有 3 个已有雏形 (Cost/Evaluation/State)，需升级为正式治理 Agent
- 缺失 2 个关键子系统: Prompt Versioning、SOP Auditor
- P0 优先建设 Prompt Versioning + State Auditor，其余 P1/P2 渐进式建设

---

# Part 1: Prompt Versioning Architecture

## 1.1 当前 Skill Prompt 管理方式

### 现状

```
governance/skills/skill-registry.yaml    ← 注册表 (id, category, status, file, workflows)
governance/skills/<category>/<name>.md  ← Prompt 内容
aitest/llm/skill_loader.py              ← 加载器 (lru_cache, variant-aware)
governance/skills/_variants/            ← 变体目录 (当前为空)
```

**加载链路:**
```
run_skill(skill_id, variant)
  → load_skill(skill_id, variant)
    → _load_skill_cached (lru_cache maxsize=64)
      → 文件系统读取 .md
  → ContextInjector.inject()
  → PromptAdapter.adapt()
  → LLMProvider.complete()
  → TraceEvent (skill_id 已记录)
```

### 1.2 当前问题

| 风险 | 严重度 | 说明 |
|------|--------|------|
| **Prompt 更新不可追踪** | HIGH | `.md` 文件直接修改，无版本号、无 changelog、无 diff 历史 (仅依赖 git) |
| **无法回滚** | HIGH | `lru_cache` 缓存的是文件内容，修改后立即生效，无法按版本回滚 |
| **无法关联历史运行结果** | HIGH | Trace 中 `skill_id="test-design/page-analysis"` 无版本后缀，无法区分 v1.0 vs v1.1 的输出差异 |
| **变体系统未激活** | MEDIUM | `skill-registry.yaml` 中 `variants: []` 为空，`_variants/` 目录仅有 `.gitkeep` |
| **A/B 测试无基础设施** | MEDIUM | `ab_test.py` 存在但 skill_loader 未集成 A/B 分流逻辑 |
| **跨 Skill 依赖无版本约束** | LOW | Skill A 输出格式变更时，下游 Skill B 无感知 |

**具体场景:**
1. 修改 `test-design/page-analysis.md` 的 Prompt 模板后，之前的 SOP 运行记录中的 `skill_id` 完全相同，无法判断那次运行用的是旧 Prompt 还是新 Prompt
2. 如果新 Prompt 导致输出质量下降，唯一回滚方式是 `git revert`，无法在运行时切换到旧版本
3. `skill-registry.yaml` 中没有 `version` 字段，`PromptVariant` dataclass 的 `version` 字段未被 registry 填充

### 1.3 推荐方案: Skill Version Model

```
skill_id: "test-design/page-analysis"
  ├── @v1.0  (2026-05-01) → governance/skills/test-design/page-analysis-v1.0.md
  ├── @v1.1  (2026-05-20) → governance/skills/test-design/page-analysis-v1.1.md
  ├── @v2.0  (2026-06-10) → governance/skills/test-design/page-analysis-v2.0.md
  └── @latest (alias → v2.0)
```

**Version Schema:**

```yaml
# skill-registry.yaml 扩展
skills:
  - id: "test-design/page-analysis"
    category: "test-design"
    status: "active"
    current_version: "2.0"          # ← 新增: 当前生产版本
    versions:                        # ← 新增: 版本历史
      - version: "2.0"
        file: "skills/test-design/page-analysis-v2.0.md"
        released: "2026-06-10"
        changelog: "增加 Element Plus 3.x 适配规则; 缩减 token 15%"
        status: "active"
      - version: "1.1"
        file: "skills/test-design/page-analysis-v1.1.md"
        released: "2026-05-20"
        changelog: "修复定位器优先级排序逻辑"
        status: "deprecated"
      - version: "1.0"
        file: "skills/test-design/page-analysis-v1.0.md"
        released: "2026-05-01"
        changelog: "初始版本"
        status: "archived"
```

**加载行为:**
- `load_skill("test-design/page-analysis")` → 加载 `current_version` (v2.0)
- `load_skill("test-design/page-analysis", version="1.1")` → 加载 v1.1 (明确指定)
- `load_skill("test-design/page-analysis@v1.0")` → 加载 v1.0 (短语法)
- `TraceEvent.skill_id` → 记录为 `"test-design/page-analysis@v2.0"` (版本固化)

### 1.4 Trace Integration

**TraceEvent 扩展字段:**

```python
# 当前 TraceEvent 已有:
skill_id: str = ""              # "test-design/page-analysis"

# 建议扩展 (metadata 中已有容量):
# metadata 中新增:
#   "skill_version": "2.0"      # ← 新增: Prompt 版本号
#   "agent_version": "2.0"      # ← 新增: Agent 定义版本号
#   "skill_registry_version": "0.3"  # ← 新增: Registry 快照版本
```

**查询能力:**
```bash
# 按版本对比同一 Skill 的表现
aitest trace summary --skill="test-design/page-analysis" --version="1.1"
aitest trace summary --skill="test-design/page-analysis" --version="2.0"

# 版本间对比 (新增)
aitest trace diff --skill="test-design/page-analysis" --v1="1.1" --v2="2.0"
  # 输出: success_rate: 0.92→0.95, avg_tokens: 3200→2800, avg_latency: 4.2s→3.8s
```

### 1.5 Migration Cost

**评级: LOW**

理由:
- `skill_loader.py` 已有 `variant` 参数和 `PromptVariant` dataclass，扩展为 `version` 只需改加载路径逻辑
- `skill-registry.yaml` 增加 `current_version` + `versions[]` 字段，向后兼容
- `.md` 文件名从 `page-analysis.md` 改为 `page-analysis-v1.0.md` 是一次性迁移，可写脚本批量处理
- `TraceEvent.metadata` 是 `dict`，加 `skill_version` 无需改 schema
- 预估工作量: 2-3 天 (1 天 registry 扩展 + 1 天 loader 改造 + 1 天迁移脚本)

---

# Part 2: State Auditor Architecture

## 2.1 当前系统状态源

| 状态源 | 存储位置 | 写入者 | 读取者 |
|--------|----------|--------|--------|
| LangGraph State | `SOPState` TypedDict (内存) | 每个 LangGraph 节点 | 节点间传递 |
| Checkpoint | `governance/.graph_state/checkpoints.sqlite` | SqliteSaver | `preflight_node()` 恢复 |
| SOP_STATUS JSON | `governance/artifacts/sop-status/SOP_STATUS_<m>.json` | `exit_node()` | `preflight_node()` 恢复, Gate checker |
| Artifact 文件 | `governance/context/projects/*/modules/*/pages/*/*.md` | AgentLoop.act() | AgentLoop.perceive(), Gate checker |
| Context Document | 同上 | Agent + 人类 | ContextInjector |
| Task | `aitest/tasks.db` (SQLite) | agent_scheduler | agent_scheduler |

## 2.2 已检测到的 State Drift 风险

| 漂移类型 | 场景 | 当前是否有检测 |
|----------|------|----------------|
| **Artifact 存在但 State 未更新** | PageObject .py 已生成，但 SOP_STATUS 仍显示 Phase 3 (Automation) 未完成 | ❌ 无 |
| **State 完成但 Artifact 缺失** | SOP_STATUS 标记 Test Design 完成，但某页面的 TEST_CASES.md 被手动删除 | ⚠️ 部分: Gate checker 检查文件存在性，但非持续监控 |
| **Checkpoint vs JSON 不一致** | SQLite checkpoint 有 Phase 5 记录，但 SOP_STATUS JSON 仅到 Phase 4 (含崩溃恢复路径) | ⚠️ 部分: preflight_node 优先 checkpoint，JSON 为后备 |
| **多 Agent 并发写入冲突** | Knowledge Agent 和 Report Agent 同时写 `governance/artifacts/` | ❌ 无 (当前无并发场景，但 Dev SOP 将来可能) |
| **Phase 跳转但产物不完整** | `skip_phases` 跳过 Test Design 直接进入 Automation，缺少 TEST_CASES.md | ⚠️ 部分: route_next_phase 允许跳转但 Gate checker 会拦截 |
| **Context 文档过期** | PAGE_CONTEXT.md 生成后页面 HTML 已变更，但无过期标记 | ⚠️ 部分: preflight_node 检查 mtime |

**具体漂移场景 (已实际发生):**

```
场景 A: Artifact → State 漂移
  1. automation-agent 成功生成 PageObject + test script
  2. exit_node() 写入 SOP_STATUS 前进程崩溃 (或 AgentLoop.update() 失败)
  3. 结果: .py 文件存在，SOP_STATUS 显示 Automation 未完成
  4. 下次 resume 时 preflight_node 检测到文件存在 → 跳过 Automation → State 跳转正确
  5. 但: 如果 preflight 缓存未失效，可能重复执行 Automation

场景 B: State → Artifact 漂移
  1. SOP_STATUS 显示 Test Design 完成 (phase 通过但某页面产物质量差)
  2. 人工删除质量差的 TEST_CASES.md 准备重新生成
  3. Gate checker 在下次 Automation 前检查到文件缺失 → 拦截 ✓
  4. 但: 如果 SOP_STATUS 已完成且无人重新触发，漂移永久存在
```

## 2.3 State Auditor Agent 设计

### 职责

```
State Auditor Agent (横向贯穿 Agent, 类似 Knowledge Agent)
  ├── 状态一致性检查 (State Consistency Check)
  ├── Artifact 验证 (Artifact Validation)
  ├── 状态漂移检测 (State Drift Detection)
  └── 自动生成审计报告 (Audit Report Generation)
```

### 检查维度

| 维度 | 检查内容 | 触发时机 |
|------|----------|----------|
| **S-Check: State-to-Artifact** | SOP_STATUS 中 completed_phases 的每个 Phase 的预期产物是否都存在且非空 | 每次 Phase 完成后、CycleEnd 时 |
| **A-Check: Artifact-to-State** | 存在超过预期的产物文件 (孤儿文件) | CycleEnd 时 |
| **C-Check: Cross-Source** | SQLite checkpoint vs SOP_STATUS JSON vs 实际文件系统 三者一致性 | 每次 resume 前、定期巡检 |
| **Q-Check: Quality Gate** | 产物文件内容是否满足最低质量标准 (行数、结构标记) | Phase 完成后 |
| **T-Check: Timeline** | Phase 时间戳是否合理 (无未来时间、无倒退、无超长间隔) | CycleEnd 时 |

### 输出: State Audit Report

```yaml
# governance/artifacts/audits/state-audit-<module>-<timestamp>.yaml
module: equipment
audit_time: "2026-06-15T10:30:00"
run_id: "sop-equipment-1718400000"
overall_status: "warning"  # ok | warning | error

checks:
  s_checks:
    - phase: "Test Design"
      status: "ok"
      expected: ["PAGE_CONTEXT.md", "RISK_MODEL.md", "TEST_CASES.md", "TEST_DESIGN.md"]
      found_all: true
    - phase: "Automation"
      status: "error"
      expected: ["page_object.py", "test_script.py"]
      missing: ["page_object.py"]           # ← 发现漂移
      action: "建议重新运行 automation-agent"

  a_checks:
    - type: "orphan_file"
      path: "modules/equipment/pages/camera/TEMP_ANALYSIS.md"
      severity: "low"
      suggestion: "非标准产物，建议归档或删除"

  c_checks:
    - source: "checkpoint_vs_json"
      status: "warning"
      detail: "SQLite 有 Phase 5 记录，JSON 仅到 Phase 4"
      suggestion: "以 SQLite 为准，重新导出 JSON"

  q_checks:
    - file: "modules/equipment/pages/alarm-config/TEST_CASES.md"
      status: "warning"
      issue: "行数 8 < 最低要求 15"
      suggestion: "TEST_CASES.md 内容不完整，建议重新运行 test-design-agent"

  t_checks:
    - phase: "Requirement → Test Design"
      gap_hours: 72.5
      severity: "info"
      detail: "Phase 间隔超过 72 小时，可能已发生上下文丢失"
```

### 集成方式

- **触发点 1**: `exit_node()` → emit `CycleEnd` → EventBus → StateAuditor 订阅者
- **触发点 2**: CLI 手动触发 `aitest audit state --module=<m>`
- **触发点 3**: 定期巡检 (cron: `0 7 * * 1` 每周一早 7 点全量审计)
- **与现有 sop_validator.py 的关系**: State Auditor 复用 `sop_validator.py` 的检查函数 (`validate_sop_state`, `validate_module_full`)，增加跨源对比和自动修复建议

---

# Part 3: SOP Auditor Architecture

## 3.1 当前 SOP 执行路径

```
START → entry → preflight → cond_route
  → project_agent → requirement_agent → test_design_agent
  → automation_agent_pre → [HITL: approval] → automation_agent_post
  → [P0: testcase_approval]
  → execution_agent → [condition: execution_failed?]
    → YES: bug_analysis_agent → [HITL: fix approval] → loop(max 3)
    → NO:  skip
  → data_sanitization_agent
  → report_agent → knowledge_agent → exit → END
```

**Phase 跳转逻辑:** `route_next_phase()` 根据 `completed_phases + skip_phases + execution_failed` 决定下一节点。

## 3.2 已检测到的 SOP 合规风险

| 风险 | 场景 | 当前检测 |
|------|------|----------|
| **Phase 被跳过但未记录原因** | `skip_phases` 包含 "Test Design"，但无审计记录说明为什么跳过 | ❌ |
| **Gate 虚拟通过** | Gate checker 检查文件存在性，但文件内容为空或为模板占位符 | ⚠️ 部分: sop_validator 有内容标记检查但未强制执行 |
| **Agent 绕过 SOP** | 直接调用 `AgentLoop('automation-agent', module='x').run()` 不经过 SOP Graph | ❌ 无检测 |
| **HITL 审批未真正执行** | 用户连续 skip 所有 HITL 节点，SOP 退化为全自动 | ❌ |
| **循环次数超限但未升级** | Bug fix 循环 max 3 次，3 次均失败后静默跳过 | ⚠️ 日志有记录但无告警 |
| **Phase 执行顺序异常** | Knowledge Agent 在 Execution 之前被触发 (EventBus 异步触发) | ❌ |

**具体风险场景:**

```
场景 C: Agent 绕过 SOP
  1. 开发者直接运行:
     python -c "from aitest.agent_runner import AgentLoop; \
                AgentLoop('automation-agent', module='equipment', page='alarm-config').run()"
  2. automation-agent 成功生成代码
  3. 但: SOP_STATUS 未更新，SOP Graph 不知道这步已完成
  4. 后续通过 SOP Graph 运行时 preflight_node 可能检测到产物 → 跳过
  5. 但: 如果产物质量差，无法追溯是 SOP 内还是 SOP 外生成的

场景 D: Gate 虚拟通过
  1. test-design-agent 生成 TEST_CASES.md，内容仅为:
     "# Test Cases\n\n待补充"
  2. Gate checker: file_exists + file_nonempty (50 bytes) → 通过 ✓
  3. 实际: 无任何测试用例，下游 automation-agent 基于空用例生成代码
  4. 结果: 生成的测试脚本覆盖率为 0
```

## 3.3 SOP Auditor Agent 设计

### 职责

```
SOP Auditor Agent
  ├── SOP Compliance Check   (SOP 合规检查)
  ├── Phase Coverage Analysis (Phase 覆盖率分析)
  ├── Gate Verification       (Gate 有效性验证)
  └── Workflow Path Audit     (工作流路径审计)
```

### 检查维度

| 维度 | 检查内容 | 数据源 |
|------|----------|--------|
| **P-Check: Phase Sequence** | 实际执行的 Phase 顺序是否符合 CANONICAL_PHASES 前缀规则 | LangGraph checkpoint + Trace |
| **S-Check: Skip Audit** | 每个 skip 的 Phase 是否有明确的 skip_reason 记录 | SOP_STATUS JSON |
| **G-Check: Gate Effectiveness** | Gate 通过率 vs 下游失败率。如果 Gate 100% 通过但下游 40% 失败 → Gate 无效 | Trace (gate_results + agent status) |
| **H-Check: HITL Integrity** | HITL 审批节点的 approve/reject/skip 比例。skip 率 > 80% 告警 | LangGraph interrupt 记录 |
| **B-Check: Bypass Detection** | 检测在 SOP Graph 外部直接调用 AgentLoop 的情况 (run_id 不在任何 SOP 运行中) | Trace (run_id 模式匹配) |
| **L-Check: Loop Health** | Bug fix 循环统计: 平均循环次数、首次修复成功率、3 次均失败率 | Trace + bug_analysis_graph checkpoint |

### 输出: SOP Audit Report

```yaml
# governance/artifacts/audits/sop-audit-<module>-<timestamp>.yaml
module: equipment
audit_time: "2026-06-15T10:30:00"
period: "2026-06-01 ~ 2026-06-15"
overall_compliance: 0.85  # 85%

compliance:
  p_check:
    runs_total: 4
    normal_path: 3          # 按 CANONICAL_PHASES 顺序执行
    skip_path: 1            # 有 Phase 被跳过
    abnormal_path: 0        # Phase 逆序或跳跃
    violations: []

  s_check:
    skipped_phases:
      - run_id: "sop-equipment-1718200000"
        phase: "Bug Analysis"
        has_reason: false   # ← 违规
        severity: "medium"

  g_check:
    gates:
      - gate: "test_design→automation"
        total_checks: 12
        passed: 12              # 100% 通过
        downstream_failures: 3  # 25% 失败 ← Gate 可能过于宽松
        effectiveness: 0.75
        suggestion: "建议增加内容级 Gate 检查 (sop_validator content_check)"

  h_check:
    hitl_nodes:
      - node: "automation_strategy_approval"
        approve: 2
        reject: 0
        skip: 6              # ← 75% skip 率
        severity: "warning"
        suggestion: "HITL 审批被频繁跳过，建议检查是否有流程问题"

  b_check:
    bypass_events:
      - agent: "automation-agent"
        run_id: "standalone-abc123"
        module: "equipment"
        page: "camera"
        timestamp: "2026-06-14T15:22:00"
        severity: "low"
        note: "该 Agent 在 SOP Graph 外部执行，SOP_STATUS 未同步"

  l_check:
    bug_fix_loops:
      total_incidents: 8
      avg_cycles: 1.4
      first_fix_success: 5    # 62.5%
      exhausted_cycles: 1     # 12.5% - 3 次均失败
```

### 集成方式

- **数据采集**: 从 `trace_log.jsonl` + `checkpoints.sqlite` + `SOP_STATUS_*.json` 三个数据源聚合
- **触发点 1**: 每次 `exit_node()` 后自动执行轻量版 (仅 P-Check + B-Check)
- **触发点 2**: CLI `aitest audit sop --module=<m> --period=7d`
- **触发点 3**: 每周全量审计 (与 State Auditor 同频)

---

# Part 4: Evaluation Framework

## 4.1 当前 evaluator.py 能力边界

### 已有能力

| 能力 | 实现 | 局限 |
|------|------|------|
| **Rule-Based Evaluation** | `_score_response()` 确定性打分 | 仅检查表面特征 (长度/关键词/结构/正则) |
| **Metric Aggregation** | `metric_from_traces()` 从 Trace 聚合 | 仅统计 success/error/tokens，无质量维度 |
| **Regression Test** | `regression.py` + baseline 文本相似度 | 相似度算法简陋 (`_text_similarity` = 单词重叠系数) |
| **Agent Run Eval** | `EvalRunner.run_agent()` 收集 Observation | 仅记录 token/latency/artifact_count |

### 缺失能力

| 能力 | 说明 | 优先级 |
|------|------|--------|
| **LLM-as-Judge** | 用 LLM 评估 LLM 输出质量 (语义正确性、逻辑一致性) | P1 |
| **Regression Evaluation** | 结构化回归测试，Prompt 变更后自动检测退化 | P1 |
| **Prompt Benchmark** | 同一输入跑多个 Prompt 版本/变体，横向对比 | P2 |
| **Agent Benchmark** | 端到端 Agent 任务基准测试 (成功率/效率/成本) | P2 |
| **Human-in-the-loop Eval** | 人工评分接口，收集人类反馈作为 Golden Standard | P2 |

## 4.2 推荐: Evaluation Framework 设计

### 架构

```
Evaluation Framework
├── Dataset Layer       ← 测试数据集管理
├── Judge Layer         ← 评分器 (Rule + LLM + Human)
├── Regression Layer    ← 回归测试 + 基线管理
└── Benchmark Layer     ← 基准测试套件
```

### Dataset Layer

```
governance/tests/
├── datasets/
│   ├── page-analysis/
│   │   ├── case-001-input.html        ← 输入: 页面 HTML
│   │   ├── case-001-golden.md         ← Golden Output: 预期 PAGE_CONTEXT
│   │   ├── case-001-criteria.yaml     ← 评分标准
│   │   └── ...
│   ├── tech-analysis/
│   ├── test-script-generator/
│   └── ...
├── regression/
│   ├── test_cases.yaml                ← 已有
│   └── baselines/                     ← 已有
└── benchmarks/
    ├── agent-bench/
    │   ├── task-001.yaml              ← 端到端任务定义
    │   └── ...
    └── prompt-bench/
        ├── compare-config.yaml        ← 多版本对比配置
        └── ...
```

**Dataset 格式:**
```yaml
# case-001-criteria.yaml
id: "page-analysis-001"
skill_id: "test-design/page-analysis"
input:
  html_file: "case-001-input.html"
  context:
    module: "equipment"
    page: "alarm-config"
golden:
  output_file: "case-001-golden.md"
criteria:
  rule_based:
    min_length: 500
    contains: ["元素清单", "定位器", "交互模式"]
    structure: ["## 页面概述", "## 元素清单", "## 交互流程"]
  llm_judge:
    enabled: true
    dimensions: ["completeness", "accuracy", "actionability"]
    prompt: "评估这份 PAGE_CONTEXT 文档..."
```

### Judge Layer

```
Judge 类型:
  1. RuleJudge       ← 已有 (_score_response) — 快速、确定性、零成本
  2. LLMJudge        ← 新增 — 语义评估、多维度打分
  3. HumanJudge      ← 新增接口 — 人工评分收集
  4. CompositeJudge  ← 组合多个 Judge，加权求和
```

**LLM-as-Judge 设计:**
```python
@dataclass
class LLMJudgeConfig:
    judge_model: str = "claude-haiku-4-5"  # 用小模型降成本
    dimensions: list[str] = None           # ["accuracy", "completeness", ...]
    rubric: str = ""                       # 评分标准描述
    aggregation: str = "min"               # min | avg | weighted

# 用法:
judge = LLMJudge(config)
result = judge.evaluate(
    output=actual_content,
    golden=golden_content,
    criteria=criteria,
)
# result: {accuracy: 0.9, completeness: 0.85, overall: 0.85, reasoning: "..."}
```

**适合本地实现 vs LangSmith:**

| 能力 | 本地实现 | LangSmith |
|------|----------|-----------|
| RuleJudge | ✅ 已实现 | ❌ 不需要 |
| LLMJudge (单条) | ✅ 推荐本地实现 | 可替代，但增加外部依赖 |
| LLMJudge (批量) | ✅ 本地 batch | ✅ LangSmith 更适合批量实验管理 |
| Regression 基线对比 | ✅ 已有 (`regression.py`) | ✅ LangSmith Dataset + Experiment |
| Prompt Benchmark | ⚠️ 可实现但 UI 弱 | ✅ LangSmith Hub + Comparator |
| Agent Benchmark | ⚠️ 可实现但无 tracing UI | ✅ LangSmith Tracing + Annotation |
| Human Feedback 收集 | ⚠️ 需自建 UI | ✅ LangSmith Annotation Queue |

**建议:**
- **本地实现**: RuleJudge + LLMJudge (单条) + Regression baseline + Dataset 管理
- **LangSmith (可选)**: Prompt Benchmark + Agent Benchmark + Human Feedback (如果进入持续优化阶段)

### Regression Layer

升级现有 `regression.py`:

```
当前: 单词重叠系数 (_text_similarity) → 阈值 0.2
升级:
  1. 结构化 Diff: 按 Markdown section 对比而非全文
  2. Semantic Similarity: 用 embedding 计算语义相似度 (复用 rag_engine 的 ChromaDB)
  3. Criteria Regression: 新输出必须通过相同 criteria 且分数不下降 > 10%
  4. Regression Gate: Prompt 变更后自动触发回归测试，不通过则阻止发布
```

### Benchmark Layer

```
Agent Benchmark:
  - 定义标准任务 (如 "为 equipment/alarm-config 生成 PageObject")
  - 固定输入 (相同的 PAGE_CONTEXT + TECH_ANALYSIS)
  - 多次运行 → 统计成功率、平均耗时、token 消耗、代码可执行率

Prompt Benchmark:
  - 同一 Skill 的多个版本/变体跑相同数据集
  - 输出对比矩阵: version × metric
  - 自动推荐最优版本
```

---

# Part 5: Cost Auditor

## 5.1 当前 trace.py + cost_advisor.py 能力

### 已有能力

| 能力 | 位置 | 成熟度 |
|------|------|--------|
| **Cost Breakdown** | `get_trace_summary()` — 按事件类型/Skill 聚合 | ✅ 完整 |
| **Token Statistics** | `get_run_stats()` — 单次运行 token 分布 | ✅ 完整 |
| **Cost Leaderboard** | `get_cost_leaderboard()` — 按 Agent 排行 | ✅ 完整 |
| **异常检测 (规则引擎)** | `cost_advisor.analyze_trace_data()` — 6 条规则 | ⚠️ 基础 |
| **模型定价表** | `MODEL_PRICING` — Anthropic/OpenAI/DeepSeek/本地 | ✅ 完整 |

### cost_advisor 现有规则:

1. `expensive_agent`: 某 Agent 占总成本 > 50% → HIGH
2. `skill_retry_storm`: Skill 执行次数 > 预期 × 3 → HIGH
3. `high_context_per_skill`: 平均 context_chars > 3000 → MEDIUM
4. `low_cache_hit_rate`: 缓存命中率 < 50% → MEDIUM
5. `high_decision_ratio`: agent_decision > 20% LLM 调用 → MEDIUM
6. `stale_page_interface`: PAGE_INTERFACE 缺失或过期 → LOW

## 5.2 缺失能力

| 能力 | 说明 | 优先级 |
|------|------|--------|
| **Context 膨胀检测** | 检测 Prompt 上下文随 Phase 推进而持续膨胀的趋势 | P1 |
| **Skill 成本趋势** | 同一 Skill 的 token 消耗随时间的变化趋势 (版本升级后是否更贵) | P1 |
| **异常 spike 告警** | 单次 token 消耗超过历史均值 3σ 时主动告警 | P1 |
| **成本预测** | 基于历史数据预测下一次 SOP 运行的预期成本 | P2 |
| **跨模型成本对比** | 同一 Skill 在不同模型上的成本/质量对比 (claude vs deepseek vs gpt) | P2 |
| **成本归因到 Prompt Section** | 分析 Prompt 的哪个部分 (system/user/context) 消耗 token 最多 | P2 |

## 5.3 Cost Auditor Agent 设计

### 职责

```
Cost Auditor Agent
├── Token 异常检测       (Spike Detection — 统计方法)
├── Context 膨胀检测     (Context Bloat Detection — 趋势分析)
├── Skill 成本分析       (Per-Skill Cost Trend)
├── Agent 成本分析       (Per-Agent Cost Trend)
└── 成本优化建议         (Optimization Recommendations)
```

### 核心检查

**Context 膨胀检测 (P1):**

```
场景: SOP 运行中，每个 Phase 的 context_chars 逐渐增加
  Phase 0 (Project):   2,000 chars
  Phase 0.5 (Req):     4,000 chars
  Phase 1 (TestDesign): 8,000 chars
  Phase 3 (Automation): 22,000 chars  ← 膨胀 11×
  Phase 4.5 (Execution): 25,000 chars

检测:
  1. 计算膨胀系数: token_phase_n / token_phase_0
  2. 阈值: > 5× 告警, > 10× 严重
  3. 归因: 哪些 context 文件贡献了膨胀 (file-by-file breakdown)
  4. 建议: 精简 PAGE_CONTEXT (用 PAGE_INTERFACE.yaml 替代), 清理冗余引用
```

**异常 Spike 检测 (P1):**

```
方法: 滚动窗口 Z-score
  - 为每个 Skill 维护历史 token 分布 (mean, std)
  - 当 token > mean + 3σ 时触发告警
  - 自动 Tag: "可能原因: 新页面元素过多 | Prompt 未正确截断 | RAG 检索过多"
```

### 输出: Cost Audit Report

```yaml
# governance/artifacts/audits/cost-audit-<timestamp>.yaml
period: "2026-06-08 ~ 2026-06-15"
total_cost: 4.32  # USD

alerts:
  - severity: "high"
    type: "spike"
    skill: "diagnosis/bug-analysis"
    run_id: "sop-equipment-1718500000"
    tokens: 45000
    baseline_mean: 18000
    z_score: 4.2
    suggestion: "该次 bug-analysis 消耗 2.5× 平均 token，检查是否触发了过多 RAG 检索"

  - severity: "medium"
    type: "context_bloat"
    module: "warehouse"
    phase_0_tokens: 2100
    phase_3_tokens: 18500
    inflation_ratio: 8.8
    top_contributors:
      - file: "modules/warehouse/MODULE_CONTEXT.md"
        chars: 8500
        suggestion: "MODULE_CONTEXT 过长，建议拆分到 PAGE_CONTEXT"
      - file: "knowledge/pitfalls/element-plus/el-dialog-multi-instance.md"
        chars: 3200
        suggestion: "该知识条目被注入到所有 automation skill，确认是否必要"

trends:
  - skill: "automation/tech-analysis"
    period_avg_tokens: 4200
    prev_period_avg: 3800
    change: "+10.5%"
    note: "v2.0 升级后 token 消耗增加，建议评估质量提升是否值得额外成本"

optimizations:
  - type: "model_selection"
    skill: "knowledge/knowledge-manager"
    current_model: "claude-sonnet-4-6"
    suggested_model: "claude-haiku-4-5"
    est_saving: "60%"
    risk: "low"
    rationale: "知识管理任务复杂度低，Haiku 足以胜任"
```

### 与现有 cost_advisor.py 的关系

- `cost_advisor.py` → 升级为 Cost Auditor Agent 的规则引擎子模块
- 增加: 趋势分析 (时间序列)、统计异常检测、跨周期对比
- 保持: 现有 6 条规则作为快速检查层

---

# Part 6: Governance Layer Blueprint

## 6.1 四层架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Test Platform v1.0                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Governance Layer (治理层)                    │   │
│  │                                                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │ Prompt   │ │ State    │ │ SOP      │ │ Eval     │   │   │
│  │  │ Version  │ │ Auditor  │ │ Auditor  │ │ Framework│   │   │
│  │  │ Manager  │ │          │ │          │ │          │   │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │   │
│  │       │            │            │            │          │   │
│  │  ┌────┴────────────┴────────────┴────────────┴─────┐    │   │
│  │  │              Cost Auditor                        │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │         Governance Event Bus (扩展)              │    │   │
│  │  │  PromptChanged | StateDrift | SOPViolation      │    │   │
│  │  │  EvalRegressed | CostAnomaly | AuditCompleted   │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Knowledge Layer (知识层)                     │   │
│  │                                                         │   │
│  │  Context/  │  RAG       │  Memory    │  Artifacts/      │   │
│  │  (57 docs) │  (ChromaDB)│  (.jsonl)  │  (audits/)       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Capability Layer (能力层)                    │   │
│  │                                                         │   │
│  │  Agent(17) │  Skill(56) │  Graph(4) │  MCP(2)          │   │
│  │  Runner    │  Loader    │  Runner   │  Server           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Infrastructure Layer (基础设施层)              │   │
│  │                                                         │   │
│  │  Trace     │  Checkpoint│  EventBus  │  Guardrails      │   │
│  │  (JSONL)   │  (SQLite)  │  (Files)   │  (Validators)    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 6.2 Governance Layer 详细架构

```
Governance Layer
├── 1. Prompt Version Manager
│   ├── Version Registry (skill-registry.yaml 扩展)
│   ├── Version Loader (skill_loader.py 扩展)
│   ├── Migration Tool (批量升级/回滚)
│   ├── A/B Test Engine (变体分流)
│   └── Trace Integration (skill_id@version 记录)
│
├── 2. State Auditor Agent
│   ├── S-Check: State-to-Artifact 一致性
│   ├── A-Check: Artifact-to-State (孤儿文件)
│   ├── C-Check: Cross-Source (checkpoint vs JSON vs FS)
│   ├── Q-Check: Quality Gate 验证
│   ├── T-Check: Timeline 合理性
│   └── Auto-Repair: 可修复漂移的自动纠正
│
├── 3. SOP Auditor Agent
│   ├── P-Check: Phase Sequence 合规
│   ├── S-Check: Skip Audit
│   ├── G-Check: Gate Effectiveness
│   ├── H-Check: HITL Integrity
│   ├── B-Check: Bypass Detection
│   └── L-Check: Loop Health
│
├── 4. Evaluation Framework
│   ├── Dataset Layer (输入+Golden+Criteria)
│   ├── Judge Layer (Rule + LLM + Human + Composite)
│   ├── Regression Layer (结构化回归 + 退化检测)
│   └── Benchmark Layer (Agent Bench + Prompt Bench)
│
├── 5. Cost Auditor Agent
│   ├── Spike Detection (统计异常)
│   ├── Context Bloat Detection (膨胀趋势)
│   ├── Skill/Agent Cost Trend (时间序列)
│   ├── Cross-Model Comparison (模型性价比)
│   └── Optimization Recommendations (降本建议)
│
└── 6. Governance Event Bus (扩展)
    ├── PromptChanged  → 触发强制回归测试
    ├── StateDrift     → 触发 State Auditor
    ├── SOPViolation   → 触发 SOP Auditor
    ├── CostAnomaly    → 触发 Cost Auditor
    ├── EvalRegressed  → 阻止版本发布
    └── AuditCompleted → 沉淀到 knowledge/
```

## 6.3 数据流

```
                  ┌─────────────┐
                  │  SOP Graph  │
                  │  Execution  │
                  └──────┬──────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │  Trace   │   │Checkpoint│   │ Artifact │
   │  JSONL   │   │  SQLite  │   │  Files   │
   └────┬─────┘   └────┬─────┘   └────┬─────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
         ┌─────────────┴─────────────┐
         │   Governance Data Lake    │
         │   (聚合 + 查询层)          │
         └─────────────┬─────────────┘
                       │
     ┌──────┬──────────┼──────────┬──────────┐
     ▼      ▼          ▼          ▼          ▼
  Prompt  State      SOP        Eval       Cost
  Version Auditor   Auditor   Framework  Auditor
     │      │          │          │          │
     └──────┴──────────┴──────────┴──────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Audit Reports  │
              │ (governance/   │
              │  artifacts/    │
              │  audits/)      │
              └────────────────┘
```

## 6.4 事件流

```
┌──────────────────────────────────────────────────────────────┐
│                     Governance Event Flow                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Skill .md 文件变更                                          │
│    │                                                         │
│    ├──→ PromptChanged ──→ 自动触发回归测试                    │
│    │         │                                               │
│    │         ├── 回归通过 → 更新 current_version              │
│    │         └── 回归失败 → EvalRegressed → 阻止发布          │
│    │                                                         │
│  SOP Phase 完成                                              │
│    │                                                         │
│    ├──→ AgentCompleted ──→ State Auditor (S-Check)           │
│    │         │                                               │
│    │         └── 发现漂移 → StateDrift → 自动修复或告警      │
│    │                                                         │
│  SOP Cycle 结束                                              │
│    │                                                         │
│    ├──→ CycleEnd ──→ State Auditor (全量 A/C/Q/T Check)     │
│    │         │                                               │
│    │         ├──→ SOP Auditor (P/S/G/H/B/L Check)           │
│    │         └──→ Cost Auditor (Spike/Bloat/Trend)          │
│    │                                                         │
│  定时巡检 (cron)                                              │
│    │                                                         │
│    └──→ 全量审计 (所有模块 × 所有检查)                       │
│              │                                               │
│              └──→ AuditReport → knowledge/ 沉淀              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 6.5 状态流

```
Governance State Machine (模块级):

  [Idle] ──SOP Start──→ [Running]
                            │
                    ┌───────┴────────┐
                    ▼                ▼
              [Phase Pass]    [Phase Fail]
                    │                │
                    └───────┬────────┘
                            ▼
                      [Checkpoint]
                            │
                    ┌───────┴────────┐
                    ▼                ▼
              [State Auditor]  [SOP Auditor]
              (S/A/C/Q/T)      (P/S/G/H/B/L)
                    │                │
                    ├────────────────┤
                    │                │
                    ▼                ▼
              [Clean]          [Drift Detected]
                    │                │
                    │                ▼
                    │         [Auto-Repair]
                    │                │
                    ├────────────────┤
                    │                │
                    ▼                ▼
              [Audit Report]   [Manual Fix Required]
                    │                │
                    └───────┬────────┘
                            ▼
                      [Idle] / [Resume]
```

---

# Part 7: Roadmap

## P0: Foundation (立即建设 — 2 周)

| 序号 | 子系统 | 内容 | 依赖 | 预估工作量 |
|------|--------|------|------|-----------|
| P0-1 | **Prompt Versioning** | skill-registry 增加 version 字段；loader 支持 `@version` 语法；Trace 记录 `skill_version` | 无 | 3 天 |
| P0-2 | **State Auditor (核心)** | S-Check (State-to-Artifact) + C-Check (Cross-Source)；集成到 `exit_node()` | P0-1 (Trace 需有 version) | 4 天 |
| P0-3 | **Governance Event Bus 扩展** | 新增 `StateDrift` + `SOPViolation` 事件类型；订阅者框架 | 现有 EventBus | 2 天 |
| P0-4 | **Regression Gate** | Prompt 变更后自动触发回归测试；阻止退化版本发布 | P0-1 | 2 天 |

**P0 交付物:**
- Skill 版本化管理 + Trace 可追溯
- State Auditor 自动检测 Artifact-State 漂移
- Prompt 变更 → 自动回归 → Gate 阻止退化

## P1: Enhancement (短期 — 3 周)

| 序号 | 子系统 | 内容 | 依赖 | 预估工作量 |
|------|--------|------|------|-----------|
| P1-1 | **State Auditor (完整)** | A/Q/T Check；自动修复 (可修复漂移)；审计报告生成 | P0-2 | 3 天 |
| P1-2 | **SOP Auditor** | P/S/G/H/B/L 全部检查；Phase 覆盖率分析；Bypass 检测 | P0-3 | 5 天 |
| P1-3 | **LLM-as-Judge** | Judge 框架 (Rule + LLM + Composite)；Golden Dataset 管理 | P0-4 | 4 天 |
| P1-4 | **Cost Auditor (异常检测)** | Spike Detection (Z-score)；Context Bloat Detection；成本趋势 | 现有 Trace/Cost | 3 天 |

**P1 交付物:**
- 完整 State Auditor (6 维检查 + 自动修复)
- SOP Auditor 全量合规审计
- LLM-as-Judge 评估 + Golden Dataset
- Cost 异常检测 + 膨胀检测

## P2: Maturity (中期 — 4 周)

| 序号 | 子系统 | 内容 | 依赖 | 预估工作量 |
|------|--------|------|------|-----------|
| P2-1 | **Prompt Benchmark** | 多版本/多变体对比矩阵；自动推荐最优版本 | P0-1, P1-3 | 5 天 |
| P2-2 | **Agent Benchmark** | 端到端 Agent 任务基准；成功率/效率/成本三维评估 | P1-3 | 5 天 |
| P2-3 | **Cost Auditor (完整)** | 成本预测模型；跨模型性价比对比；成本归因到 Prompt Section | P1-4 | 4 天 |
| P2-4 | **Human Feedback Loop** | 人工评分接口；Human-as-Judge；反馈数据闭环 | P1-3 | 3 天 |
| P2-5 | **Governance Dashboard** | 治理面板 UI (chat.html 扩展)；实时漂移/合规/成本监控 | P1-1~P1-4 | 5 天 |

**P2 交付物:**
- Prompt/Agent Benchmark 套件
- 成本预测 + 跨模型对比
- Human Feedback 闭环
- 治理监控面板

## 优先级决策矩阵

```
                    影响面
              高      中      低
          ┌───────┬───────┬───────┐
    高    │ P0-1  │ P0-2  │ P1-3  │
          │ P0-3  │ P0-4  │       │
风        ├───────┼───────┼───────┤
    中    │ P1-1  │ P1-2  │ P2-1  │
险        │ P1-4  │       │ P2-4  │
          ├───────┼───────┼───────┤
    低    │ P2-2  │ P2-3  │ P2-5  │
          └───────┴───────┴───────┘
```

**P0 理由:**
- Prompt Versioning (P0-1): **当前最高风险** — 所有 Skill 无版本号，无法回滚，无法关联历史。影响面覆盖全部 56 个 Skill 和所有历史运行记录。
- State Auditor 核心 (P0-2): **质量基石** — State Drift 已实际发生 (场景 A/B)，当前靠人工发现。
- Governance Event Bus (P0-3): **架构依赖** — P1 的 SOP Auditor 和 Cost Auditor 依赖事件驱动触发。
- Regression Gate (P0-4): **变更安全** — Skill 数量 56 且持续迭代，没有自动化回归门禁意味着每次 Prompt 修改都是"盲飞"。

---

## 附录: 现有基础设施就绪度评估

| 组件 | 就绪度 | 治理层复用方式 |
|------|--------|---------------|
| Trace (JSONL) | ✅ 100% | State/SOP/Cost Auditor 的数据源 |
| Checkpoint (SQLite) | ✅ 100% | State Auditor 的 C-Check 对比源 |
| EventBus | ✅ 80% | 扩展事件类型 → Governance Event Bus |
| Validator (sop_validator.py) | ✅ 90% | State/SOP Auditor 复用检查函数 |
| Eval (evaluator.py) | ⚠️ 50% | 升级为 Evaluation Framework 的 RuleJudge 层 |
| Cost (trace.py + cost_advisor.py) | ⚠️ 60% | 升级为 Cost Auditor 的规则引擎 + 统计层 |
| Regression (regression.py) | ⚠️ 40% | 升级为 Regression Layer (结构化 diff + 语义相似度) |
| Skill Loader | ⚠️ 70% | 已有 variant 参数，扩展为 version 支持 |
| Skill Registry (YAML) | ⚠️ 60% | 增加 version 字段，向后兼容 |
| MCP Server | ✅ 80% | 可暴露 Governance API 给外部消费者 |
| RAG (ChromaDB) | ✅ 90% | 治理报告可索引；Semantic Similarity 复用 embedding |

**总评: 基础设施就绪度 72%。** 核心痛点不在"缺少基础能力"，而在"缺少系统化的治理闭环"。当前所有组件独立工作良好，但缺乏跨组件的审计、验证和反馈链路。Governance Layer 的建设本质上是**将这些孤立的可观测性组件连接成治理闭环**。
