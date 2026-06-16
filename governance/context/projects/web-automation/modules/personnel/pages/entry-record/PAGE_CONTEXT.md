# PAGE_CONTEXT — personnel / entry-record

## 基本信息
- 页面ID：entry-record
- 页面名称：入场记录
- 所属模块：人员管理（personnel）→ 承包商管理
- 页面入口：左侧菜单 → 人员管理 → 承包商管理 → 入场记录
- 路由 / 标识：`#/personnel/contractor/record`
- 自动化代码：`page/personnel_page/EntryRecordPage.py` + `script/personnel/test_entry_record.py`

## 页面职责
- 展示所有承包商人员入场历史记录（只读为主）
- 支持按姓名/单位/日期范围搜索
- 支持导出入场记录
- 支持查看入场详情

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-name | 人员姓名搜索框 | el-input | 搜索区 | placeholder="请输入姓名" |
| search-unit | 承包商单位下拉 | el-select | 搜索区 | — |
| search-date-start | 入场开始日期 | el-date-picker | 搜索区 | — |
| search-date-end | 入场结束日期 | el-date-picker | 搜索区 | — |
| search-btn | 搜索按钮 | el-button | 搜索区 | — |
| reset-btn | 重置按钮 | el-button | 搜索区 | — |
| export-btn | 导出按钮 | el-button | 工具栏 | 文字="导出" |
| table | 入场记录表格 | el-table | 表格区 | 7~11列+操作列 |
| col-record-id | 记录编号列 | text | 表格区 | 第1列 |
| col-applicant | 申请人列 | text | 表格区 | — |
| col-unit | 承包商列 | text | 表格区 | — |
| col-personnel | 人员姓名列 | text | 表格区 | — |
| col-position | 岗位列 | text | 表格区 | — |
| col-status | 状态列 | el-tag | 表格区 | — |
| col-actions | 操作列 | buttons | 表格区 | 详情 |
| btn-detail | 详情按钮 | el-button | 行内 | 文字="详情"或"查看" |
| detail-dialog | 详情弹窗 | el-dialog | 弹窗 | 查看入场记录详情 |
| pagination | 分页器 | el-pagination | 底部 | 默认10条/页 |

## 关键交互
- 页面加载 → 表格异步加载 → 显示入场记录列表
- 搜索 → 输入姓名/选择单位/选择日期范围 → 表格异步刷新
- 导出 → 点击导出按钮 → 触发浏览器下载
- 详情 → 点击行内详情 → 弹窗展示完整入场信息
- 重置 → 清空搜索条件 → 恢复全部记录

## 权限与角色
- 可见角色：admin、安全管理员、审批人
- 可操作角色：admin（导出）、安全管理员（导出）
- 特殊限制：普通承包商人员仅可查看自己的记录

## 特殊行为
- 只读页面：无新增/编辑/删除操作，仅查询+导出
- 日期范围搜索：支持入场时间起止日期筛选
- 空数据：数据为0时显示"暂无数据"，分页器显示"共 0 条"
- 导出：可能触发浏览器下载弹窗

## 依赖
- 接口：GET /api/contractor/entry-record/list, GET /api/contractor/entry-record/export
- 上游页面：入场审批（审批通过后自动生成入场记录）
- 下游页面：无
