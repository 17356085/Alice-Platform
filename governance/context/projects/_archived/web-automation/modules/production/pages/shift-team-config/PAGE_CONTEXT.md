# PAGE_CONTEXT — production / shift-team-config

## 基本信息
- 页面ID：shift-team-config
- 页面名称：班次班组配置
- 所属模块：生产管理（production）
- 页面入口：左侧菜单 → 生产管理 → 班次班组配置
- 路由：`#/production/shift-team-config`
- 页面类型：**CRUD 管理页**
- UI 框架：**Element Plus**（el-table / el-button / el-dialog / el-form / el-select）

## 页面职责
- CRUD 管理工厂排班配置——工厂、排班类型、时段、日期、班组、班次
- 搜索区支持按工厂、排班类型(select)、班组、班次筛选
- 表格展示所有配置记录，行级操作（编辑/删除）
- 新增/编辑通过 el-dialog 弹窗完成

## 核心元素

### 搜索区
| 元素ID | 元素描述 | 控件类型 | placeholder | 备注 |
|--------|----------|----------|-------------|------|
| input-factory | 工厂 | el-input | "请输入工厂编码" | |
| select-schedule-type | 排班类型 | el-select | — | 需点击展开选项 |
| input-team | 班组 | el-input | "请输入班组" | |
| input-shift | 班次 | el-input | "请输入班次" | |
| btn-search | 搜索按钮 | el-button (primary) | — | 文字="搜索" |
| btn-reset | 重置按钮 | el-button | — | 文字="重置" |
| btn-add | 新增按钮 | el-button (primary) | — | 文字="新增"，打开弹窗 |

### 表格
| 元素ID | 元素描述 | 控件类型 | 备注 |
|--------|----------|----------|------|
| table-main | 主数据表格 | el-table | 8列: checkbox + 工厂 + 排班类型 + 时段 + 日期 + 班组 + 班次 + 操作 |
| col-checkbox | 复选框列 | el-checkbox | 首列 |
| col-factory | 工厂列 | text | |
| col-schedule-type | 排班类型列 | text | |
| col-time-slot | 时段列 | text | |
| col-date | 日期列 | text | |
| col-team | 班组列 | text | |
| col-shift | 班次列 | text | |
| col-actions | 操作列 | el-button (link) | 编辑 + 删除 |
| pagination | 分页 | el-pagination | "共 N 条" |

### 新增/编辑弹窗
| 元素ID | 元素描述 | 控件类型 | placeholder | 备注 |
|--------|----------|----------|-------------|------|
| dialog-main | 弹窗容器 | el-dialog | — | 标题="新增班次班组配置" 或 "修改班次班组配置" |
| field-factory | 工厂 | el-input | "4位编码" | 必填 |
| field-schedule-type | 排班类型 | el-input(?) | — | 实地确认为 input |
| field-time-slot | 时段 | el-input | "如：12:00-0:00" | |
| field-date | 日期 | el-input | "yyyyMMdd" | |
| field-team | 班组 | el-input | "如：白班" | |
| field-shift | 班次 | el-input | "如：运行一部" | |
| btn-confirm | 确定按钮 | el-button (primary) | — | 文字="确 定" |
| btn-cancel | 取消按钮 | el-button | — | 文字="取 消" |

## 关键交互
- **搜索**：输入条件 → 点击「搜索」→ 表格异步刷新
- **重置**：点击「重置」→ 清空搜索条件 → 表格恢复默认数据
- **新增**：点击「新增」→ 弹窗打开（空表单）→ 填写 → 确定（保存） 或 取消
- **编辑**：点击行「编辑」→ 弹窗打开（回填数据）→ 修改 → 确定（更新）
- **删除**：点击行「删除」→ 确认 → 删除记录

## 页面状态
- **加载中**：el-table loading 遮罩
- **空数据**：当前环境无数据（共 0 条），表格显示 el-empty
- **弹窗**：单例模式（同一时间只有一个弹窗可见）

## 依赖
- 接口：CRUD API（推测 /api/production/shift-team-config）
- 上游页面：无
- 下游页面：无

## 与同类 CRUD 页面的差异
| 特征 | 典型 CRUD | 本页面 |
|------|----------|--------|
| 数据量 | 有数据 | **0条**（测试环境无种子数据） |
| 表单复杂度 | 3-5字段 | 6字段 |
| 排班类型 | el-select | **el-input**（未使用 el-select 组件） |
