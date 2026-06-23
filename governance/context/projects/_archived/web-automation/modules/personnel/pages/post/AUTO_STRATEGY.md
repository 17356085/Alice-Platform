# AUTO_STRATEGY — personnel / post

> 基于 TECH_ANALYSIS + PostManagePage.py (542行) | 2026-06-11
> 页面类型: 标准 el-table CRUD

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| PO-01 | 页面正常加载 | P0 | ✅ | 表格+搜索区 |
| PO-02 | 岗位名称/编码搜索 | P1 | ✅ | placeholder A级 |
| PO-03 | 部门筛选 | P1 | ✅ | el-select [1] |
| PO-04 | 分类筛选 | P1 | ✅ | el-select [2] |
| PO-05 | 状态筛选 | P1 | ✅ | el-select [3] |
| PO-06 | 重置搜索 | P1 | ✅ | |
| PO-07 | 分页 | P1 | ✅ | |
| PO-08 | 新增岗位 | P1 | ✅ | 新增按钮 A 级定位 |
| PO-09 | 编辑岗位 | P1 | 🔄 | |
| PO-10 | 删除岗位 | P1 | 🔄 | |

## PageObject 拆分

```
PostManagePage (542行) ← 搜索区 + 表格 + 弹窗CRUD
```

## ROI

| 指标 | 值 |
|------|-----|
| 已投入 | ~2h |
| 维护 | ~0.3h/月 |
| 手工 | 8min/次 |
| 自动化率 | 80% (8/10) |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
