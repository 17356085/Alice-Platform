# PAGE_CONTEXT — system / params-management

## 基本信息
- 页面ID：params-management
- 页面名称：参数设置
- 所属模块：系统管理（system）
- 页面入口：左侧菜单 → 系统管理 → 参数设置
- 路由：#/system/config

## 页面职责
- 展示系统参数配置列表，支持搜索、新增、编辑、删除
- 支持按参数名称、参数键名、参数类型、业务模块搜索
- 提供刷新缓存功能

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-name | 参数名称搜索框 | el-input | 搜索区 | placeholder="请输入参数名称" |
| search-key | 参数键名搜索框 | el-input | 搜索区 | placeholder="请输入参数键名" |
| search-type | 参数类型下拉 | el-select | 搜索区 | 字符串/数值/布尔等 |
| search-module | 业务模块下拉 | el-select | 搜索区 | |
| search-btn | 搜索按钮 | el-button | 搜索区 | 文字="搜索" |
| reset-btn | 重置按钮 | el-button | 搜索区 | 文字="重置" |
| add-btn | 新增按钮 | el-button | 工具栏 | 文字="新增" |
| export-btn | 导出按钮 | el-button | 工具栏 | 文字="导出" |
| refresh-cache-btn | 刷新缓存按钮 | el-button | 工具栏 | 文字="刷新缓存" |
| table | 参数列表表格 | el-table | 表格区 | 名称/键名/值/类型/模块/备注/操作 |
| col-actions | 操作列 | buttons | 表格区 | 编辑+删除 |
| dialog | 新增/编辑弹窗 | el-dialog | 弹窗 | 含名称/键名/值/类型/模块/备注 |
| pagination | 分页器 | el-pagination | 底部 | |

## 关键交互
- 新增 → 弹窗 → 填写表单 → 确认 → 表格刷新 + toast
- 编辑 → 弹窗(回显数据) → 修改 → 确认 → 表格刷新 + toast
- 删除 → 确认弹窗 → 确认 → 记录消失 + toast
- 刷新缓存 → toast提示刷新结果
- 搜索 → 表格异步刷新

## 权限与角色
- 可见角色：admin、系统管理员
- 可操作角色：admin(全部)、系统管理员(新增/编辑/刷新缓存)
- 特殊限制：系统内置参数不可删除

## 特殊行为
- 异步加载：表格数据异步加载
- 动态渲染：参数类型列用不同颜色标识
- 前端校验：名称必填≤100字符；键名必填
- 后端校验：键名唯一性；系统参数受保护；刷新缓存需admin权限

## 依赖
- 接口：GET/POST/PUT/DELETE /api/system/config/*
- 上下游页面：上游-字典管理(参数值可能引用字典)
