# Skill: regression-scope

## 目标
基于 Git diff + 历史缺陷 + 执行结果 → 推荐回归测试范围。TLO 闭环反馈最后一环。

## 输入
- Git diff (当前分支 vs main/master)
- 历史缺陷数据 (known-issues.yaml)
- 最近执行结果 (trace_log.jsonl)
- 模块 SOP 状态 (SOP_STATUS_*.json)

## 输出
- REGRESSION_SCOPE.md — 回归范围推荐报告
  - 变更影响分析 (哪些文件变了 → 哪些模块受影响)
  - 高风险区域 (Top 5，含等级)
  - 推荐回归模块列表 (优先级排序)
  - 回归测试估算 (用例数 + 预估耗时)
  - 不推荐回归的模块 (变更无关)

## 分析方法

### 1. Git Diff 影响分析
```
变更文件 → 提取模块名 → 映射到测试模块
  script/equipment/test_alarm.py     → equipment
  script/warehouse/page_spare.py     → warehouse
  aitest/graphs/sop_graph.py         → ALL (核心编排变更)
  governance/agents/*.yaml           → ALL (Agent 定义变更)
```

### 2. 历史缺陷热度
```
known-issues.yaml 中按模块统计:
  equipment:  12 issues / 5 高危  → 高风险
  personnel:   8 issues / 2 高危  → 中风险
  workflow:    3 issues / 0 高危  → 低风险
```

### 3. 执行结果趋势
```
最近 7 天执行结果:
  equipment: 85% pass, 15% fail → 仍需关注
  warehouse: 95% pass,  5% fail → 可降低回归频率
  tank:      100% pass, 0% fail → 最低优先级
```

## 推荐算法

```
Risk_Score(module) = 
    diff_impact(module) * 0.4 +
    defect_heat(module)  * 0.35 +
    (1 - recent_pass_rate(module)) * 0.25

score ≥ 0.7 → 必须回归
score ≥ 0.4 → 建议回归
score < 0.4 → 可选回归
```

## 规则
- 核心编排变更 (sop_graph/agent_runner) → 全部模块必须回归
- Agent 定义变更 → 受影响的 Agent 覆盖的全部模块必须回归
- Page Object 变更 → 仅该模块回归
- 配置文件变更 (.env, conftest) → 全部模块冒烟

## 依赖
- git (命令行)
- governance/context/known-issues.yaml
- governance/.traces/trace_log.jsonl
- governance/artifacts/sop-status/SOP_STATUS_*.json

## 边界
- 不执行测试
- 不修改代码
- 纯分析建议，最终决策由人工确认

---

## Prompt 模板

```text
你是一个资深质量策略顾问。请基于以下信息推荐回归测试范围。

## 输入
- Git diff: {{git_diff_summary}}
- 历史缺陷: {{defect_heat}}
- 最近执行: {{recent_results}}

## 任务
1. 分析 Git diff 改动影响的模块
2. 结合历史缺陷热度排序模块风险
3. 考虑最近执行通过率调整优先级
4. 输出 REGRESSION_SCOPE.md

## 输出格式
| 优先级 | 模块 | 风险分 | 理由 | 用例数 | 预估耗时 |
| P0 | equipment | 0.85 | diff 变更 + 5 高危缺陷 | 28 | 5min |
| P1 | warehouse | 0.60 | diff 变更 + 2 中危缺陷 | 15 | 3min |
| P2 | tank     | 0.20 | 无变更 + 无高危 | 7 | 2min |

## 回归建议摘要
- 必须回归: equipment, warehouse
- 建议回归: personnel
- 可选回归: tank, workflow
- 无需回归: dcs (3月无变更+无缺陷)
```
