# AUTO_STRATEGY — personnel / exam

> 基于 TECH_ANALYSIS + ExamManagePage.py (856行) | 2026-06-11
> 页面类型: 表格CRUD + 阅卷模式

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| EX-01 | 页面正常加载 | P0 | ✅ | 表格+搜索区 |
| EX-02 | 考试名称搜索 | P1 | ✅ | placeholder A级 |
| EX-03 | 状态筛选 | P1 | ✅ | el-select |
| EX-04 | 发布状态筛选 | P1 | ✅ | el-select |
| EX-05 | 日期范围搜索 | P1 | ✅ | el-date-picker |
| EX-06 | 重置搜索 | P1 | ✅ | |
| EX-07 | 分页操作 | P1 | ✅ | |
| EX-08 | 新增/编辑考试 | P1 | 🔄 | 复杂表单 |
| EX-09 | 阅卷模式 | P1 | ❌ | 评分表单复杂 |

## PageObject 拆分

```
ExamManagePage (856行) ← 搜索区 + 表格 + 弹窗CRUD + 阅卷模式
  (ExamGradingPage) ← 阅卷子页面(建议拆分)
```

## ROI

| 指标 | 值 |
|------|-----|
| 已投入 | ~3h |
| 维护 | ~0.5h/月 |
| 手工 | 15min/次 |
| 自动化率 | 78% (7/9) |

## 技术债

- 阅卷模式含评分表单+考生答卷区，DOM 结构复杂

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
