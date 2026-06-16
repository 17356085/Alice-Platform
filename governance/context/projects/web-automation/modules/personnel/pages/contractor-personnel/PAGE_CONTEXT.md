# PAGE_CONTEXT — personnel / contractor-personnel

## 基本信息
- 页面ID：contractor-personnel
- 页面名称：承包商人员
- 所属模块：人员管理（personnel）→ 承包商管理
- 页面入口：左侧菜单 → 人员管理 → 承包商管理 → 承包商人员
- 路由 / 标识：`#/personnel/contractor`（与承包商单位共用路由，通过侧边栏 nest-menu 切换）
- 自动化代码：`page/personnel_page/ContractorPersonnelPage.py` + `script/personnel/test_contractor_personnel.py`

## 页面职责
- 展示承包商人员列表，支持按姓名/身份证/所属单位/入场状态搜索
- 提供承包商人员的新增、编辑、启停用、删除操作
- **无独立路由**，通过侧边栏 nest-menu 项在 `#/personnel/contractor` 下切换内部视图

## 核心元素
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| search-name | 姓名/身份证搜索框 | el-input | 搜索区(card) | placeholder="请输入姓名/身份证" |
| search-unit | 所属承包商下拉 | el-select | 搜索区(card) | — |
| search-status | 入场状态下拉 | el-select | 搜索区(card) | — |
| search-btn | 搜索按钮 | el-button | 搜索区 | — |
| reset-btn | 重置按钮 | el-button | 搜索区 | — |
| add-btn | 新增按钮 | el-button | 工具栏 | — |
| table | 承包商人员表格 | el-table | 表格区 | card+table 混合布局 |
| col-name | 姓名列 | text | 表格区 | — |
| col-idcard | 身份证列 | text | 表格区 | — |
| col-unit | 所属单位列 | text | 表格区 | — |
| col-phone | 手机号列 | text | 表格区 | — |
| col-status | 入场状态列 | el-tag? | 表格区 | — |
| col-actions | 操作列 | buttons | 表格区 | 编辑+启停用+删除 |
| dialog | 新增/编辑弹窗 | el-dialog | 弹窗 | 包含姓名/身份证/单位/岗位/手机等字段 |
| pagination | 分页器 | el-pagination | 底部 | — |
| sidebar-personnel | 侧边栏-承包商人员 | el-menu-item.nest-menu | 侧边栏 | 无独立href，点击切换视图 |

## 关键交互
- 侧边栏切换 → 展开"人员管理" → 展开"承包商管理" → 点击"承包商人员" → 视图切换
- 搜索 → card 区输入条件 → 表格异步刷新
- 新增 → 弹窗 → 选择所属承包商 + 填写人员信息 → 保存
- 编辑/删除 → 同标准 CRUD 模式

## 权限与角色
- 可见角色：admin、具有承包商管理权限的角色
- 权限标识：`personnel:contractor:person:list/add/edit/remove`

## 特殊行为
- **无独立路由**：与承包商单位共用 `#/personnel/contractor`，JS hash 直接导航默认显示单位视图
- 导航需两步：(1) hash 跳转到 `#/personnel/contractor` (2) 点击侧边栏 nest-menu 切换视图
- 侧边栏 nest-menu 项展开前提：父级 sub-menu "人员管理" 和 "承包商管理" 均已展开
- card 搜索区：区别于标准表格搜索区，使用 el-card 包裹

## 依赖
- 接口：GET/POST/PUT/DELETE /api/contractor/person/*
- 上游页面：承包商单位（需先有承包商单位才能关联人员）
