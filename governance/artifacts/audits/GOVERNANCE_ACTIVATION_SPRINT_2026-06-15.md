# Governance Activation Sprint — 2026-06-15

> 验证并激活已有治理体系。让治理事件真实触发。让治理链路真实运行。

---

## Part 1: Governance Activation Inventory

| 组件 | 状态 | 未激活原因 |
|------|------|-----------|
| **Prompt Versioning** | READY (代码) / INACTIVE (运行时) | `promote_skill_version()` **0个调用方**。26个Skill全在v1.0，从未经历版本升级。 |
| **State Auditor** | READY (代码) / INACTIVE (事件) | 能发现漂移(equipment发现16个)，但emit仅在`sop_graph.py:489`。CLI/API审计路径**不发射**StateDrift。 |
| **SOP Auditor** | READY (代码) / INACTIVE (事件) | 能发现违规(equipment发现3个)，但emit仅在`sop_graph.py:510`。CLI/API审计路径**不发射**SOPViolation。 |
| **Regression Gate** | PARTIAL | `check_prompt_upgrade()`可用。`promote_skill_version()`存在但**从未被调用**。无版本生命周期。 |
| **Cost Auditor** | READY (代码) / INACTIVE (调度) | 仅手动CLI/API。无定时任务、无CycleEnd自动触发。 |
| **Governance Event Bus** | READY (基础设施) / INACTIVE (消费) | `KnowledgeAgentSubscriber`仅在`event_bus watch`模式激活。生产环境无订阅者。 |

### 触发条件分析

| 组件 | 触发条件 | 条件满足? | 缺失数据 |
|------|---------|-----------|---------|
| Prompt Versioning | `promote_skill_version()`被调用 | ❌ 从未调用 | 调用方 |
| State Auditor emit | `sop_graph.exit_node`中`drift_count > 0` | ⚠️ 是(16个漂移)但走错代码路径 | CLI/API路径缺少emit |
| SOP Auditor emit | `sop_graph.exit_node`中`total_violations > 0` | ⚠️ 是(3个违规)但走错代码路径 | CLI/API路径缺少emit |
| Regression Gate | `promote_skill_version()`被调用 | ❌ 从未调用 | 调用方 |
| Cost Auditor | `alert.severity in (high,medium)` | ⚠️ 未知(从未运行) | 定时执行 |
| AuditCompleted | 任意审计完成 | ❌ emit代码不存在 | 缺失emit调用 |

---

## Part 2: Event Activation Analysis

### 各事件生命周期

#### PromptChanged
```
[✓] 已定义:    event_bus.py:76 — EVENT_ACTIONS条目
[✓] emit代码:  regression.py:612 — promote_skill_version()内
[✗] 已触发:    promote_skill_version()有0个调用方
[✗] EventBus:  emit()可用但从未被调用
[✗] 订阅者:    KnowledgeAgentSubscriber已注册但未激活
[✗] 已持久化:  会写入governance/.events/ — 从未到达
```

#### StateDrift
```
[✓] 已定义:    event_bus.py:66 — EVENT_ACTIONS条目
[✓] emit代码:  sop_graph.py:489 — exit_node()内
[✗] 已触发:    审计通过CLI/API运行，绕过exit_node
[✗] EventBus:  emit()可用但审计路径不调用
[✗] 订阅者:    KnowledgeAgentSubscriber已注册但未激活
[✗] 已持久化:  报告存在(16个漂移)但无事件
```

#### SOPViolation
```
[✓] 已定义:    event_bus.py:71 — EVENT_ACTIONS条目
[✓] emit代码:  sop_graph.py:510 — exit_node()内
[✗] 已触发:    审计通过CLI/API运行，绕过exit_node
[✗] EventBus:  emit()可用但审计路径不调用
[✗] 订阅者:    KnowledgeAgentSubscriber已注册但未激活
[✗] 已持久化:  报告存在(3个违规)但无事件
```

#### EvalRegressed
```
[✓] 已定义:    event_bus.py:81 — EVENT_ACTIONS条目
[✓] emit代码:  regression.py:631 — promote_skill_version()内
[✗] 已触发:    promote_skill_version()有0个调用方
[✗] EventBus:  emit()可用但从未被调用
[✗] 订阅者:    KnowledgeAgentSubscriber已注册但未激活
```

