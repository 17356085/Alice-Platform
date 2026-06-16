# PAGE_CONTEXT — personnel / contractor-unit

## 基本信息
- 页面ID：contractor-unit
- 页面名称：承包商单位
- 所属模块：人员管理（personnel）→ 承包商管理
- 页面入口：左侧菜单 → 人员管理 → 承包商管理 → 承包商单位
- 路由 / 标识：`#/personnel/contractor`
- 自动化代码：`page/personnel_page/ContractorUnitPage.py` + `script/personnel/test_contractor_unit.py`

## 页面职责
- 展示承包商单位列表，支持按名称/编码/状态搜索
- 提供承包商单位的新增、编辑、启停用、删除操作
- 承包商单位与承包商人员共用路由，通过侧边栏 nest-menu 项切换视图

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-name | 单位名称搜索框 | el-input | 搜索区 | placeholder="单位名称" |
| search-code | 单位编码搜索框 | el-input | 搜索区 | placeholder="单位编码" |
| search-status | 状态下拉 | el-select | 搜索区 | 启用/停用 |
| search-btn | 搜索按钮 | el-button | 搜索区 | — |
| reset-btn | 重置按钮 | el-button | 搜索区 | — |
| add-btn | 新增按钮 | el-button | 工具栏 | 表格上方 |
| table | 承包商单位表格 | el-table | 表格区 | 6列+操作列 |
| col-name | 承包商名称列 | text | 表格区 | 第1列 |
| col-code | 承包商代码列 | text | 表格区 | 第2列 |
| col-safety | 安全负责人列 | text | 表格区 | 第3列 |
| col-contact | 联系人列 | text | 表格区 | 第4列 |
| col-phone | 联系电话列 | text | 表格区 | 第5列 |
| col-status | 状态列 | el-tag? | 表格区 | 启用/停用 |
| col-actions | 操作列 | buttons | 表格区 | 编辑+启停用+删除 |
| dialog | 新增/编辑弹窗 | el-dialog | 弹窗 | 居中，包含单位编码/名称/联系人/电话等字段 |
| pagination | 分页器 | el-pagination | 底部 | 默认10条/页 |
| sidebar-unit | 侧边栏-承包商单位 | el-menu-item.nest-menu | 侧边栏 | 与承包商人员同级 |

## 关键交互
- 页面加载 → 表格异步请求 → loading → 数据渲染
- 搜索 → 输入条件 → 点击搜索 → 表格异步刷新
- 重置 → 清空搜索条件 → 表格恢复全部数据
- 新增 → 弹窗展开 → 填写表单 → 保存 → toast"新增成功" + 表格刷新
- 编辑 → 行内编辑按钮 → 弹窗预填数据 → 保存 → toast + 表格刷新
- 启用/停用 → 行内按钮 → 状态切换 → toast
- 删除 → 确认弹窗 → 确认 → 记录消失 + toast
- 侧边栏切换 → 点击"承包商人员" → 内部视图切换（同路由）

## 权限与角色
- 可见角色：admin、具有承包商管理权限的角色
- 可操作角色：admin（全部）、承包商管理员（新增/编辑）
- 权限标识：`personnel:contractor:list/add/edit/remove`

## 特殊行为
- 异步加载：表格数据异步加载，loading 遮罩 300-800ms
- 同路由双视图：承包商单位与人员共用 `#/personnel/contractor`，侧边栏菜单项无独立 href
- 动态渲染：无数据时显示"暂无数据"
- 前端校验：单位名称/编码必填

## 依赖
- 接口：GET/POST/PUT/DELETE /api/contractor/*
- 上下游页面：承包商人员（同路由视图切换）
