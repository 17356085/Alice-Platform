# PAGE_CONTEXT — production / business-type-config

## 基本信息
- 页面ID：business-type-config
- 页面名称：业务类型配置
- 所属模块：生产管理（production）
- 页面入口：左侧菜单 → 生产管理 → 业务类型配置
- 路由：`#/production/business-type-config`
- 页面类型：**CRUD 管理页**（含批量删除 + 复杂表单）
- UI 框架：**Element Plus**（el-table / el-button / el-dialog / el-form）

## 页面职责
- CRUD 管理生产业务类型——计划参数(ZPLPA)、业务类型、工厂、物料编码、库存地点、工序号、工作中心、调用接口、生产版本、期间、作业类型1-6、计算公式
- 搜索区支持按计划参数、业务类型(select)、工厂、物料编码筛选
- 表格展示所有配置记录（14条），行级操作（编辑/删除）
- 批量删除：勾选多行后启用页面级删除按钮
- 新增/编辑通过 el-dialog 弹窗完成（17字段，生产管理中最复杂的表单）

## 核心元素

### 搜索区
| 元素ID | 元素描述 | 控件类型 | placeholder | 备注 |
|--------|----------|----------|-------------|------|
| input-plan-param | 计划参数 | el-input | "请输入计划参数" | |
| select-biz-type | 业务类型 | el-select | — | |
| input-factory | 工厂 | el-input | "请输入工厂编码" | |
| input-material | 物料编码 | el-input | "请输入物料编码" | |
| btn-search | 搜索按钮 | el-button (primary) | — | 文字="搜索" |
| btn-reset | 重置按钮 | el-button | — | 文字="重置" |
| btn-add | 新增按钮 | el-button (primary) | — | 文字="新增" |
| btn-delete | 批量删除按钮 | el-button (danger) | — | 默认 disabled，勾选后启用 |

### 表格
| 元素ID | 元素描述 | 控件类型 | 备注 |
|--------|----------|----------|------|
| table-main | 主数据表格 | el-table | 11列: checkbox + 计划参数(ZPLPA) + 业务类型 + 工厂 + 物料编码 + 库存地点 + 工序号 + 工作中心 + 调用接口 + 生产版本 + 操作 |
| col-checkbox | 复选框 | el-checkbox | 首列，支持全选 |
| col-plan-param | 计划参数 | text | 含 ZPLPA 技术标识 |
| col-biz-type | 业务类型 | text | |
| col-factory | 工厂 | text | 4位编码 |
| col-material | 物料编码 | text | |
| col-storage | 库存地点 | text | |
| col-process | 工序号 | text | |
| col-work-center | 工作中心 | text | |
| col-interface | 调用接口 | text | PPI002 |
| col-version | 生产版本 | text | |
| col-actions | 操作列 | el-button (link) | 编辑 + 删除 |
| pagination | 分页 | el-pagination | "共 14 条" |

### 新增/编辑弹窗（17字段 — 生产管理中最复杂的表单）
| 字段 | 控件类型 | placeholder | 备注 |
|------|----------|-------------|------|
| 计划参数 | el-input | "如：10010001" | |
| 业务类型 | el-input | — | |
| 工厂 | el-input | "4位编码" | |
| 物料编码 | el-input | "请输入物料编码" | |
| 库存地点 | el-input | "4位编码" | |
| 工序号 | el-input | "4位编码" | |
| 工作中心 | el-input | "请输入工作中心" | |
| 调用接口 | el-input | "PPI002" | 默认值 PPI002 |
| 生产版本 | el-input | "请输入生产版本" | |
| 期间 | el-input | "yyyyMMdd" | |
| 作业类型1-6 | el-input | "数量" | 6个相同字段 |
| 计算公式 | el-input | "参数值计算公式，如：10010001+100*10010002*10010003" | |

| 弹窗按钮 | 描述 |
|----------|------|
| btn-confirm | 确定按钮 (el-button primary) |
| btn-cancel | 取消按钮 (el-button) |

## 关键交互
- **搜索**：输入条件 → 点击「搜索」→ 表格异步刷新
- **重置**：点击「重置」→ 清空条件 → 恢复 14 条全部数据
- **新增**：点击「新增」→ 弹窗（标题"新增业务类型配置"，17字段空表单）→ 填写 → 确定/取消
- **编辑**：点击行「编辑」→ 弹窗（标题"修改业务类型配置"，回填数据）→ 修改 → 确定
- **行删除**：点击行「删除」→ 确认 → 删除
- **批量删除**：勾选行 → 页面级「删除」启用 → 点击删除

## 页面状态
- **加载中**：el-table loading 遮罩
- **有数据**：14 条记录，10 条/页
- **弹窗**：单例模式

## 依赖
- 接口：CRUD API（推测 /api/production/business-type-config）
- 上游页面：无
- 下游页面：无

## 与 shift-team-config 的差异
| 特征 | shift-team-config | business-type-config |
|------|-------------------|---------------------|
| 数据量 | 0条 | **14条** |
| 表单字段 | 6字段 | **17字段**（含6个作业类型+公式） |
| 批量删除 | ❌ 无 | ✅ 复选框+页面级删除 |
| 表头后缀 | 无 | 计划参数带 **(ZPLPA)** 标识 |
| 复杂度 | 简单 CRUD | **生产管理最复杂 CRUD** |
