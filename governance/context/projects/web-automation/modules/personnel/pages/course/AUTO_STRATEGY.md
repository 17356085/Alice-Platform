# AUTO_STRATEGY — personnel / course

> 基于 TECH_ANALYSIS + CourseManagePage.py (570行) | 2026-06-11
> 页面类型: 课程卡片网格 + 搜索筛选 + 弹窗CRUD

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| CR-01 | 页面正常加载 | P0 | ✅ | 课程卡片网格出现 |
| CR-02 | 课程名称搜索 | P1 | ✅ | 输入框定位 |
| CR-03 | 分类筛选 | P1 | ✅ | el-select [1] |
| CR-04 | 素材类型筛选 | P1 | ✅ | el-select [2] |
| CR-05 | 发布状态筛选 | P1 | ✅ | el-select [3] |
| CR-06 | 重置搜索 | P1 | ✅ | |
| CR-07 | 新增课程 | P1 | 🔄 | 含文件上传(素材) |
| CR-08 | 课程卡片-查看 | P1 | 🔄 | |
| CR-09 | 编辑课程 | P1 | 🔄 | |

## PageObject 拆分

```
CourseManagePage (570行) ← 卡片网格 + 搜索区 + 弹窗CRUD + 素材上传
```

## ROI

| 指标 | 值 |
|------|-----|
| 已投入 | ~2.5h |
| 维护 | ~0.3h/月 |
| 手工 | 10min/次 |
| 自动化率 | 67% (6/9) |

## 技术债

- 文件上传自动化依赖系统文件对话框（Selenium 不可控）

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
