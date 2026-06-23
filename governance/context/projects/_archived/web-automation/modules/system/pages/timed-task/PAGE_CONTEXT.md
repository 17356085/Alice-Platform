# PAGE_CONTEXT — system / timed-task

## 基本信息
- 页面ID：timed-task
- 页面名称：定时任务
- 所属模块：系统管理（system）
- 页面入口：左侧菜单 → 系统管理 → 定时任务
- 路由：#/system/job

## 页面职责
- 展示系统定时任务列表，支持搜索、新增、编辑、删除
- 支持任务执行（运行一次）、暂停/恢复、查看日志
- 任务状态通过 el-radio 筛选（全部/运行中/已暂停）
- Cron 表达式支持可视化生成器（抽屉）

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-name | 任务名称搜索框 | el-input | 搜索区 | placeholder含"请输入任务名称" |
| search-type | 任务类型下拉 | el-select | 搜索区 | |
| status-all | 全部状态 | el-radio | 搜索区 | |
| status-running | 运行中 | el-radio | 搜索区 | |
| status-paused | 已暂停 | el-radio | 搜索区 | |
| search-btn | 搜索按钮 | el-button | 搜索区 | 文字="搜索" |
| reset-btn | 重置按钮 | el-button | 搜索区 | 文字="重置" |
| add-btn | 新增按钮 | el-button | 工具栏 | 文字="新增" |
| edit-btn | 修改按钮 | el-button | 工具栏 | |
| delete-btn | 删除按钮 | el-button | 工具栏 | |
| log-btn | 日志按钮 | el-button | 工具栏 | 文字="日志" |
| table | 任务列表表格 | el-table | 表格区 | 名称/任务组/Cron/状态/操作 |
| dialog | 新增/编辑弹窗 | el-dialog | 弹窗 | 含名称/任务组/Cron/类名/参数 |
| cron-drawer | Cron可视化生成抽屉 | el-drawer | 抽屉 | 含"确认使用"/"取消"按钮 |
| pagination | 分页器 | el-pagination | 底部 | |

## 关键交互
- 新增 → 弹窗 → 填写表单 → Cron可视化生成器(可选) → 确认 → 表格刷新 + toast
- 编辑 → 弹窗(回显) → 修改 → 确认 → 刷新 + toast
- 删除 → 确认弹窗 → 确认 → 记录消失 + toast
- 状态筛选(radio) → 表格异步刷新
- 执行任务 → 按钮点击 → toast提示执行结果
- 暂停/恢复 → 按钮点击 → toast提示

## 权限与角色
- 可见角色：admin
- 可操作角色：admin(全部操作)
- 特殊限制：非admin角色不可见此页面(高危操作)

## 特殊行为
- 异步加载：表格数据异步；状态切换后表格刷新
- 动态渲染：状态列用不同颜色标识运行中/暂停
- Cron生成器：点击Cron字段旁按钮打开可视化抽屉
- 前端校验：任务名称必填；Cron表达式格式校验
- 后端校验：任务名称唯一性；Cron表达式合法性

## 依赖
- 接口：GET/POST/PUT/DELETE /api/system/job/*
- 上下游页面：无直接依赖
