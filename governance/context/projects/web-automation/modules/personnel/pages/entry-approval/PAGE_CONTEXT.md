# PAGE_CONTEXT — personnel / entry-approval

## 基本信息
- 页面ID：entry-approval
- 页面名称：入场审批
- 所属模块：人员管理（personnel）→ 承包商管理
- 页面入口：左侧菜单 → 人员管理 → 承包商管理 → 入场审批
- 路由 / 标识：`#/personnel/contractor/approval`
- 自动化代码：`page/personnel_page/EntryApprovalPage.py` + `script/personnel/test_entry_approval.py`

## 页面职责
- 展示承包商人员的入场申请列表，支持按申请人/单位/审批状态搜索
- 提供审批通过、审批驳回、查看详情操作
- 审批流程核心节点，决定承包商人员是否可以进入作业区域

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-name | 申请人搜索框 | el-input | 搜索区 | placeholder="请输入姓名" |
| search-unit | 承包商单位下拉 | el-select | 搜索区 | — |
| search-status | 审批状态下拉 | el-select | 搜索区 | 待审批/已通过/已驳回 |
| search-btn | 搜索按钮 | el-button | 搜索区 | — |
| reset-btn | 重置按钮 | el-button | 搜索区 | — |
| table | 入场审批表格 | el-table | 表格区 | 8列+操作列 |
| col-applicant | 申请人列 | text | 表格区 | 第1列 |
| col-unit | 承包商列 | text | 表格区 | 第2列 |
| col-entry-time | 入场时间列 | text | 表格区 | 第3列 |
| col-description | 入场说明列 | text | 表格区 | 第4列 |
| col-work-type | 作业类型列 | text | 表格区 | 第5列 |
| col-status | 审批状态列 | el-tag | 表格区 | 待审批/已通过/已驳回 |
| col-actions | 操作列 | buttons | 表格区 | 通过+驳回+详情 |
| btn-approve | 通过按钮 | el-button | 行内 | 文字="通过" |
| btn-reject | 驳回按钮 | el-button | 行内 | 文字="驳回" |
| btn-detail | 详情按钮 | el-button | 行内 | 文字="详情" |
| approval-dialog | 审批意见弹窗 | el-dialog | 弹窗 | 驳回时填写审批意见 |
| detail-dialog | 详情弹窗 | el-dialog | 弹窗 | 查看申请详情 |
| pagination | 分页器 | el-pagination | 底部 | 默认10条/页 |

## 关键交互
- 页面加载 → 表格异步加载 → 显示待审批/已审批记录
- 通过 → 点击通过按钮 → 确认 → 状态变更 + toast
- 驳回 → 点击驳回按钮 → 填写审批意见 → 确认 → 状态变更 + toast
- 详情 → 弹窗展示申请人/单位/入场说明等完整信息
- 状态筛选 → 切换下拉选项 → 表格异步刷新

## 权限与角色
- 可见角色：admin、审批人、安全管理员
- 可操作角色：admin（全部）、审批人（通过/驳回）
- 特殊限制：普通用户仅可查看自己的申请

## 特殊行为
- 异步加载：表格数据 + 下拉选项异步加载
- 状态标签：待审批=橙色、已通过=绿色、已驳回=红色
- 审批意见：驳回时必填，通过时可选
- 操作按钮显隐：已审批记录不显示"通过/驳回"按钮

## 依赖
- 接口：GET /api/contractor/approval/list, POST /api/contractor/approval/approve, POST /api/contractor/approval/reject
- 上游页面：承包商人员（人员发起入场申请）
- 下游页面：入场记录（审批通过后生成记录）
