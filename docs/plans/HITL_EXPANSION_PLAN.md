# HITL 扩展方案 — 自动化策略审批 + 测试用例审批

> **来源**：AI 工程能力评估（2026-06-14）→ ⑩ Human-in-the-Loop 掌握度 🟡良好，存在 2 个扩展点
> **目标**：交付给独立 AI 会话执行，无需原始对话上下文
> **前提**：执行前请先阅读 `CLAUDE.md`（项目入口）和 `governance/README.md`（治理骨架）

---

## 快速导航

| 任务 | 优先级 | 预计工期 | 预期收益 | 依赖 |
|------|--------|----------|----------|------|
| [任务 A：自动化策略审批 HITL](#任务-a自动化策略审批-hitl) | **P1** | 2-3 小时 | 代码生成前人工把关定位器/等待策略，减少返工 | 无 |
| [任务 B：P0 测试用例审批 HITL](#任务-bp0-测试用例审批-hitl) | **P2** | 1-2 小时 | 关键模块 P0 用例人工确认，防止漏测核心场景 | 任务 A 完成后更佳（复用模式） |

---

## 背景（给接手 AI 的上下文）

### 当前 HITL 状态

整个项目只有 **1 个 HITL 点**：`bug_analysis_graph.py` 中的 `request_approval_node`（Bug 修复方案审批）。

```
分析失败 → 自动修复 → ⏸️ 人工审批 → 验证 → (循环 或 出报告)
```

核心机制：LangGraph `interrupt()` 挂起执行，携带上下文（cycle、module、analysis_summary、fix_summary、options），等待人工输入 `approve`/`reject`/`skip`。

### 当前 automation-agent 和 test-design-agent 的架构

两个 Agent 通过 `make_agent_loop_node()` 作为不透明节点嵌入 sop_graph，内部由 `AgentLoop.run()` 串行执行全部 Skill，无人工断点：

```
automation-agent Skill 链:
  tech-analysis → auto-strategy → page-object-generator → test-script-generator → code-consistency-checker

test-design-agent Skill 链:
  page-analysis → risk-modeling → testcase-design
```

### 关键文件路径

```
aitest/graphs/
├── sop_graph.py              ← 顶层编排图，需拆分 automation_agent 节点
├── bug_analysis_graph.py     ← ★ 唯一 HITL 参考实现 (request_approval_node:188-216)
├── state.py                  ← SOPState TypedDict，需新增 HITL 字段
├── nodes.py                  ← make_agent_loop_node() — 需支持 skill_subset
├── execution_graph.py        ← execution/report/knowledge SubGraph

aitest/
└── agent_runner.py           ← AgentLoop 类 — 需支持 skill_subset 参数

governance/
├── context/environments.yaml ← P0 模块白名单定义
└── agents/agent-definitions.yaml ← Agent Skill 映射（单一事实源）

.claude/skills/
├── automation-agent/SKILL.md ← 需文档化 HITL 检查点
└── test-design-agent/SKILL.md
```

---

## 任务 A：自动化策略审批 HITL

### 问题

`AUTO_STRATEGY.md`（定位器策略、等待策略、测试文件结构）生成后直接进入代码生成。策略如果出错（如定位器选型不当），后续 PageObject 和测试脚本全部需要返工。

### 方案

在 automation-agent 的 Skill 链中插入人工断点：

```
tech-analysis → auto-strategy → ⏸️ 人工审批 AUTO_STRATEGY.md → page-object-generator → ...
```

#### 步骤 1：AgentLoop 支持部分 Skill 执行

**文件**：[aitest/agent_runner.py](aitest/agent_runner.py)

在 `AgentLoop.__init__` 中新增 `skill_subset` 参数：

```python
class AgentLoop:
    def __init__(
        self,
        agent_name: str,
        provider: str = "claude",
        verbose: bool = True,
        skill_subset: list[str] | None = None,  # ★ 新增：None=全部Skill
        **context,
    ):
        self._skill_subset = skill_subset
        # ... 其余不变

    @property
    def skills(self) -> list[str]:
        full = AGENT_SKILL_MAP.get(self.agent_name, [])
        if self._skill_subset:
            return [s for s in full if s in self._skill_subset]
        return full
```

改动量：~5 行，完全向后兼容。

#### 步骤 2：sop_graph 拆分 automation_agent 节点

**文件**：[aitest/graphs/sop_graph.py](aitest/graphs/sop_graph.py)

将当前单个 `automation_agent` 替换为三个节点：

```python
# 替换原来的:
# builder.add_node("automation_agent", make_agent_loop_node("automation-agent"))

# 改为:
builder.add_node("automation_agent_pre",
    make_agent_loop_node("automation-agent", skill_subset=[
        "automation/tech-analysis",
        "automation/auto-strategy",
    ]))
builder.add_node("automation_strategy_approval", automation_strategy_approval_node)
builder.add_node("automation_agent_post",
    make_agent_loop_node("automation-agent", skill_subset=[
        "automation/page-object-generator",
        "automation/test-script-generator",
        "automation/code-consistency-checker",
    ]))
```

#### 步骤 3：审批节点实现

```python
def automation_strategy_approval_node(state: SOPState) -> dict:
    """HITL：审批 AUTO_STRATEGY.md 后再生成代码。"""
    from langgraph.types import interrupt

    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    page = pages[idx] if idx < len(pages) else ""

    strategy_path = (
        GOVERNANCE / "context" / "projects" / "web-automation" / "modules"
        / state["module"] / "pages" / page / "AUTO_STRATEGY.md"
    )

    if not strategy_path.exists():
        return {"auto_strategy_approved": True}  # 无策略文件，跳过

    summary = strategy_path.read_text(encoding="utf-8")[:800]

    decision = interrupt({
        "type": "automation_strategy_approval",
        "module": state["module"],
        "page": page,
        "strategy_summary": summary,
        "options": ["approve", "reject", "edit"],
        "hint": (
            "审批 AUTO_STRATEGY.md — "
            "确认定位器策略(优先CSS/测试id?)、等待策略(wait_vue_stable?)、"
            "测试文件结构后再生成代码。reject=退回重做，edit=附带修改意见继续"
        ),
    })

    if decision == "approve":
        return {"auto_strategy_approved": True}
    elif isinstance(decision, dict) and decision.get("action") == "edit":
        return {
            "auto_strategy_approved": True,
            "human_feedback": decision.get("feedback", ""),
        }
    else:
        return {
            "auto_strategy_approved": False,
            "fatal_error": f"自动化策略被拒绝: {decision}",
        }
```

#### 步骤 4：条件路由调整

**文件**：[aitest/graphs/sop_graph.py](aitest/graphs/sop_graph.py) — `route_next_phase()`

```python
# 在 route_next_phase 中新增：
# Automation phase 内部分段路由
if current_phase == "Automation" and not state.get("auto_strategy_approved"):
    return "automation_strategy_approval"
```

同时修改 `PHASE_TO_NODE` 映射，将 `"Automation"` 指向 `"automation_agent_pre"`。

#### 步骤 5：State 新增字段

**文件**：[aitest/graphs/state.py](aitest/graphs/state.py)

```python
class SOPState(TypedDict):
    # ... 现有字段 ...
    auto_strategy_approved: Optional[bool]  # None=等待中, True=已批准, False=已拒绝
```

#### 步骤 6：节点注册 + 边

**文件**：[aitest/graphs/sop_graph.py](aitest/graphs/sop_graph.py) — `build_sop_graph()`

```python
# 替换 ALL_AGENT_NODES 中的 "automation_agent"
# 新增内部路由：
builder.add_edge("automation_agent_pre", "automation_strategy_approval")
builder.add_conditional_edges(
    "automation_strategy_approval",
    lambda s: "automation_agent_post" if s.get("auto_strategy_approved") else "exit",
    {"automation_agent_post": "automation_agent_post", "exit": "exit"},
)
builder.add_conditional_edges("automation_agent_post", route_next_phase, route_map)
```

---

## 任务 B：P0 测试用例审批 HITL

### 问题

重要模块（如 equipment、production）的 P0 用例如果设计有遗漏，后续自动化代码覆盖不足，线上风险高。目前 TEST_CASES.md 生成后直接进入 automation 阶段。

### 方案

在 `test-design-agent` 和 `automation-agent` 之间插入条件 HITL 节点，**仅对 P0 模块触发**。

```
test-design-agent → ⏸️ 审批 P0 用例（仅 P0 模块）→ automation-agent-pre → ...
```

#### 步骤 1：P0 模块配置

**文件**：[governance/context/environments.yaml](governance/context/environments.yaml)

```yaml
hitl:
  p0_modules:
    - equipment
    - production
    - quality
  testcase_approval:
    enabled: true
    min_p0_cases: 1  # P0 用例数 ≥ 此值才触发审批
```

#### 步骤 2：审批节点实现

**文件**：[aitest/graphs/sop_graph.py](aitest/graphs/sop_graph.py)

```python
def testcase_approval_node(state: SOPState) -> dict:
    """HITL：P0 模块的测试用例需人工审批后才进入自动化阶段。"""
    from langgraph.types import interrupt

    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    page = pages[idx] if idx < len(pages) else ""

    # 检查是否 P0 模块
    p0_modules = _load_p0_modules()
    if state["module"] not in p0_modules:
        return {"test_cases_approved": True}

    test_cases_path = (
        GOVERNANCE / "context" / "projects" / "web-automation" / "modules"
        / state["module"] / "pages" / page / "TEST_CASES.md"
    )

    if not test_cases_path.exists():
        return {"test_cases_approved": True}

    content = test_cases_path.read_text(encoding="utf-8")
    p0_cases = _extract_p0_cases(content)

    if not p0_cases:
        return {"test_cases_approved": True}

    decision = interrupt({
        "type": "testcase_approval",
        "module": state["module"],
        "page": page,
        "p0_case_count": len(p0_cases),
        "p0_cases_preview": [
            {"id": c["id"], "title": c["title"], "priority": c["priority"]}
            for c in p0_cases[:5]
        ],
        "options": ["approve", "reject", "modify"],
        "hint": (
            f"审批 {page} 的 {len(p0_cases)} 个 P0 测试用例 — "
            "确认覆盖关键业务场景后再生成自动化代码"
        ),
    })

    if decision == "approve":
        return {"test_cases_approved": True}
    elif isinstance(decision, dict) and decision.get("action") == "modify":
        return {
            "test_cases_approved": True,
            "human_feedback": decision.get("feedback", ""),
        }
    else:
        return {
            "test_cases_approved": False,
            "fatal_error": f"P0 测试用例被拒绝: {decision}",
        }


def _load_p0_modules() -> list[str]:
    """从 environments.yaml 加载 P0 模块列表。"""
    import yaml
    env_path = GOVERNANCE / "context" / "environments.yaml"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("hitl", {}).get("p0_modules", [])
    return []


def _extract_p0_cases(content: str) -> list[dict]:
    """从 TEST_CASES.md 解析 P0 用例列表。"""
    import re
    cases = []
    # 匹配优先级为 P0 的测试用例行
    pattern = r'(?:###\s+(?:P0|TC\d+).*?\n)|(?:\|\s*(?:TC\d+|P0)\s*\|)'
    # 简化实现：按行扫描，找到含 P0 标记的行
    for line in content.split("\n"):
        if "P0" in line and ("|" in line or line.startswith("###") or line.startswith("-")):
            cases.append({"id": "", "title": line.strip()[:120], "priority": "P0"})
    return cases
```

#### 步骤 3：条件路由调整

**文件**：[aitest/graphs/sop_graph.py](aitest/graphs/sop_graph.py) — `route_next_phase()`

在 Test Design 完成后、Automation 开始前插入判断：

```python
# route_next_phase 中：
if phase == "Automation":
    # 检查是否需要测试用例审批
    p0_modules = _load_p0_modules()
    if state["module"] in p0_modules and not state.get("test_cases_approved"):
        return "testcase_approval"
    return "automation_agent_pre"
```

#### 步骤 4：State 新增字段

**文件**：[aitest/graphs/state.py](aitest/graphs/state.py)

```python
class SOPState(TypedDict):
    # ... 现有字段 ...
    test_cases_approved: Optional[bool]  # None=未检查/等待中, True=已批准, False=已拒绝
```

#### 步骤 5：节点注册

**文件**：[aitest/graphs/sop_graph.py](aitest/graphs/sop_graph.py) — `build_sop_graph()`

```python
builder.add_node("testcase_approval", testcase_approval_node)

# 条件路由映射更新：
route_map["testcase_approval"] = "testcase_approval"

# test_design_agent 完成后的边改为条件路由：
# （原先: builder.add_conditional_edges("test_design_agent", route_next_phase, route_map)）
# 保持不变，route_next_phase 内部已处理 testcase_approval 的判断
```

---

## 实现顺序

```
1. AgentLoop.skill_subset 支持 (aitest/agent_runner.py)  ← 前置依赖，~5行
2. State 新增字段 (aitest/graphs/state.py)                ← 2个字段
3. 任务 A：automation_strategy_approval_node (sop_graph.py)  ← 核心
4. A 的条件路由 + 边调整 (sop_graph.py)
5. 任务 B：testcase_approval_node (sop_graph.py)
6. B 的 P0 配置 (environments.yaml)
7. 文档更新 (SKILL.md × 2)
8. 端到端验证：aitest graph run --module=equipment --mode=full
```

## 风险评估

| 风险 | 影响 | 缓解 |
|------|------|------|
| AgentLoop skill_subset 改变内部状态机行为 | 中 | `skill_index` 基于子集重排，`plan()` 中的索引计算需适配 |
| sop_graph 节点拆分后 checkpoint 不兼容 | 低 | 新 checkpoint 用新 run_id，不回放旧 checkpoint |
| P0 模块判断依赖 environments.yaml 格式 | 低 | `_load_p0_modules()` 有默认空列表兜底 |
| 两个 HITL 点都默认关闭 | 无 | auto_strategy HITL 通过 `--mode=full` 时默认开启；P0 HITL 仅在配置了 p0_modules 时生效 |

## 与现有架构的一致性

- 复用 LangGraph `interrupt()` 模式（与 `bug_analysis_graph.py:188-216` 一致）
- 复用 `SOPState` TypedDict（不新增 TypedDict）
- 复用 `make_agent_loop_node()` 工厂（加上 `skill_subset` 参数）
- HITL 上下文格式统一：`{type, module, page, options, hint, ...}`
- 所有新节点遵循 `fn(state: SOPState) -> dict` 签名
