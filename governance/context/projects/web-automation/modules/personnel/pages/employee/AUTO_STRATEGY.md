# AUTO_STRATEGY — personnel / employee

> 基于 TECH_ANALYSIS + EmployeeManagePage.py (123行) | 2026-06-11
> 页面类型: 标准 el-table 列表页（只读为主）

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| EM-01 | 页面正常加载 | P0 | ✅ | 导航+表格加载 |
| EM-02 | 表头完整性 | P0 | ✅ | 表头对比 |
| EM-03 | 姓名/工号搜索 | P1 | ✅ | placeholder 定位 A 级 |
| EM-04 | 部门搜索 | P1 | ✅ | 部门下拉筛选 |
| EM-05 | 分页操作 | P1 | ✅ | 标准 el-pagination |
| EM-06 | 查看详情 | P1 | 🔄 | 详情弹窗/跳转待确认 |
| EM-07 | 编辑员工 | P1 | 🔄 | 权限依赖 |

## PageObject 拆分

```
EmployeeManagePage (123行) ← 搜索区 + 表格 + 分页
```

## ROI

| 指标 | 值 |
|------|-----|
| 已投入 | ~1h |
| 维护 | ~0.2h/月 |
| 手工 | 5min/次 |
| 自动化率 | 71% (5/7) |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
