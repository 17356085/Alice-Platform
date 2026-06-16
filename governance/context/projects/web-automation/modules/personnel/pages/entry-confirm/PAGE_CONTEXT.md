# PAGE_CONTEXT — personnel / entry-confirm

## 基本信息
- 页面ID：entry-confirm
- 页面名称：入场确认
- 所属模块：人员管理（personnel）→ 承包商管理
- 页面入口：左侧菜单 → 人员管理 → 承包商管理 → 入场确认
- 路由 / 标识：`#/personnel/contractor/confirm`
- 自动化代码：`page/personnel_page/EntryConfirmPage.py` + `script/personnel/test_entry_confirm.py`

## 页面职责
- 承包商人员到达门岗后，安保人员在此确认其实际入场
- 列表展示待确认/已确认的入场申请，支持按承包商名称、人员姓名搜索
- 提供单条"确认入场"和"批量确认入场"操作
- 是承包商入场流程的最终节点：申请 → 审批 → **确认入场** → 生成入场记录

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-contractor | 承包商名称搜索框 | el-input | 搜索区 | placeholder="承包商名称" |
| search-personnel | 人员姓名搜索框 | el-input | 搜索区 | placeholder="人员姓名" |
| search-btn | 搜索按钮 | el-button | 搜索区 | 文字="搜索" |
| reset-btn | 重置按钮 | el-button | 搜索区 | 文字="重置" |
| batch-confirm-btn | 批量确认入场按钮 | el-button | 工具栏 | 文字="批量确认入场" |
| clear-cache-btn | 清空缓存按钮 | el-button | 工具栏 | 文字="清空缓存" |
| table | 入场确认表格 | el-table | 表格区 | 9列（含复选框） |
| col-checkbox | 复选框列 | el-checkbox | 表格区 | 第1列，批量选择 |
| col-request-no | 申请编号列 | text | 表格区 | 第2列 |
| col-contractor | 承包商列 | text | 表格区 | 第3列 |
| col-personnel | 人员列 | text | 表格区 | 第4列 |
| col-work-type | 工种列 | text | 表格区 | 第5列 |
| col-work-area | 作业区域列 | text | 表格区 | 第6列 |
| col-planned-entry | 计划入场列 | text | 表格区 | 第7列 |
| col-entry-reason | 入场事由列 | text | 表格区 | 第8列 |
| col-actions | 操作列 | buttons | 表格区 | 第9列，确认入场按钮 |
| btn-confirm-entry | 确认入场按钮 | el-button | 行内 | 文字="确认入场" |
| tag-unread | 未读标签 | el-tag | 表格区 | 未读=橙色 |
| tag-read | 已读标签 | el-tag | 表格区 | 已读=绿色 |
| pagination | 分页器 | el-pagination | 底部 | — |

## 关键交互
- 页面加载 → 表格异步加载 → 显示待确认入场记录
- 确认入场 → 点击行内"确认入场"按钮 → 确认弹窗 → 状态变更 + toast
- 批量确认入场 → 勾选多行 → 点击"批量确认入场" → 批量操作
- 搜索 → 输入承包商名称/人员姓名 → 搜索 → 表格异步刷新
- 重置 → 清空搜索条件 → 恢复全部数据
- 清空缓存 → 清除前端缓存数据

## 权限与角色
- 可见角色：admin、安保人员、安全管理员
- 可操作角色：admin（全部）、安保人员（确认入场）
- 特殊限制：普通用户无权限操作

## 特殊行为
- 状态标签：未读=橙色、已读=绿色
- 复选框列用于批量操作
- 确认入场为不可逆操作

## 依赖
- 上游页面：入场审批（审批通过后流转至此）
- 下游页面：入场记录（确认入场后生成入场记录）
- 数据流：入场申请 → 入场审批 → **入场确认** → 入场记录
