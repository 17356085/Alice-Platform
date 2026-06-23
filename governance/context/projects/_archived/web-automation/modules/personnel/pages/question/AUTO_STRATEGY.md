# AUTO_STRATEGY — personnel / question

> 基于 TECH_ANALYSIS + QuestionBankPage.py (702行) | 2026-06-11
> 页面类型: 表格CRUD + 批量导入

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| QT-01 | 页面正常加载 | P0 | ✅ | 表格出现 |
| QT-02 | 题干搜索 | P1 | ✅ | placeholder A级 |
| QT-03 | 题型筛选 | P1 | ✅ | el-select [1] |
| QT-04 | 难度筛选 | P1 | ✅ | el-select [2] |
| QT-05 | 重置搜索 | P1 | ✅ | |
| QT-06 | 分页 | P1 | ✅ | |
| QT-07 | 新建试题 | P1 | ✅ | 按钮 A 级定位 |
| QT-08 | 批量导入 | P1 | ❌ | 文件对话框+Selenium不可控 |
| QT-09 | 批量删除 | P1 | 🔄 | 勾选+确认 |
| QT-10 | 编辑试题 | P1 | 🔄 | |

## PageObject 拆分

```
QuestionBankPage (702行) ← 搜索区 + 表格 + 弹窗CRUD + 导入
```

## ROI

| 指标 | 值 |
|------|-----|
| 已投入 | ~2.5h |
| 维护 | ~0.3h/月 |
| 手工 | 10min/次 |
| 自动化率 | 70% (7/10) |

## 技术债

- 批量导入依赖 `<input type="file">`，Selenium send_keys 可操作但文件路径管理复杂

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