#### CostAnomaly
```
[✓] 已定义:    event_bus.py:86 — EVENT_ACTIONS条目
[✓] emit代码:  cost_auditor.py:116 — audit()内
[✗] 已触发:    Cost auditor从未自动运行
[✗] EventBus:  手动运行时会触发
[✗] 订阅者:    KnowledgeAgentSubscriber已注册但未激活
```

#### AuditCompleted
```
[✓] 已定义:    event_bus.py:91 — EVENT_ACTIONS条目
[✗] emit代码:  不存在 — 整个代码库零调用方
[✗] 已触发:    不适用
```

### Event Activation Matrix

| 事件 | 已定义 | emit存在 | 可达 | 已持久化 | 已消费 | **已激活** |
|------|--------|----------|------|----------|--------|-----------|
| PromptChanged | ✅ | ✅ | ❌ | ❌ | ❌ | **NO** |
| StateDrift | ✅ | ✅ | ❌ | ❌ | ❌ | **NO** |
| SOPViolation | ✅ | ✅ | ❌ | ❌ | ❌ | **NO** |
| EvalRegressed | ✅ | ✅ | ❌ | ❌ | ❌ | **NO** |
| CostAnomaly | ✅ | ✅ | ⚠️ | ❌ | ❌ | **NO** |
| AuditCompleted | ✅ | ❌ | ❌ | ❌ | ❌ | **NO** |

**0/6 治理事件已激活。**

---

## Part 3: Governance Dead Paths

### Dead Path 1 (P0): `promote_skill_version()` — 孤儿函数

**位置**: `regression.py:581-644`

**问题**: 完整的版本推广生命周期已实现但**0个调用方**。该函数:
1. 从registry获取当前版本
2. 运行回归门禁(`check_prompt_upgrade`)
3. 通过→更新registry + 发射`PromptChanged`
4. 失败→发射`EvalRegressed`

但整个代码库没有任何地方调用`promote_skill_version()`。CLI没有、API没有、SOP graph没有、scheduler没有、任何agent没有。

**影响**: `PromptChanged`和`EvalRegressed`永久死亡。Prompt versioning链路完全实现但从未启动。

---

### Dead Path 2 (P0): 审计emit仅在`exit_node`

**位置**: `sop_graph.py:480-519`

**问题**: `StateDrift`和`SOPViolation`仅在SOP graph `exit_node`中发射。但审计器还通过以下方式运行:
1. CLI: `aitest audit state --module=equipment` → `state_auditor.py:__main__` → 无emit
2. API: `GET /api/audit/state` → `server/main.py:163` → 无emit
3. 手动: `StateAuditor().audit("equipment")` → 无emit

这些路径发现了真实的漂移/违规但**不发射事件**。

**影响**: equipment模块发现16个state drift和3个SOP违规 — 零事件发射。

---

### Dead Path 3 (P0): `AuditCompleted` — 幽灵事件

**位置**: `event_bus.py:91-95`

**问题**: 事件在`EVENT_ACTIONS`中完整定义(含触发器、条件、prompt模板)。但`emit("AuditCompleted", ...)`在整个项目的任何`.py`文件中都不存在。

**影响**: 治理审计生命周期缺失终结事件。无法追踪审计是否发生。

---

### Dead Path 4 (P1): `try/except Exception: pass` — 静默故障掩码

**位置**: 5处

| 文件 | 行号 | 事件 |
|------|------|------|
| `sop_graph.py` | 496-497 | StateDrift |
| `sop_graph.py` | 515-516 | SOPViolation |
| `regression.py` | 617-618 | PromptChanged |
| `regression.py` | 636-637 | EvalRegressed |
| `cost_auditor.py` | 121-122 | CostAnomaly |

**问题**: 即使emit被触发，任何失败(ValueError、文件系统错误等)都被静默吞掉。

**影响**: 即使触发条件满足，故障不可见。调试不可能。

---

### Dead Path 5 (P1): `KnowledgeAgentSubscriber` — 生产环境从未激活

**位置**: `event_bus.py:248-322`

**问题**: 治理事件的唯一运行时订阅者仅在手动CLI模式激活:
- `event_bus.py:376` — `python -m aitest.event_bus watch` (手动)

以下位置未激活:
- `sop_graph.py`
- `server/main.py`
- `agent_runner.py`
- 任何scheduler/cron

