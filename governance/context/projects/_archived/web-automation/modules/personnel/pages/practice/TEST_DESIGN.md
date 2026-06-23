# TEST_DESIGN — personnel / practice

> 2026-06-12 | 基于 RISK_MODEL + PAGE_CONTEXT（20条真实数据）

| 编号 | 场景 | 优先级 | 自动化 |
|------|------|--------|:--:|
| PRAC-01 | 页面加载→表格+状态下拉+分页正常渲染 | P0 | ✅ |
| PRAC-02 | 状态下拉筛选（全部/已完成/未完成） | P1 | ✅ |
| PRAC-03 | 分页切换（共20条，2页） | P1 | ✅ |
| PRAC-04 | 已完成记录→点击"开始练习"→跳转答题界面 | P1 | ✅ |
| PRAC-05 | 未完成记录→点击"继续练习"→恢复上次进度 | P1 | ✅ |
| PRAC-06 | 点击"查看成绩"→弹窗展示正确率/得分/题目详情 | P1 | ✅ |
| PRAC-07 | 删除练习记录→确认弹窗→确认→记录消失 | P1 | ✅ |
| PRAC-08 | 删除练习记录→取消→记录保留 | P2 | ✅ |
| PRAC-09 | 练习进行中关闭页面→答题进度保留(localStorage) | P0 | ❌ |
| PRAC-10 | 正确率显示 0/0 时的边界处理（不显示NaN） | P1 | ✅ |
| PRAC-11 | 空数据状态→el-empty 正常显示 | P2 | ✅ |

## P0风险覆盖: RISK-PRAC-001(答题进度丢失)→PRAC-09 | RISK-PRAC-002(删除级联)→PRAC-07

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 -->
