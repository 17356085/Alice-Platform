# AUTO_STRATEGY — personnel / study-record

> 基于 TECH_ANALYSIS + PAGE_CONTEXT（9条真实数据） | 2026-06-12
> 页面类型: 管理端记录列表（表格 + 3条件筛选 + 无行操作）

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| SR-01 | 页面正常加载 | P0 | ✅ | 表格+3筛选条件+分页渲染 |
| SR-02 | 学员名称搜索 | P1 | ✅ | CSS input[placeholder*=学员名称] |
| SR-03 | 课程名称搜索 | P1 | ✅ | CSS input[placeholder*=课程名称] |
| SR-04 | 是否完成筛选 | P1 | ✅ | el-select 选择→查询 |
| SR-05 | 组合筛选 | P1 | ✅ | 多条件同时填充→查询 |
| SR-06 | 重置搜索 | P1 | ✅ | 重置按钮 |
| SR-07 | 分页切换 | P1 | ✅ | el-pagination 点击 |
| SR-08 | 学习进度显示 | P1 | ✅ | 文本断言百分比格式 |
| SR-09 | 学习时长格式化 | P2 | ✅ | 文本断言"秒/分钟"单位 |
| SR-10 | 空数据状态 | P2 | ✅ | el-empty |
| SR-11 | 普通员工数据隔离 | P0 | ❌ | 需切换角色，多账号测试 |

## PageObject 拆分

```
StudyRecordPage
├── 筛选区: input_student_name / input_course_name / select_completed
│          click_search / click_reset
├── 表格区: get_table_rows / get_row_by_student / get_progress
├── 分页区: get_total_count / change_page
└── 导航: navigate_to_study_record
```

## ROI

| 指标 | 值 |
|------|-----|
| 预计投入 | ~1.5h |
| 预计维护 | ~0.2h/月 |
| 手工测试 | 8min/次 |
| 目标自动化率 | 91% (10/11) |

## 技术债

- SR-11（多角色数据隔离）需不同角色账号，当前仅 admin 可用，降级为手工
- 列 6-9 表头未渲染（使用 td:nth-child 保底），若后续版本修复表头需更新定位器

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 -->