**影响**: 即使事件发射，无人监听。事件持久化到`.events/`目录但永不被处理。

---

### Dead Path 6 (P2): `ContextUpdated` — 又一个幽灵事件

**位置**: `event_bus.py:59-63`

与AuditCompleted相同：`EVENT_ACTIONS`中已定义但`emit("ContextUpdated", ...)`在项目中不存在。

---

### Dead Path 7 (P2): `AgentCompleted` — 狭窄的里程碑门禁

**位置**: `agent_runner.py:1524-1528`

`_maybe_emit_event()`仅对3个硬编码skill触发:
```python
milestones = [
    "automation/tech-analysis",
    "automation/page-object-generator",
    "automation/code-consistency-checker",
]
```

其他53个skill永远不会触发`AgentCompleted`。

---

### Dead Path 汇总

| Dead Path | 严重度 | 受影响事件 |
|-----------|--------|-----------|
| `promote_skill_version()`孤儿函数 | **P0** | PromptChanged, EvalRegressed |
| 审计emit仅在exit_node | **P0** | StateDrift, SOPViolation |
| AuditCompleted幽灵事件 | **P0** | AuditCompleted |
| try/except静默pass (x5) | **P1** | 全部5个治理事件 |
| KnowledgeAgentSubscriber未激活 | **P1** | 全部事件(消费端) |
| ContextUpdated幽灵事件 | **P2** | ContextUpdated |
| AgentCompleted狭窄门禁 | **P2** | AgentCompleted |

---

## Part 4: Governance Activation Test Plan

### 实验1: Prompt Versioning 激活

**目标**: 触发`PromptChanged`事件

**前置条件**: skill-registry.yaml中存在至少一个已注册版本的skill

**步骤**:
```bash
# 1. 在skill-registry.yaml中为已有skill创建v1.1版本条目
# 2. 添加版本化文件(复制现有skill文件)
# 3. 调用promote_skill_version
python -c "
from aitest.regression import promote_skill_version
result = promote_skill_version('test-design/page-analysis', '1.1')
print(result)
"

# 4. 检查事件
python -m aitest.event_bus listen
```

**预期**: `governance/.events/promptchanged-*.json`存在，含skill_id, old_version="1.0", new_version="1.1"

**成功标准**: 事件文件已创建

**风险**: `check_prompt_upgrade()`可能因无baseline而失败→触发`EvalRegressed`(同样是有效激活)

---

### 实验2: State Auditor 激活

**目标**: 触发`StateDrift`事件

**前置条件**: 已知有状态漂移的模块(equipment有16个漂移)

**步骤**:
```bash
python -c "
from aitest.state_auditor import StateAuditor
from aitest.event_bus import emit

auditor = StateAuditor()
report = auditor.audit('equipment')
if report['drift_count'] > 0:
    emit('StateDrift',
         module='equipment',
         run_id='activation-test',
         drift_count=report['drift_count'],
         error_count=report['error_count'],
         warning_count=report['warning_count'],
         overall_status=report['overall_status'])
    print(f'Emitted StateDrift: {report[\"drift_count\"]} drifts')
"

python -m aitest.event_bus listen
```

**预期**: `StateDrift`事件，drift_count=16

**成功标准**: 事件文件已创建

---

### 实验3: SOP Auditor 激活

**目标**: 触发`SOPViolation`事件

**前置条件**: 已知有SOP违规的模块(equipment有3个违规)

**步骤**:
```bash
python -c "
from aitest.sop_auditor import SOPAuditor
from aitest.event_bus import emit

auditor = SOPAuditor()
report = auditor.audit('equipment', days=30)
if report['total_violations'] > 0:
    emit('SOPViolation',
         module='equipment',
         run_id='activation-test',
         violation_type='manual_audit',
         detail=f'SOP审计发现 {report[\"total_violations\"]} 个违规')
    print(f'Emitted SOPViolation: {report[\"total_violations\"]} violations')
    for v in report['violations']:
        print(f'  - [{v[\"check_type\"]}] {v[\"detail\"][:100]}')
"

python -m aitest.event_bus listen
```

**预期**: `SOPViolation`事件，3个违规

**成功标准**: 事件文件已创建

---

### 实验4: Regression Gate 激活

**目标**: 触发`EvalRegressed`事件

**前置条件**: 故意质量退化的skill版本

