# AUTO_STRATEGY — personnel / paper

> 基于 TECH_ANALYSIS + PaperManagePage.py (1531行) | 2026-06-11
> 页面类型: 表格CRUD + 手工选题(左右栏)

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| PP-01 | 页面正常加载 | P0 | ✅ | 表格出现 |
| PP-02 | 试卷名称搜索 | P1 | ✅ | placeholder A级 |
| PP-03 | 分类筛选 | P1 | ✅ | el-select [1] |
| PP-04 | 组卷方式筛选 | P1 | ✅ | el-select [2] |
| PP-05 | 状态筛选 | P1 | ✅ | el-select [3] |
| PP-06 | 重置搜索 | P1 | ✅ | |
| PP-07 | 分页 | P1 | ✅ | |
| PP-08 | 新增/编辑试卷 | P1 | 🔄 | 复杂表单 |
| PP-09 | 手工选题 | P1 | 🔄 | 左栏题库+右栏已选题 |

## PageObject 拆分

```
PaperManagePage (1531行,最大) ← 建议拆分:
  PaperListPage ← 搜索+表格+分页
  PaperEditDialog ← 试卷编辑弹窗
  ManualSelectPanel ← 手工选题左右栏
```

## ROI

| 指标 | 值 |
|------|-----|
| 已投入 | ~4h |
| 维护 | ~0.8h/月(复杂度高) |
| 手工 | 20min/次 |
| 自动化率 | 78% (7/9) |

## 技术债

- 1531行 PO 为项目中最大，建议拆分为 3 个子类
- 手工选题左右栏定位器依赖 CSS class `.left-panel` / `.right-panel`

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
