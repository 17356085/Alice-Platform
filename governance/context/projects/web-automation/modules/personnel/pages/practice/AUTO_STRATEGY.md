# AUTO_STRATEGY — personnel / practice

> 基于 TECH_ANALYSIS + PAGE_CONTEXT（20条真实数据） | 2026-06-12
> 页面类型: 个人端记录列表（表格 + 单筛选 + 行操作按钮）

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| PRAC-01 | 页面正常加载 | P0 | ✅ | 表格+状态下拉+分页渲染 |
| PRAC-02 | 状态下拉筛选 | P1 | ✅ | el-select 定位 |
| PRAC-03 | 分页切换 | P1 | ✅ | el-pagination 点击 |
| PRAC-04 | 已完成-开始练习 | P1 | ✅ | 按钮文字"开始练习" |
| PRAC-05 | 未完成-继续练习 | P1 | ✅ | 按钮文字"继续练习" |
| PRAC-06 | 查看成绩 | P1 | ✅ | 弹窗检测 |
| PRAC-07 | 删除练习记录 | P1 | ✅ | 确认弹窗→记录消失 |
| PRAC-08 | 删除-取消 | P2 | ✅ | 弹窗关闭 |
| PRAC-09 | 答题进度保留 | P0 | ❌ | localStorage 检测需 JS 注入 |
| PRAC-10 | 正确率边界值 | P1 | ✅ | 文本断言 0.0% |
| PRAC-11 | 空数据状态 | P2 | ✅ | el-empty |

## PageObject 拆分

```
PracticePage
├── 筛选区: select_status / get_table_rows
├── 表格区: get_row_by_name / get_row_status / get_row_accuracy
├── 行操作: click_start_practice / click_continue_practice
│          click_view_result / click_delete
├── 确认弹窗: confirm_delete / cancel_delete
├── 成绩弹窗: get_result_dialog / close_result_dialog
└── 导航: navigate_to_practice
```

## ROI

| 指标 | 值 |
|------|-----|
| 预计投入 | ~2h |
| 预计维护 | ~0.2h/月 |
| 手工测试 | 10min/次 |
| 目标自动化率 | 91% (10/11) |

## 技术债

- PRAC-09（localStorage 进度保留）需 JS 注入，自动化困难，降级为手工
- "开始练习"/"继续练习" 点击后跳转到独立答题页面，超出本页面范围

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 -->
