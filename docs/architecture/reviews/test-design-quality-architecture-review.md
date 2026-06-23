# Test Design Quality — Architecture Review

> AI Platform Architect 视角。不设计 Skill，不写代码，不新增 Agent。
> 先定位问题属于哪一层，再决定实现方案。

---

# Part 1: Current Architecture Analysis

## 1.1 数据流：Page Analysis → Risk Modeling → Testcase Design

```
Page Analysis (page-analysis)
  INPUT:  截图 / HTML 源码 / MODULE_CONTEXT
  OUTPUT: PAGE_CONTEXT.md (UI 元素清单: 搜索区/表格/弹窗/权限点)
  NATURE: 静态 UI 结构枚举
    ↓
Risk Modeling (risk-modeling)
  INPUT:  PAGE_CONTEXT.md / MODULE_CONTEXT / 历史缺陷
  OUTPUT: RISK_MODEL.md (6 维度风险: 业务/权限/数据/接口/UI-UX/性能)
  NATURE: UI 元素的潜在故障模式分析
    ↓
Testcase Design (testcase-design)
  INPUT:  PAGE_CONTEXT.md / RISK_MODEL.md
  OUTPUT: TEST_DESIGN.md + TEST_CASES.md
  NATURE: 将风险映射到 8 个 UI 操作维度的测试场景
```

## 1.2 "测试设计完成"的判定机制

系统通过三层机制判定"测试设计完成"：

| 层 | 机制 | 文件位置 | 语义 |
|---|------|---------|------|
| L1 Orchestrator | `"Test Design" ∈ completed_phases` | `state.py:214-266` | AgentLoop 跑完无 fatal error |
| L2 Agent | `AgentResult.success = True` | `agent_runner.py:72-85` | 技能链全部执行完毕 |
| L3 Validator | Q-Check: 文件存在 + min_lines + keyword match | `state_auditor.py:679-743` | 产物文件合乎最低结构标准 |

**关键发现：三层判定全部是结构性判定，零语义判定。**

```
"Test Design" 完成 = 
  PAGE_CONTEXT.md 存在 ∧ lines ≥ 20 ∧ 含"元素""定位"
  ∧ RISK_MODEL.md 存在 ∧ lines ≥ 15 ∧ 含"风险""等级"
  ∧ TEST_DESIGN.md 存在 ∧ lines ≥ 15 ∧ 含"用例""场景"
  ∧ TEST_CASES.md 存在 ∧ lines ≥ 15 ∧ 含"用例""预期"
```

## 1.3 Current Quality Model

系统的实际优化目标（从代码中反推，非文档宣称）：

| 优化目标 | 度量方式 | 实现位置 |
|---------|---------|---------|
| **文件覆盖率** | 每个页面是否有 4 个产物文件 | `state_auditor.py` S-Check |
| **结构完整性** | 产物行数 ≥ 阈值 + 关键词存在 | `state_auditor.py` Q-Check, `QUALITY_MARKERS` |
| **风险覆盖率** | P0 风险 → P0 用例一一对应 | `testcase-design.md` 检查清单 |
| **维度覆盖率** | TEST_DESIGN 是否覆盖 8 个维度 | `testcase-design.md` 检查清单 |
| **自动化覆盖率** | 每个用例是否标注自动化状态 | `testcase-design.md` 检查清单 |
| **按钮覆盖率** | 表格操作列是否每个按钮都有测试 | 隐式（page-analysis 列出按钮 → testcase-design 为每个按钮生成用例） |
| **Phase 覆盖率** | `completed_phases` 是否包含全部 10 个 Phase | `sop_graph.py` route_next_phase |

**系统的真实优化目标 = 产物文件的完备性 × 结构合规性，而非业务场景的覆盖度。**

---

# Part 2: Root Cause Analysis

## 为什么生成的测试用例偏向"新增/编辑/删除/查询"而非"业务流程/业务规则/数据流"？

### P0 — Skill Prompt 的维度设计是 UI 操作分类法

**文件**: `governance/skills/test-design/testcase-design.md:44-82`

