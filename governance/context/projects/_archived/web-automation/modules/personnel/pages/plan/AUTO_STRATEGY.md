# AUTO_STRATEGY — personnel / plan

> 基于 TECH_ANALYSIS + TrainPlanPage.py (1528行) | 2026-06-11
> 页面类型: 表格CRUD + 多步骤流程

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| TP-01 | 页面正常加载 | P0 | ✅ | 表格出现 |
| TP-02 | 计划名称搜索 | P1 | ✅ | placeholder A级 |
| TP-03 | 类型筛选 | P1 | ✅ | el-select [1] |
| TP-04 | 状态筛选 | P1 | ✅ | el-select [2] |
| TP-05 | 发布筛选 | P1 | ✅ | el-select [3] |
| TP-06 | 重置搜索 | P1 | ✅ | |
| TP-07 | 分页 | P1 | ✅ | |
| TP-08 | 新增培训计划 | P1 | 🔄 | 多步骤表单 |
| TP-09 | 审批流程 | P1 | ❌ | 流程复杂 |

## PageObject 拆分

```
TrainPlanPage (1528行) ← 建议拆分:
  TrainPlanListPage ← 搜索+表格+分页
  TrainPlanWizard ← 多步骤表单
```

## ROI

| 指标 | 值 |
|------|-----|
| 已投入 | ~4h |
| 维护 | ~0.8h/月 |
| 手工 | 20min/次 |
| 自动化率 | 78% (7/9) |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
