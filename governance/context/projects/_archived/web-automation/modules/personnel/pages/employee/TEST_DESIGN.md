# TEST_DESIGN — personnel / employee

> 2026-06-11 | 基于 RISK_MODEL + AUTO_STRATEGY | 6维度覆盖

| 编号 | 场景 | 优先级 | 自动化 |
|------|------|--------|:--:|
| EM-01 | 页面正常加载→表格+搜索区可见 | P0 | ✅ |
| EM-02 | 表格表头完整性 | P0 | ✅ |
| EM-03 | 姓名/工号搜索 | P1 | ✅ |
| EM-04 | 部门筛选 | P1 | ✅ |
| EM-05 | 分页-翻页/改变每页条数 | P1 | ✅ |
| EM-06 | 查看详情弹窗 | P1 | 🔄 |
| EM-07 | 权限–部门主管仅见本部门 | P1 | 🔄 |
| EM-08 | 权限–无权限用户URL拦截 | P0 | 🔄 |

## P0风险覆盖

| 风险 | 场景 | 状态 |
|------|------|:--:|
| RISK-EMP-001 误删除 | 删除确认弹窗 | ⚠️ |
| RISK-EMP-002 权限越权 | EM-07 + EM-08 | 🔄 |

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