```text
### 1. 页面加载与显示
### 2. 搜索与筛选
### 3. 表格操作
### 4. 新增操作         ← 按钮操作
### 5. 编辑操作         ← 按钮操作
### 6. 删除操作         ← 按钮操作
### 7. 权限测试
### 8. 异常场景
```

这 8 个维度是按 **UI 控件的操作类型** 分类的，不是按 **业务目标** 分类的。

当 LLM 收到这 8 个维度的指令时，它自然产出：
- "新增按钮是否可用"
- "编辑弹窗是否回显"
- "删除确认是否弹窗"

而不是：
- "储罐液位超过安全阈值时，报警是否正确触发并流转到处置工单"
- "承包商从入场申请→审批→入场确认→离场记录的完整生命周期"

**这是根因中的根因。Skill Prompt 的结构直接决定了 LLM 的产出结构。**

### P0 — Page Analysis 只输出 UI 结构，不输出业务语义

**文件**: `governance/skills/test-design/page-analysis.md:39-73`

page-analysis 的任务是：
```
1. 页面整体结构：顶部/左侧/主内容区
2. 搜索/筛选区：每个控件类型 + 标签文字 + 按钮
3. 表格/列表区：列标题 + 数据类型 + 操作按钮
4. 分页区
5. 弹窗/对话框
6. 页面状态：加载中/空数据/错误
7. 权限点
```

**全部是 UI 层面的元素枚举。没有问：**
- 这个页面服务于什么业务目标？
- 用户在什么业务流程中到达这个页面？
- 页面数据从哪里来、流向哪里？
- 不同角色在这个页面分别完成什么任务？

page-analysis 是 testcase-design 的输入源。输入只有 UI 结构 → 输出只能是 UI 操作覆盖。

### P1 — Risk Modeling 有业务维度但未被下游消费

**文件**: `governance/skills/test-design/risk-modeling.md:38-82`

risk-modeling 确实定义了 6 个风险维度，包含"业务风险"：
```
### 1. 业务风险
- 误操作导致的数据丢失
- 权限越权
- 业务规则冲突
```

但 testcase-design 的 8 个维度中，并没有 "业务规则验证" 维度。risk-modeling 产出的业务风险，在 testcase-design 阶段被压缩进了 "新增/编辑/删除" 的 UI 操作框架中。

**信息在 Pipeline 中被降维了：**
```
业务风险 "液位超过阈值应触发报警并阻止进液"
  → testcase-design 中变成 "编辑液位字段，输入超阈值值，检查校验提示"
  → 丢失了：报警触发条件、报警流转、进液阀门联锁
```

### P1 — Q-Check 只验证结构不验证语义

**文件**: `aitest/state_auditor.py:550-580`

```python
"TEST_DESIGN.md": {
    "min_lines": 15,
    "markers": ["用例", "场景", "覆盖", "策略"],
    "marker_min_match": 2,
},
```

Q-Check 验证的是"文件中是否包含中文字符串'用例''场景'"，而不是"测试用例是否覆盖了业务规则 X"。

一个只有 UI 操作覆盖的 TEST_DESIGN.md 和一个有完整业务覆盖的 TEST_DESIGN.md，在 Q-Check 下得分完全相同。

### P2 — LLMJudge 存在但未接入 SOP 主流程

**文件**: `aitest/evaluator.py:505-609`

`LLMJudge` 可以对输出进行语义质量评估，支持多维度打分（completeness, accuracy, clarity）。但它只在 `regression.py` 的 `check_prompt_upgrade()` 中使用 —— 用于评估 Skill Prompt 版本升级前后的输出质量，**不用于评估日常 SOP 运行中的测试用例业务覆盖度**。

### P2 — Agent 定义中缺少"业务覆盖"概念

**文件**: `governance/agents/agent-definitions.yaml:73-101`

`test-design-agent` 的描述是 "页面分析、风险建模、测试用例设计"。它的 boundaries 是 "不写代码、不执行测试、不分析 Bug"。没有任何关于"确保业务场景覆盖"的约束或目标。

### Root Cause Summary

