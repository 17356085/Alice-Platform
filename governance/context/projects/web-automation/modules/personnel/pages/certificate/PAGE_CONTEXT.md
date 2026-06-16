# PAGE_CONTEXT — personnel / certificate

## 基本信息
- 页面ID：certificate
- 页面名称：证书管理
- 所属模块：人员管理（personnel）→ 培训管理
- 页面入口：左侧菜单 → 人员管理 → 培训管理 → 证书管理
- 路由：`#/personnel/training/certificate`
- 自动化代码：待开发

## 页面职责
- 展示证书列表，支持按证书名称/状态搜索筛选
- 提供证书的新增、编辑、删除操作（标准 CRUD 管理页）
- 支持证书核发操作（批量/单条）

## 核心元素

### 搜索区
| 元素ID | 元素描述 | 控件类型 | 备注 |
|--------|----------|----------|------|
| search-cert-name | 证书名称搜索框 | el-input | placeholder="请输入证书名称" |
| search-status | 状态下拉筛选 | el-select | 状态枚举值 |
| search-btn | 查询按钮 | el-button | 文字="查询" |
| reset-btn | 重置按钮 | el-button | 文字="重置" |

### 表格区（10 列）
| 列序号 | 列名 | 控件类型 | 备注 |
|--------|------|----------|------|
| 1 | 编号 | text | 序号/ID |
| 2 | 证书名称 | text | 证书名称 |
| 3 | 证书编号 | text | 证书编号（系统生成或手动输入） |
| 4 | 持有人 | text | 关联用户名称 |
| 5 | 证书类型 | text/tag | 类型分类 |
| 6 | 颁发日期 | text | 日期格式 |
| 7 | 颁发机构 | text | 颁发机构名称 |
| 8 | 状态 | el-tag | 动态颜色标签（有效/过期/待核发等） |
| 9 | 认证标准 | text | 认证标准名称 |
| 10 | 操作 | buttons | 行内操作按钮（编辑/删除/核发等） |

### 操作按钮
| 元素ID | 元素描述 | 所在区域 | 定位策略 |
|--------|----------|----------|----------|
| add-btn | 新增证书按钮 | 表格上方 | `//button[.//span[normalize-space(.)="新增证书"]]` |
| issue-btn | 证书核发按钮 | 表格上方 | `//button[.//span[normalize-space(.)="证书核发"]]` |

### 新增/编辑弹窗
| 元素ID | 元素描述 | 控件类型 | 备注 |
|--------|----------|----------|------|
| dialog | 弹窗容器 | el-dialog | 标题="新增证书" / "编辑证书" |
| form-cert-name | 证书名称 | el-input | placeholder="请输入证书名称"，必填 |
| form-user | 用户 | el-input | placeholder="请输入用户名称"，用户搜索/选择 |
| form-cert-type | 证书类型 | el-select | 下拉选择 |
| form-issue-org | 颁发机构 | el-input | placeholder="请输入颁发机构" |
| form-issue-date | 颁发日期 | el-date-picker | placeholder="请选择颁发日期" |
| form-valid-start | 有效期-开始 | el-date-picker | placeholder="开始日期" |
| form-permanent | 永久有效 | el-switch/el-checkbox | 布尔开关 |
| form-remark | 备注 | el-input/textarea | placeholder="请输入备注" |
| dialog-cancel | 取消按钮 | el-button | 文字="取消" |
| dialog-confirm | 确定按钮 | el-button | 文字="确定" |

### 分页区
- 分页器：el-pagination，默认 10 条/页
- 当前数据：0 条（无测试数据）

## 关键交互
- 搜索 → 输入证书名称 + 选择状态 → 点击查询 → 表格异步刷新 + loading 遮罩
- 重置 → 清空搜索条件 → 表格恢复默认数据
- 新增 → 点击"新增证书" → 弹窗展开（8 个表单项）→ 填写 → 确定 → 表格刷新 + toast 提示
- 编辑 → 行内点击编辑 → 弹窗展开（预填数据）→ 修改 → 确定 → 行数据更新 + toast
- 删除 → 行内点击删除 → 确认弹窗 → 确定 → 行消失 + toast
- 核发 → 点击"证书核发" → 待确认（可能为批量操作入口 / 子标签页切换）

## 权限与角色
- 可见角色：admin、培训管理员（待确认）
- 可操作角色：admin、培训管理员（新增/编辑/删除/核发）
- 特殊限制：普通员工可能仅可查看与自己相关的证书

## 特殊行为
- 异步加载：表格数据 + 状态下拉选项异步加载；search 触发 loading 300-800ms
- 动态渲染：状态列使用 el-tag（有效=绿色/过期=红色/待核发=橙色）
- 日期选择：颁发日期 + 有效期使用 el-date-picker
- 前端校验：证书名称必填、用户必填、证书类型必选、颁发日期必选
- 空状态：表格无数据时显示 `el-empty` 组件（"暂无数据"）
- "证书核发"按钮行为待深入确认（可能为列表面板切换或批量核发流程）

## 依赖
- 接口：GET /api/certificate/list, POST /api/certificate/add, PUT /api/certificate/{id}, DELETE /api/certificate/{id}（待确认实际路径）
- 上下游页面：培训计划（plan，关联培训完成后生成证书）、个人学习档案（my-archive，展示证书汇总）
