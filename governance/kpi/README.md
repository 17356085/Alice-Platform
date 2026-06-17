# KPI 目录标准

> 测试 KPI 数据与报告的权威存储位置。Agent/Skill/Workflow 产出 Excel 报告时必须写入此目录。

## 目录结构

```
governance/kpi/
├── reports/{模块}/         ← Phase 9 综合测试报告 .xlsx（SOP 最终交付物）
├── timeseries/            ← 执行时序 JSONL（sop-{module}-*.jsonl, state-{module}-*.jsonl）
└── README.md              ← 本文件
```

## 报告命名规范

| 类型 | 路径 | 命名 | 覆盖策略 |
|------|------|------|----------|
| 综合测试报告 | `reports/{模块}/` | `测试报告-{模块}.xlsx` | **覆盖** — SOP 重跑时直接覆写 |
| 执行时序 | `timeseries/` | `sop-{module}-YYYY-MM-DD.jsonl` | **追加** — 每次执行追加一行 |

## 反模式

- ❌ 不要把 .xlsx 输出到 `ZJSN_Test-master526/reports/`（旧路径，已废弃）
- ❌ 不要在文件名加时间戳（报告是覆盖式的，最新即权威）
- ❌ 不要把 Excel 放在 `governance/kpi/testcases/`（旧路径，已废弃）

## 关联文档

- `governance/skills/execution/excel-exporter.md` — Excel 生成 Skill
- `governance/skills/reporting/report-generator.md` — 报告引擎 Skill
- `governance/context/shared-language.md` — 术语注册