| 等级 | 根因 | 位置 |
|------|------|------|
| **P0** | testcase-design Skill 的 8 维度是 UI 操作分类法，不是业务场景分类法 | `skills/test-design/testcase-design.md:44-82` |
| **P0** | page-analysis Skill 只输出 UI 元素清单，不输出业务语义 | `skills/test-design/page-analysis.md:39-73` |
| **P1** | risk-modeling 产出的业务风险在下游 testcase-design 中被降维为 UI 操作 | Data flow: risk-modeling → testcase-design |
| **P1** | Q-Check 是结构性验证（行数+关键词），不是语义性验证 | `state_auditor.py:679-743` |
| **P2** | LLMJudge 存在但未接入 SOP 主流程的质量门禁 | `evaluator.py:505` vs `sop_graph.py` |
| **P2** | Agent 定义中缺少"业务覆盖"作为 Agent 目标或 boundary | `agent-definitions.yaml:73-101` |

---

# Part 3: Business Coverage Architecture

## 业务覆盖应该如何定义

从业务出发，而不是从 UI 出发。正确的层次是：

```
业务目标 (Business Goal)
  ↓ "为什么存在这个模块？"
角色 (Role)
  ↓ "谁在使用？各自完成什么任务？"
流程 (Workflow)
  ↓ "跨页面/跨角色的完整业务过程"
规则 (Business Rule)
  ↓ "什么条件下触发什么行为？"
数据 (Data Flow)
  ↓ "数据从哪里来、经过什么变换、到哪里去？"
页面 (Page)
  ↓ "每个页面在流程中的位置和作用"
UI 操作 (UI Operation)
  ↓ "具体的点击/输入/验证"（最后才到这一层）
```

## Business Coverage Model

### 1. Business Goal Coverage

| 维度 | 定义 | 度量 |
|------|------|------|
| Goal Identification | 每个模块是否识别了核心业务目标？ | 0/1 per module |
| Goal-Test Mapping | 每个业务目标是否有对应的端到端测试场景？ | 映射率 |
| Goal Completeness | 是否存在未被任何测试场景覆盖的业务目标？ | 缺口数 |

**示例**：
- tank 模块目标 = "实时监控储罐液位/压力/温度，异常时触发报警并联动处置"
- → 测试应覆盖 "液位超限 → 报警触发 → 状态变更 → 处置工单生成" 的完整链路
- 当前 TEST_DESIGN 只覆盖了 "编辑液位字段 → 保存" 的点操作

### 2. Role Coverage

| 维度 | 定义 | 度量 |
|------|------|------|
| Role Identification | 是否识别了所有访问该模块的角色？ | 角色列表完整度 |
| Role Journey | 每个角色的完整业务旅程是否有测试？ | journey 覆盖率 |
| Role Permission | 每个角色的权限边界是否有测试？ | ✅ 当前已覆盖 |
| Role Collaboration | 多角色协作流程是否有测试？ | 协作场景数 |

### 3. Workflow Coverage

| 维度 | 定义 | 度量 |
|------|------|------|
| Happy Path | 端到端主流程是否完整覆盖？ | 场景数 |
| Alternative Path | 分支流程是否覆盖？ | 场景数 |
| Exception Path | 异常中断+恢复是否覆盖？ | 场景数 |
| Cross-Page Flow | 跨页面业务流程是否覆盖？ | 跨页面场景数 |
| Cross-Module Flow | 跨模块业务流程是否覆盖？ | 跨模块场景数 |

### 4. Business Rule Coverage

| 维度 | 定义 | 度量 |
|------|------|------|
| Validation Rules | 业务校验规则（非 UI 校验）是否测试？ | 规则覆盖率 |
| State Transition | 业务状态流转是否正确？ | 状态机覆盖率 |
| Calculation Rules | 业务计算逻辑是否正确？ | 计算场景数 |
| Trigger Rules | 触发条件+触发动作是否正确？ | 触发链路数 |

### 5. Data Flow Coverage

| 维度 | 定义 | 度量 |
|------|------|------|
| Data Origin | 数据从哪里创建/导入？ | 数据源覆盖 |
| Data Transformation | 数据在流转中如何变换？ | 变换验证 |
| Data Consumption | 数据最终在哪里被消费/展示？ | 消费点覆盖 |
| Data Consistency | 跨页面/跨模块数据一致性 | 一致性检查数 |

### 6. Cross-Page Coverage

