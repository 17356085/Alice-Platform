# PAGE_CONTEXT — system / notice-management

## 基本信息
- 页面ID：notice-management
- 页面名称：通知管理
- 所属模块：系统管理（system）
- 页面入口：左侧菜单 → 系统管理 → 通知管理
- 路由：#/system/notice

## 页面职责
- 展示系统通知/公告列表，支持搜索、新增、编辑、删除
- 支持按通知标题、通知类型搜索
- 弹窗表单含标题/类型/内容(富文本)/状态

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-title | 通知标题搜索框 | el-input | 搜索区 | placeholder="请输入通知标题" |
| search-type | 通知类型下拉 | el-select | 搜索区 | 通知/公告 |
| search-btn | 搜索按钮 | el-button | 搜索区 | |
| reset-btn | 重置按钮 | el-button | 搜索区 | |
| add-btn | 新增按钮 | el-button | 工具栏 | 文字="新增" |
| table | 通知列表表格 | el-table | 表格区 | 标题/类型/状态/创建时间/操作 |
| col-actions | 操作列 | buttons | 表格区 | 编辑+删除 |
| dialog | 新增/编辑弹窗 | el-dialog | 弹窗 | 含标题/类型/内容/状态 |
| dialog-title-input | 标题输入框 | el-input | 弹窗 | placeholder="请输入通知标题" |
| dialog-type-select | 类型下拉 | el-select | 弹窗 | 通知/公告 |
| dialog-content | 内容编辑区 | 富文本编辑器 | 弹窗 | |
| pagination | 分页器 | el-pagination | 底部 | |

## 关键交互
- 新增 → 弹窗(含富文本编辑器) → 填写 → 确认 → 表格刷新 + toast
- 编辑 → 弹窗(回显含富文本) → 修改 → 确认 → 刷新 + toast
- 删除 → 确认弹窗 → 确认 → 记录消失 + toast
- 搜索 → 表格异步刷新

## 权限与角色
- 可见角色：admin、系统管理员
- 可操作角色：admin(全部)、系统管理员(新增/编辑)
- 特殊限制：普通用户仅可查看已发布通知(通过首页通知栏)

## 特殊行为
- 异步加载：表格数据异步；富文本编辑器初始化耗时
- 动态渲染：类型列用 el-tag 区分通知/公告
- 前端校验：标题必填≤100字符；内容必填
- 后端校验：标题唯一性

## 依赖
- 接口：GET/POST/PUT/DELETE /api/system/notice/*
- 上下游页面：下游-首页通知栏(展示已发布通知)
