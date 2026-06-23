# PAGE_CONTEXT — system / system-log

## 基本信息
- 页面ID：system-log
- 页面名称：系统日志
- 所属模块：系统管理（system）
- 页面入口：左侧菜单 → 系统管理 → 日志管理 → 系统日志
- 路由：#/system/log/system-log

## 页面职责
- 展示系统运行日志列表（只读），支持搜索、筛选、清空
- 支持按日志类型(el-select)、日志级别(el-select)、模块名称搜索
- 支持按时间范围筛选
- 支持清空全部日志(高危操作)

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-log-type | 日志类型下拉 | el-select | 搜索区 | 含"请选择日志类型" |
| search-log-level | 日志级别下拉 | el-select | 搜索区 | 含"请选择日志级别" |
| search-module | 模块名称搜索框 | el-input | 搜索区 | placeholder="请输入模块名称" |
| date-start | 开始日期 | el-date-picker | 搜索区 | placeholder="开始日期" |
| date-end | 结束日期 | el-date-picker | 搜索区 | placeholder="结束日期" |
| search-btn | 搜索按钮 | el-button | 搜索区 | 文字="搜索" |
| reset-btn | 重置按钮 | el-button | 搜索区 | 文字="重置" |
| clear-btn | 清空按钮 | el-button | 工具栏 | 文字="清空" |
| table | 系统日志表格 | el-table | 表格区 | 类型/级别/模块/内容/时间 |
| col-level | 日志级别列 | el-tag | 表格区 | ERROR=红/WARN=黄/INFO=蓝/DEBUG=灰 |
| pagination | 分页器 | el-pagination | 底部 | |

## 关键交互
- 日志类型下拉选择 → 筛选日志类型（操作日志/登录日志/系统日志等）
- 日志级别下拉选择 → 筛选级别（ERROR/WARN/INFO/DEBUG）
- 模块名称输入 → 精确/模糊搜索模块
- 搜索 → 表格异步刷新（类型/级别/模块/时间多条件组合）
- 清空 → 二次确认弹窗 → 确认 → 所有记录删除 + toast（高危）
- 重置 → 所有搜索条件清空 → 表格恢复

## 权限与角色
- 可见角色：admin
- 可操作角色：admin(全部)
- 特殊限制：非admin角色不可见(系统运行数据敏感)

## 特殊行为
- 异步加载：表格数据异步；el-select下拉选项异步加载
- 动态渲染：日志级别用不同颜色 el-tag（ERROR红/WARN黄/INFO蓝/DEBUG灰）
- 清空操作：二次确认防误操作
- 大量数据：系统日志数据量极大(每条业务操作都生成)，时间范围筛选+分页
- 无详情弹窗：表格直接展示关键信息，无额外详情页

## 依赖
- 接口：GET /api/system/log/system-log/list, DELETE /api/system/log/system-log/clear
- 上下游页面：无直接依赖（运维监控独立页面）