| 维度 | 定义 | 度量 |
|------|------|------|
| Page Dependency | 页面间的数据依赖关系是否测试？ | 依赖链路数 |
| Navigation Flow | 页面间导航是否正确？ | 导航场景数 |
| Shared Data | 共享数据的变更是否在所有页面生效？ | 共享数据场景 |

---

# Part 4: Architecture Placement Review

## 方案 A: 新增 business-scenario-audit Skill（后审计）

**位置**: Test Design 完成后，Automation 之前，作为独立的审计步骤

```
Page Analysis → Risk Modeling → Testcase Design → [Business Scenario Audit] → Automation
```

| 维度 | 评价 |
|------|------|
| 优点 | 低侵入性，不修改现有 Skill；可独立迭代；审计结果可量化 |
| 缺点 | 治标不治本——testcase-design 仍然按 UI 维度产出，审计只能打回重做，增加往返；不改变 LLM 的生成行为 |
| 系统影响 | 新增 1 个 Skill + 1 个 SOP Phase 节点 |
| 治理影响 | 审计结果可作为 GateResult 接入 gate_results |
| Token 成本 | 每个页面额外 ~2000-4000 tokens（审计 prompt + 审计输出） |
| 维护成本 | 低——独立 Skill，审计维度可渐进增强 |
| 扩展性 | 中——只能审计，不能从源头改善生成质量 |

## 方案 B: 增强 risk-modeling + 新增 BUSINESS_SCENARIOS.md（源头改进）

**位置**: risk-modeling 产出新增 BUSINESS_SCENARIOS.md，作为 testcase-design 的必选输入

```
Page Analysis → Risk Modeling → BUSINESS_SCENARIOS.md
                                      ↓
                              Testcase Design (消费 BUSINESS_SCENARIOS)
```

| 维度 | 评价 |
|------|------|
| 优点 | 从源头注入业务上下文；testcase-design 有业务场景可参照；不新增 Agent |
| 缺点 | 改变了 risk-modeling 的职责边界（它原本只输出风险）；testcase-design 的 8 维度仍然未变，只是多了输入；需要修改 2 个 Skill |
| 系统影响 | 修改 risk-modeling Skill + testcase-design Skill + 新增产物类型 |
| 治理影响 | 新增产物需加入 PHASE_EXPECTED_ARTIFACTS + QUALITY_MARKERS |
| Token 成本 | risk-modeling 额外 ~3000 tokens，testcase-design 额外 ~1000 tokens（消费场景） |
| 维护成本 | 中——2 个 Skill 联动修改，后续需保持一致性 |
| 扩展性 | 中——业务场景模型可渐进丰富，但受限于 testcase-design 的 UI 维度框架 |

## 方案 C: 新增 TESTCASE_QUALITY_GATE（治理门禁）

**位置**: Automation 之前，作为 L3 Validator 门禁

```
Test Design → [TESTCASE_QUALITY_GATE] → Automation
                  ↓ 不通过则阻断
```

| 维度 | 评价 |
|------|------|
| 优点 | 硬阻断，强制执行；可量化评分；与现有 3 层门禁架构一致 |
| 缺点 | 纯治理手段，不改善生成质量——门禁只能拒绝，不能指导如何改进；可能成为流程瓶颈 |
| 系统影响 | 新增 GateResult 类型 + 门禁检查函数 + 可能的 HITL 中断 |
| 治理影响 | 最大——新增治理事件、阻断点、审批流程 |
| Token 成本 | LLM-as-Judge 评估每个页面 ~2000-4000 tokens |
| 维护成本 | 中——门禁逻辑需维护，评分标准需校准 |
| 扩展性 | 高——可渐进增加评分维度，可接入 LLMJudge |

## 推荐: 混合方案 B + C（两阶段）

**不推荐纯 A。** 后审计是修补，不改变生成质量。

```
Phase 1 (源头改进 = 方案 B):
  Page Analysis → Risk Modeling → BUSINESS_SCENARIOS.md (NEW)
                                      ↓
                              Testcase Design (增强: 新增"业务场景"维度作为第 9 维)

Phase 2 (治理门禁 = 方案 C):
  Test Design → TESTCASE_QUALITY_GATE (NEW L3 Gate)
                  ↓ score ≥ 60 → Automation
                  ↓ score < 60 → 打回 Test Design 重做 (max 2 rounds)
```