**步骤**:
```bash
# 1. 创建故意退化的skill版本(v0.9-degraded)
# 2. 在skill-registry.yaml中注册
# 3. 运行promote
python -c "
from aitest.regression import promote_skill_version
result = promote_skill_version('test-design/page-analysis', '0.9-degraded')
print('Promoted:', result['promoted'])
print('Gate:', result.get('gate_result', {}).get('recommendation', ''))
"

python -m aitest.event_bus listen
```

**预期**: `EvalRegressed`事件(门禁检测到退化版本)

**替代(通过)**: 如果baseline存在且新版本通过门禁→`PromptChanged`事件

**成功标准**: `EvalRegressed`或`PromptChanged`事件文件存在

---

### 实验5: Cost Auditor 激活

**目标**: 触发`CostAnomaly`事件

**前置条件**: 有足够事件计算成本统计的trace log(已有5760个事件)

**步骤**:
```bash
python -c "
from aitest.cost_auditor import CostAuditor
auditor = CostAuditor()
report = auditor.audit(days=30)
print(f'Alerts: {report[\"alert_count\"]}')
print(f'Total cost: \${report[\"total_cost\"]:.4f}')
for a in report['alerts'][:5]:
    print(f'  [{a[\"severity\"]}] {a[\"finding\"][:100]}')
"

python -m aitest.event_bus listen
```

**预期**: 成本审计报告 + high/medium级别的`CostAnomaly`事件

**成功标准**: CostAnomaly事件文件存在(如检测到异常)或确认性报告(无异常)

---

### Activation Checklist

| 实验 | 前置条件 | 命令 | 预期事件 | 成功 |
|------|---------|------|---------|------|
| 1. PromptVersioning | registry中v1.1条目 | `promote_skill_version(...)` | PromptChanged | 事件文件创建 |
| 2. StateDrift | equipment模块 | `StateAuditor.audit()` + emit | StateDrift | 事件文件创建 |
| 3. SOPViolation | equipment模块 | `SOPAuditor.audit()` + emit | SOPViolation | 事件文件创建 |
| 4. RegressionGate | 退化skill版本 | `promote_skill_version(...)` | EvalRegressed | 事件文件创建 |
| 5. CostAnomaly | 已有trace数据 | `CostAuditor.audit()` | CostAnomaly | 事件文件创建 |

---

## Part 5: End-to-End Governance Chain

### Prompt Governance Chain

```
Skill修改 → 版本注册 → promote_skill_version()
    → check_prompt_upgrade() → gate通过/失败
    → emit(PromptChanged | EvalRegressed)
    → EventBus持久化 → KnowledgeAgentSubscriber消费
    → 治理报告
```

**覆盖率**: 40% — 步骤1-4代码存在。步骤5(emit)不可达。步骤6-7(订阅者)未激活。

### State Governance Chain

```
SOP Graph运行 → exit_node → StateAuditor.audit()
    → 检测到漂移 → emit(StateDrift)
    → EventBus持久化 → KnowledgeAgentSubscriber消费
    → 治理报告
```

**覆盖率**: 30% — 步骤1-3正常。步骤4(emit)仅在exit_node路径，CLI/API不走。步骤5不可达。步骤6-7未激活。

### SOP Governance Chain

```
SOP Graph运行 → exit_node → SOPAuditor.audit()
    → 检测到违规 → emit(SOPViolation)
    → EventBus持久化 → KnowledgeAgentSubscriber消费
    → 治理报告
```

**覆盖率**: 30% — 与State Governance相同。

### Evaluation Governance Chain

```
Skill版本升级 → promote_skill_version()
    → check_prompt_upgrade() → gate通过/失败
    → emit(PromptChanged | EvalRegressed)
    → EventBus持久化 → KnowledgeAgentSubscriber消费
```

**覆盖率**: 20% — 整条链依赖`promote_skill_version()`被调用。从未被调用。

### Cost Governance Chain

```
CostAuditor.audit() → spike/bloat/trend/optimization检查
    → 检测到异常 → emit(CostAnomaly)
    → EventBus持久化 → KnowledgeAgentSubscriber消费
```

**覆盖率**: 40% — 步骤1-4手动调用时可用。无自动触发。步骤5-6未激活。

### 整体链路覆盖率: **32%**

---

## Part 6: Governance Activation Score

