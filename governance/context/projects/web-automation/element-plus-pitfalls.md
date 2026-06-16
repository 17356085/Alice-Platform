# Element Plus 已知坑位 — 快速索引

> **事实源**: `governance/context/known-issues.yaml`（EP-001 ~ EP-011, 11 条）
> **加载者**: automation-agent, bug-analysis-agent, knowledge-agent

Element Plus 11 个已知坑位已在 `governance/context/known-issues.yaml` 中结构化维护，包含：
- 症状（symptoms）、根因（root_cause）、解决方案（solution）
- 受影响模块（affected_modules）
- 出现频次（occurrence_count）和状态（active/mitigated/resolved）

## 快速索引

| ID | 标题 | 影响组件 |
|----|------|---------|
| EP-001 | Teleport 渲染 | el-select, el-date-picker, el-dialog |
| EP-002 | filterable select 时序不一致 | el-select (filterable) |
| EP-003 | loading 遮罩不消失 | el-table, 搜索区 |
| EP-004 | 动态 class 哈希 | 所有 el-* 组件 |
| EP-005 | v-if 控制元素 | 按钮, 表格列 |
| EP-006 | fixed-right 列克隆 | el-table fixed 列 |
| EP-007 | el-tag 动态颜色 | el-tag |
| EP-008 | 下拉选项延迟渲染 | el-select（远程搜索） |
| EP-009 | el-dropdown 菜单挂载 | el-dropdown |
| EP-010 | Vue 动画期间元素不可交互 | 弹窗, 表格 |
| EP-011 | dialog 2.x 结构变化 | el-dialog |

> 完整详情（症状、根因、解决方案代码）请查阅 `governance/context/known-issues.yaml`。