**理由**：
- 方案 B 确保 LLM **生成时**就有业务上下文参照
- 方案 C 确保即使有上下文，**产出质量**也可验证
- B 降低 C 的拒绝率（源头好了，门禁通过率自然高）
- 两个改动独立可交付：B 先上，C 后上

| 阶段 | 改动范围 | 风险 |
|------|---------|------|
| B 先 | risk-modeling Skill + testcase-design Skill + 新产物 | 低——向后兼容，不破坏现有流程 |
| C 后 | State Auditor / SOP Graph + 新门禁事件 | 中——新增阻断点，需 HITL fallback |

---

# Part 5: Governance Impact Analysis

如果引入业务覆盖能力，影响矩阵：

| Component | Impact | Risk | Complexity |
|-----------|--------|------|------------|
| **Skill Registry** | 修改 risk-modeling + testcase-design 2 个 Skill | 低 — 版本化管理，可回滚 | 中 |
| **Agent Definitions** | test-design-agent 新增第 7 个 Skill (business-scenario) 或增强现有 Skill | 低 — YAML 字段新增 | 低 |
| **SOPState** | 可能新增 `business_scenarios_approved` HITL 字段 | 中 — TypedDict 字段新增需兼容 | 低 |
| **SOP Graph** | 可能新增 BUS-SCENARIO 节点 或 增强 TEST-DESIGN 节点的技能链 | 中 — 图结构变更 | 中 |
| **State Auditor** | Q-Check 新增 `BUSINESS_SCENARIOS.md` 质量标记；新增语义质量检查维度 | 中 — 检查逻辑从结构扩展到语义 | 高 |
| **SOP Auditor** | 新增 BSC-Check（业务场景覆盖检查） | 低 — 新检查类型 | 中 |
| **Event Bus** | 新增 `BusinessCoverageInsufficient` 事件类型 | 低 — 事件类型是字符串枚举 | 低 |
| **Regression Gate** | 可新增业务覆盖回归测试用例 | 低 — 纯增量 | 低 |
| **Evaluation** | LLMJudge 需新增 business_coverage 评分维度 | 中 — 需要 golden reference | 高 |
| **Governance KPI** | 新增 Business Coverage Score 指标 | 低 — 纯增量 | 低 |
| **HITL** | 低分时可能需要人工审批（P0 模块已有 HITL 框架） | 中 — 审批节点可复用 | 低 |
| **Context Files** | 可能需要新增 `business-context` 上下文类型 | 低 — 新文件 | 低 |

---

# Part 6: Quality Evaluation Framework

## Test Design Quality Score (0–100)

### 评分模型

```
总分 = Σ(维度分数 × 维度权重)

维度分数 = 该维度下各检查项得分 / 检查项数 × 100
```

### 维度权重

| 维度 | 权重 | 检查项 | 评分方式 |
|------|:----:|------|:---:|
| **Business Coverage** | 25% | 业务目标识别、目标-场景映射、E2E 流程覆盖 | LLM-as-Judge |
| **Role Coverage** | 15% | 角色识别完整度、角色旅程、多角色协作 | 结构+LLM |
| **Workflow Coverage** | 20% | Happy/Alternative/Exception path、跨页面流程 | LLM-as-Judge |
| **Rule Coverage** | 15% | 业务校验规则、状态机、计算逻辑 | LLM-as-Judge |
| **Data Coverage** | 10% | 数据来源、变换、消费、一致性 | 结构+LLM |
| **Automation Readiness** | 10% | 定位器可用性、测试数据具体性、步骤可复现性 | 确定性规则 |
| **Maintainability** | 5% | 用例结构一致性、编号规范性、文档完整性 | 确定性规则 |

### 评分规则

| 分数段 | 等级 | 门禁行为 |
|:---:|------|---------|
| 85–100 | ✅ Excellent | 直接通过 |
| 70–84 | 🟡 Good | 通过，标注改进建议 |
| 60–69 | 🟠 Acceptable | 通过，P0 模块需人工确认 |
| 40–59 | 🔴 Insufficient | **阻断**（非 P0 模块警告） |
| 0–39 | ⛔ Critical | **硬阻断**，打回 Test Design 重做 |

