# AUTO_STRATEGY — personnel / wrong-question

> 基于 TECH_ANALYSIS + PAGE_CONTEXT（⚠️ 推断，无实际数据） | 2026-06-12
> 页面类型: 个人端数据列表（8筛选 + 表格 + 重新作答弹窗）

## 覆盖矩阵

| 编号 | 标题 | 优先级 | 自动化 | 理由 |
|------|------|--------|:--:|------|
| WQ-01 | 页面正常加载 | P0 | ✅ | 表格+筛选区+分页渲染 |
| WQ-02 | 课程筛选 | P1 | ✅ | el-select 选择 |
| WQ-03 | 题型筛选 | P1 | ✅ | el-select 选择 |
| WQ-04 | 来源考试筛选 | P1 | ✅ | el-select 选择 |
| WQ-05 | 组合筛选 | P1 | ✅ | 多条件组合 |
| WQ-06 | 重置搜索 | P1 | ✅ | 重置按钮 |
| WQ-07 | 分页切换 | P1 | ✅ | el-pagination |
| WQ-08 | 重新作答-完整流程 | P1 | ✅ | 弹窗→作答→提交→判分 |
| WQ-09 | 重新作答答对后处理 | P0 | ✅ | 标记"已订正" |
| WQ-10 | 查看解析 | P2 | ✅ | 弹窗展示解析 |
| WQ-11 | 移出错题本 | P2 | ✅ | 确认弹窗→移除 |
| WQ-12 | 空数据状态 | P1 | ✅ | el-empty |
| WQ-13 | 作答来源区分 | P1 | ❌ | 需后端日志验证 |

## PageObject 拆分

```
WrongQuestionPage
├── 筛选区: select_course / select_question_type / select_exam
│          input_keyword / click_search / click_reset
├── 表格区: get_table_rows / get_row_by_question
├── 行操作: click_redo / click_view_analysis / click_remove
├── 重新作答弹窗: get_question_content / select_answer / click_submit
│                get_result / close_dialog
├── 确认弹窗: confirm_remove / cancel_remove
└── 导航: navigate_to_wrong_question
```

## ROI

| 指标 | 值 |
|------|-----|
| 预计投入 | ~2.5h（定位器需数据就绪后验证） |
| 预计维护 | ~0.3h/月 |
| 手工测试 | 12min/次 |
| 目标自动化率 | 92% (12/13) |

## 技术债

- ⚠️ 所有定位器基于推断，需产生错题数据后实际验证
- WQ-13（作答来源区分）需后端接口验证，自动化不可行
- 重新作答弹窗内的题目渲染组件可能因题型不同而结构不同（单选/多选/判断/填空）

<!-- status: scaffold | completed_by: ai-assistant | completed_at: 2026-06-12 -->
