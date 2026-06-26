# Dev SOP KPI Reports

Dev SOP 流水线的 KPI 报告目录。按开发项目分目录存储。

## 目录结构

```
reports-dev/
├── README.md                    ← 这个文件
└── <project>/                   ← 按开发项目分
    └── 开发报告-<project>.xlsx   ← KPI 报告（待首次运行后生成）
```

## KPI 指标定义

| 指标 | 说明 | 目标 |
|------|------|------|
| Phase 完成率 | completed_phases / total_phases | ≥80% |
| Agent 成功率 | passed_agents / total_agents | ≥90% |
| Skill 成功率 | passed_skills / total_skills | ≥85% |
| Token 效率 | tokens_per_phase | 待基线 |
| 门禁通过率 | gate_pass_runs / total_runs | 100% |
| HITL 触发率 | hitl_triggers / total_skills | ≤10% |
| 修复轮次均值 | avg debug rounds per issue | ≤2 |

## 报告生成

首次 Dev SOP 全量运行后，运行以下命令生成报告:

```bash
aitest kpi generate --engine=dev-sop --module=<project> --format=xlsx
```

## 当前状态

- **aitest-platform**: 0 completed phases（待首次运行）
- **报告**: 无（待生成）