### 确定性规则（不消耗 LLM Token）

```python
STRUCTURAL_CHECKS = {
    "automation_readiness": [
        ("每个用例有具体测试数据", lambda tc: not any("输入XXX" in step for step in tc.steps)),
        ("步骤数 ≥ 2", lambda tc: len(tc.steps) >= 2),
        ("预期结果非空", lambda tc: bool(tc.expected_result)),
    ],
    "maintainability": [
        ("用例编号连续", lambda tcs: _check_sequential_ids(tcs)),
        ("P0 覆盖率 = 100%", lambda tcs: _check_p0_coverage(tcs) >= 1.0),
        ("产物文件 ≥ 4", lambda artifacts: len(artifacts) >= 4),
    ],
}
```

### LLM-as-Judge 维度（消耗 Token）

```yaml
business_coverage:
  prompt: |
    评估测试用例是否覆盖了以下业务维度：
    1. 业务目标：测试用例是否针对页面的核心业务目标设计？
    2. 业务流程：是否覆盖了端到端业务流程而非仅单点操作？
    3. 业务规则：是否验证了关键业务规则而非仅 UI 校验？
    4. 真实场景：测试数据是否反映真实业务场景？
  score: 0.0-1.0

workflow_coverage:
  prompt: |
    评估测试用例是否覆盖了完整工作流：
    1. Happy Path: 主流程是否完整？
    2. Alternative Path: 分支流程是否覆盖？
    3. Exception Path: 异常恢复是否覆盖？
    4. Cross-Page: 跨页面流程是否覆盖？
  score: 0.0-1.0

role_coverage:
  prompt: |
    评估测试用例是否覆盖了角色维度：
    1. 是否识别了所有相关角色？
    2. 每个角色是否有独立测试场景？
    3. 多角色协作流程是否覆盖？
  score: 0.0-1.0
```

### Token 成本估算

| 评估方式 | 每次消耗 | 适用 |
|---------|:-----:|------|
| 确定性规则 | 0 tokens | Automation Readiness + Maintainability (≈15%) |
| LLM-as-Judge (haiku) | ~2000 input + ~500 output | Business + Workflow + Role + Rule + Data (≈85%) |
| **每页面总计** | **~2500 tokens** | — |
| 每模块 (平均 6 页) | ~15000 tokens | — |
| 全量 12 模块 | ~180000 tokens | 一次性，日常仅增量模块 |

---

# Part 7: Governance Integration

## 建议新增的治理事件

### 1. `BusinessCoverageInsufficient`

```yaml
event: BusinessCoverageInsufficient
trigger: TESTCASE_QUALITY_GATE score < 60 (或 P0 模块 < 70)
phase: Test Design → Automation 之间
action: 阻断 → 打回 Test Design 重做
max_rounds: 2
fallback: HITL (人工审批后放行)
subscriber: knowledge-agent (记录 pattern 到 known-issues.yaml)
```

### 2. `WorkflowCoverageInsufficient`

```yaml
event: WorkflowCoverageInsufficient
trigger: 跨页面流程覆盖率为 0 且模块有 ≥ 2 个页面
phase: Test Design → Automation 之间
action: 警告 (不阻断，因为可能该模块页面确实独立)
subscriber: knowledge-agent
```

### 3. `TestDesignQualityRegressed`

```yaml
event: TestDesignQualityRegressed
trigger: 当前 score < 上次同模块 score - 20
phase: Test Design → Automation 之间
action: 警告 + 记录
subscriber: knowledge-agent
```

## 触发阶段

```
CANONICAL_PHASES:
  Project Init
  Requirement
  Test Design        ← 产出 TEST_DESIGN + TEST_CASES
  [QUALITY GATE]     ← NEW: 业务覆盖门禁（L3 Validator）
  Automation         ← 门禁通过后进入
  Execute & Debug
  ...
```

## 与现有门禁架构的对齐

现有 3 层门禁 (`state.py:47-51`):