| 维度 | 得分 | 说明 |
|------|------|------|
| **组件就绪度** | 75/100 | 5个治理组件全部实现。代码质量良好。5条dead path存在。 |
| **事件就绪度** | 25/100 | 4/6事件有emit代码但在不可达路径。1个事件无emit。0/6曾触发。 |
| **数据流就绪度** | 30/100 | Trace数据存在(5760事件)。审计数据存在(16漂移, 3违规)。但事件数据流从未启动。 |
| **治理覆盖率** | 32/100 | 见Part 5链路分析。所有链路在emit或消费阶段断裂。 |
| **运维就绪度** | 15/100 | 无治理检查自动触发。无活跃订阅者。仅手动CLI/API。 |

### 总分: **35/100**

---

## Part 7: Activation Roadmap

### P0: 闭合Emit缺口 (关键 — 阻塞所有治理事件)

| 动作 | 内容 | 位置 |
|------|------|------|
| **审计路径添加emit** | State/SOP/Cost审计器应在自身`audit()`方法中发射事件，而非仅从`sop_graph.exit_node` | `state_auditor.py`, `sop_auditor.py`, `cost_auditor.py` |
| **接入`promote_skill_version()`** | 添加CLI命令: `aitest skill promote <id> <version>`。或从`exit_node` Knowledge阶段后调用。 | `cli.py`或`sop_graph.py` |
| **添加`AuditCompleted` emit** | 每个审计器的`audit()`应在结束时发射AuditCompleted | 全部3个审计器文件 |
| **移除静默`pass`** | 将`except Exception: pass` → `except Exception as e: log_error(...)` | 5处 |

### P1: 激活消费端

| 动作 | 内容 | 位置 |
|------|------|------|
| **自动启动订阅者** | 在服务器启动(`main.py`)和SOP graph运行时激活`KnowledgeAgentSubscriber` | `server/main.py`, `sop_graph.py` |
| **扩展`AgentCompleted`** | 扩展milestone列表或改为skill-status触发 | `agent_runner.py` |
| **发射`ContextUpdated`** | 从`context_injector.py`或`context_sync` skill发射 | `context_injector.py` |

### P2: 自动化触发

| 动作 | 内容 | 位置 |
|------|------|------|
| **定时成本审计** | Cron或scheduler: 每日`aitest audit cost --days=7` | `agent_scheduler.py` |
| **CycleEnd自动审计** | 已在`exit_node`中 — 确保此路径为主要路径，非CLI/API | 已存在，需使用方式转变 |

### 激活序列

```
Step 1 (P0): 审计器audit()方法中添加emit
    → StateDrift, SOPViolation, CostAnomaly, AuditCompleted变为可达

Step 2 (P0): 接入promote_skill_version()到CLI
    → PromptChanged, EvalRegressed变为可达

Step 3 (P0): 将try/except pass替换为log_error
    → 故障变为可见

Step 4 (P1): 服务器启动时激活KnowledgeAgentSubscriber
    → 事件被消费，而非仅持久化

Step 5 (P2): 调度定期审计
    → 治理变为运维化，而非仅按需

Step 3后: 事件发射 → 激活评分 ~55
Step 4后: 事件发射+消费 → 激活评分 ~70
Step 5后: 治理运维化 → 达到L3 Governed
```

---

## Final Verdict

### 当前状态: L2 Managed → 接近 L3 Governed

### 距离 L3 缺失

| 缺失 | 严重度 | 修复工作量 |
|------|--------|-----------|
| 治理事件从未触发 (0/6) | P0 | 1-2天 |
| `promote_skill_version()` 无调用方 | P0 | 0.5天 |
| `AuditCompleted` 无emit代码 | P0 | 0.5天 |
| 静默`except:pass` 掩盖故障 | P1 | 0.5天 |
| 订阅者生产环境未激活 | P1 | 0.5天 |
| 审计未自动调度 | P2 | 1天 |

### 激活后预期

治理体系代码完整度 80% → 激活后可达 L3 Governed:
- 全部6个治理事件真实触发
- 5条治理链闭合 (Prompt/State/SOP/Evaluation/Cost)
- 审计覆盖率 >65%
- 事件持久化 + 订阅消费正常

### 核心结论

**治理体系已建成，但开关从未打开。需要约4天激活工作即可达到L3 Governed。**
