# PAGE_CONTEXT — system / login-log

## 基本信息
- 页面ID：login-log
- 页面名称：登录日志
- 所属模块：系统管理（system）
- 页面入口：左侧菜单 → 系统管理 → 日志管理 → 登录日志
- 路由：#/system/log/login-log

## 页面职责
- 展示用户登录记录列表（只读），支持搜索、筛选、清空、导出
- 支持按用户名、登录状态(全部/成功/失败)、登录时间范围搜索
- 提供详情弹窗查看单条登录日志详情
- 支持清空全部日志(高危操作)

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-username | 用户名搜索框 | el-input | 搜索区 | placeholder="请输入用户名" |
| status-all | 全部状态 | el-radio | 搜索区 | |
| status-success | 成功 | el-radio | 搜索区 | |
| status-fail | 失败 | el-radio | 搜索区 | |
| search-status | 状态下拉 | el-select | 搜索区 | 备用筛选 |
| date-start | 开始日期 | el-date-picker | 搜索区 | placeholder含"开始日期" |
| date-end | 结束日期 | el-date-picker | 搜索区 | placeholder含"结束日期" |
| search-btn | 搜索按钮 | el-button | 搜索区 | 文字="搜索" |
| reset-btn | 重置按钮 | el-button | 搜索区 | 文字="重置" |
| clear-btn | 清空按钮 | el-button | 工具栏 | 文字="清空" |
| export-btn | 导出按钮 | el-button | 工具栏 | 文字="导出" |
| table | 登录日志表格 | el-table | 表格区 | 用户名/IP/地点/浏览器/OS/状态/时间/操作 |
| col-status | 状态列 | el-tag | 表格区 | 成功=绿/失败=红 |
| col-actions | 操作列 | button | 表格区 | 详情 |
| detail-dialog | 详情弹窗 | el-dialog | 弹窗 | 标题"登录日志详情" |
| pagination | 分页器 | el-pagination | 底部 | |

## 关键交互
- 搜索 → 表格异步刷新（用户名/状态/时间范围组合筛选）
- 点击详情 → 弹窗展示完整登录信息
- 清空 → 二次确认弹窗 → 确认 → 所有记录删除 + toast（高危）
- 导出 → 下载Excel文件
- 日期选择 → el-date-range-picker 面板

## 权限与角色
- 可见角色：admin
- 可操作角色：admin(搜索/查看/导出/清空)
- 特殊限制：非admin角色不可见此页面(审计数据敏感)

## 特殊行为
- 异步加载：表格数据异步；日期范围选择后需手动点搜索
- 动态渲染：状态列 el-tag 颜色；详情弹窗内容动态
- 清空操作：需二次确认防止误操作
- 详情弹窗：含登录IP、浏览器UA、操作系统等详细信息
- 大量数据：默认分页展示，历史数据量大

## 依赖
- 接口：GET /api/system/log/login-log/list, DELETE /api/system/log/login-log/clear
- 上下游页面：无直接依赖（审计独立页面）