```python
class GateLevel(Enum):
    L1_ORCHESTRATOR = 1   # Phase 级前后检查
    L2_AGENT = 2          # Agent 边界检查
    L3_VALIDATOR = 3      # Python validator 调用
```

TESTCASE_QUALITY_GATE 定位为 **L3_VALIDATOR**，与 StateAuditor / SOPAuditor 同级：

- L1: `route_next_phase()` 检查 `"Test Design" ∈ completed_phases`（不改）
- L2: `AgentResult.success = True` + `skill_observations`（不改）
- **L3 (NEW)**: `TESTCASE_QUALITY_GATE` — 语义质量评分 + 阻断逻辑

## 阻断流程

```
Test Design completed
  ↓
L3 Gate: TESTCASE_QUALITY_GATE
  ├── score ≥ 70 → ✅ PASS → Automation
  ├── score 60-69 → ⚠️ WARN → Automation (P0 模块 → HITL)
  ├── score 40-59 → 🔴 FAIL → retry Test Design (max 2)
  └── score < 40 → ⛔ BLOCK → HITL mandatory
```

---

# Final Verdict

## AITest Platform 当前的问题：缺少的是一个 Quality Model

不是缺少一个 Skill。不是缺少一个 Governance Layer。

**是缺少一个从业务出发的测试质量模型。**

### 证据

| 观察 | 结论 |
|------|------|
| 8 个 Skill 都正常工作 | Skill 不缺 |
| 3 层门禁都正常工作 | Governance 不缺 |
| 8 个 Agent 都正常运行 | Agent 不缺 |
| 但产出的测试用例只有 UI 操作覆盖 | **Quality Model 缺失** |
| page-analysis 只输出 UI 元素 | Quality Model 没定义"页面业务语义" |
| testcase-design 只按 UI 维度生成 | Quality Model 没定义"业务场景覆盖" |
| Q-Check 只检查行数+关键词 | Quality Model 没定义"语义质量" |
| LLMJudge 存在但只在回归测试中用 | Quality Model 没接入 SOP 主流程 |

### 业务覆盖能力应该放在整个系统架构的哪一层

```
┌─────────────────────────────────────────────┐
│          Quality Model (NEW)                 │
│  定义：什么是好的测试用例？                    │
│  维度：业务目标/角色/流程/规则/数据/跨页面      │
│  评分：0-100                                 │
│  标准：每个维度的 golden reference            │
├─────────────────────────────────────────────┤
│          Skill Layer (MODIFY)                │
│  page-analysis: + 业务语义输出                │
│  risk-modeling: + BUSINESS_SCENARIOS 产物     │
│  testcase-design: + 业务场景作为第 9 维度      │
├─────────────────────────────────────────────┤
│          Governance Layer (EXTEND)            │
│  + TESTCASE_QUALITY_GATE (L3)                │
│  + BusinessCoverageInsufficient event        │
│  + Q-Check 从结构扩展到语义                   │
├─────────────────────────────────────────────┤
│          Evaluation Layer (HOOK)              │
│  LLMJudge: + business_coverage dimension     │
│  Regression: + business scenario golden set  │
└─────────────────────────────────────────────┘
```

**Quality Model 在最顶层**——它定义标准。
**Skill Layer 在中间**——它实现标准。
**Governance Layer 在底部**——它执行标准。

三层都改，但 Quality Model 先行。

### 实施顺序

1. **Design Quality Model** — 定义评分维度、权重、golden reference 样本（本文 Part 6）
2. **Implement Source Improvement** (方案 B) — 增强 risk-modeling + testcase-design Skill
3. **Implement Governance Gate** (方案 C) — TESTCASE_QUALITY_GATE + 事件
4. **Calibrate** — 用历史模块数据校准评分阈值
5. **Automate** — 接入 Regression Runner 做持续质量回归

### 一句话结论

> AITest Platform 不缺执行能力，不缺治理能力，缺的是**一个定义"什么才是好的测试用例"的 Quality Model**。当前系统隐式的 Quality Model = 文件存在 × 结构合规 × UI 按钮覆盖。需要显式替换为：业务目标覆盖 × 角色旅程覆盖 × 工作流完整覆盖 × 业务规则覆盖 × 数据流覆盖。
