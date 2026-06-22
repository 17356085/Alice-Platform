# PAGE_CONTEXT — system / operation-log

## 基本信息
- 页面ID：operation-log
- 页面名称：操作日志
- 所属模块：系统管理（system）
- 页面入口：左侧菜单 → 系统管理 → 日志管理 → 操作日志
- 路由：#/system/log/oper-log

## 页面职责
- 展示用户操作记录列表（只读），支持搜索、筛选、清空、导出
- 支持按系统模块、操作类型、操作人员、状态搜索
- 支持按操作时间范围筛选
- 提供详情查看每一条操作记录
- 支持清空全部日志(高危操作)

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-module | 系统模块搜索框 | el-input | 搜索区 | placeholder="请输入系统模块" |
| search-op-type | 操作类型输入框 | el-input | 搜索区 | placeholder="请输入操作类型" |
| search-operator | 操作人员搜索框 | el-input | 搜索区 | placeholder="请输入操作人员" |
| status-all | 全部 | el-radio | 搜索区 | |
| status-success | 成功 | el-radio | 搜索区 | |
| status-fail | 失败 | el-radio | 搜索区 | |
| date-start | 开始日期 | el-date-picker | 搜索区 | placeholder="开始日期" |
| date-end | 结束日期 | el-date-picker | 搜索区 | placeholder="结束日期" |
| search-btn | 搜索按钮 | el-button | 搜索区 | 文字="搜索" |
| reset-btn | 重置按钮 | el-button | 搜索区 | 文字="重置" |
| clear-btn | 清空按钮 | el-button | 工具栏 | 文字="清空" |
| export-btn | 导出按钮 | el-button | 工具栏 | 文字="导出" |
| table | 操作日志表格 | el-table | 表格区 | 模块/类型/操作人/IP/状态/时间/操作 |
| col-status | 状态列 | el-tag | 表格区 | 成功=绿/失败=红 |
| col-actions | 操作列 | button | 表格区 | 详情 |
| detail-dialog | 详情弹窗 | el-dialog | 弹窗 | 含请求参数/返回结果 |
| pagination | 分页器 | el-pagination | 底部 | |

## 关键交互
- 搜索 → 表格异步刷新（模块/类型/操作人/状态/时间多条件组合）
- 点击详情 → 弹窗展示请求参数、返回结果、耗时等详细信息
- 清空 → 二次确认弹窗 → 确认 → 所有记录删除 + toast（高危）
- 导出 → 下载Excel文件
- 状态切换(radio) → 表格筛选刷新

## 权限与角色
- 可见角色：admin
- 可操作角色：admin(全部)
- 特殊限制：非admin角色不可见(审计数据，含敏感操作参数)

## 特殊行为
- 异步加载：表格数据异步；多条件组合搜索
- 动态渲染：状态列 el-tag；详情弹窗含JSON格式请求参数
- 清空操作：二次确认防误操作
- 详情弹窗：含完整请求参数(request params/body)和返回结果(response)，内容较长
- 大量数据：操作日志数据量极大(每次操作都记录)，分页+时间范围筛选

## 依赖
- 接口：GET /api/system/log/oper-log/list, DELETE /api/system/log/oper-log/clear
- 上下游页面：无直接依赖（审计独立页面）
