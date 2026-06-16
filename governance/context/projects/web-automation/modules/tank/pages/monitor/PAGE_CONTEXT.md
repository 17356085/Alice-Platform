# PAGE_CONTEXT — tank / monitor

## 基本信息
- 页面ID：tank-monitor
- 页面名称：储罐监控管理
- 所属模块：储罐管理（tank）
- 页面入口：左侧菜单 → 储罐管理 → 储罐监控管理
- 路由：`#/tank/monitor`

## 页面职责
- 展示储罐列表总览，含统计卡片（总数/正常运行/检修/报警）
- 提供储罐信息的筛选、新增、导入导出功能
- 支持查看单个储罐详情和历史数据

## 核心元素

### 顶部统计卡片区
| 元素ID | 元素描述 | 控件类型 | 区域 | 备注 |
|--------|----------|----------|------|------|
| stat-total | 储罐总数（数值: 1） | el-statistic / text | 统计卡片 | 显示总量 |
| stat-normal | 正常运行（数值: 0） | el-statistic / text | 统计卡片 | 正常状态数 |
| stat-maintenance | 检修维护（数值: 0） | el-statistic / text | 统计卡片 | 检修中数量 |
| stat-alarm | 报警储罐（数值: 1） | el-statistic / text | 统计卡片 | 报警中数量 |

### 搜索/筛选区
| 元素ID | 元素描述 | 控件类型 | 区域 | 备注 |
|--------|----------|----------|------|------|
| search-input | 储罐名称/编号搜索框 | el-input | 搜索区 | placeholder="储罐名称/编号" |
| select-tank-type | 储罐类型筛选 | el-select | 搜索区 | 选项：LNG储罐/焦油罐/常压储罐/其他压力储罐 |
| select-medium-type | 介质类型筛选 | el-select | 搜索区 | 选项：液化天然气(LNG)/液氨/煤焦油/成品油 |
| select-run-status | 运行状态筛选 | el-select | 搜索区 | 选项：正常/预警/报警/检修 |
| btn-query | 查询按钮 | el-button | 搜索区 | 文字="查询" |
| btn-reset | 重置按钮 | el-button | 搜索区 | 文字="重置" |
| btn-add | 新增储罐按钮 | el-button | 工具栏 | 文字="新增储罐" |
| btn-import | 导入按钮 | el-button | 工具栏 | 文字="导入" |
| btn-export | 导出按钮 | el-button | 工具栏 | 文字="导出" |

### 储罐列表表格区
| 元素ID | 元素描述 | 控件类型 | 区域 | 备注 |
|--------|----------|----------|------|------|
| table | 储罐列表表格 | el-table（class="data-table"） | 表格区 | 11列 |
| col-tank-id | 储罐编号列 | text | 表格区 | e.g. TANK-LNG-001 |
| col-tank-name | 储罐名称列 | text | 表格区 | e.g. LNG储罐 |
| col-tank-type | 储罐类型列 | text | 表格区 | e.g. LNG储罐 |
| col-medium-type | 介质类型列 | text | 表格区 | e.g. LNG |
| col-capacity | 设计容量列 | text | 表格区 | e.g. 30600 m³ |
| col-liquid-level | 液位列 | text | 表格区 | e.g. 24.2% |
| col-pressure | 压力列 | text | 表格区 | e.g. 16.77 MPa |
| col-temperature | 温度列 | text | 表格区 | e.g. -160.2 ℃ |
| col-bog | BOG量列 | text | 表格区 | e.g. 0.05 Nm³/h |
| col-status | 运行状态列 | el-tag | 表格区 | 报警/正常/预警/检修 |
| col-actions | 操作列 | button group | 表格区 | 查看/历史数据/编辑 |

### 弹窗
| 元素ID | 元素描述 | 控件类型 | 区域 | 备注 |
|--------|----------|----------|------|------|
| dialog-detail | 储罐详情弹窗/抽屉 | el-dialog/drawer | 弹窗 | 点击"查看"触发 |
| dialog-history | 历史数据弹窗 | el-dialog | 弹窗 | 点击"历史数据"触发 |
| dialog-edit | 新增/编辑储罐弹窗 | el-dialog | 弹窗 | 点击"新增储罐"或"编辑"触发 |
| dialog-import | 导入弹窗 | el-dialog | 弹窗 | 点击"导入"触发 |

### 分页区
| 元素ID | 元素描述 | 控件类型 | 区域 | 备注 |
|--------|----------|----------|------|------|
| pagination | 分页器 | el-pagination | 底部 | 共1条，10/20/50条/页 |

## 关键交互
- 搜索 → 输入关键字/选择筛选条件 → 点击查询 → 表格异步刷新
- 重置 → 点击重置 → 清空所有筛选条件 → 表格恢复全量
- 查看详情 → 点击"查看"→ 详情弹窗/抽屉展开
- 历史数据 → 点击"历史数据"→ 趋势数据弹窗
- 新增储罐 → 点击"新增储罐"→ 新增表单弹窗
- 编辑 → 点击行内"编辑"→ 编辑表单弹窗
- 导入/导出 → 文件上传/下载操作

## 权限与角色
- 可见角色：admin、储罐管理员、操作工
- 可操作角色：admin（全部）、储罐管理员（除删除外）
- 特殊限制：操作工仅可查看

## 特殊行为
- 异步加载：表格数据、下拉选项异步加载；搜索后有 loading 遮罩
- 动态渲染：运行状态列使用 el-tag 动态着色（报警=红/正常=绿/预警=黄/检修=灰）
- 前端校验：新增/编辑表单有必填校验
- 后端校验：储罐编号唯一性校验

## 依赖
- 接口：GET /api/tank/list, POST /api/tank/add, PUT /api/tank/{id}, DELETE /api/tank/{id}, GET /api/tank/{id}/history, 导入POST /api/tank/import, 导出GET /api/tank/export
- 上下游页面：上游=设备台账（equipment），下游=储罐日报表（tank/report）

## 治理备注
- 本文件于 2026-06-11 基于 Selenium 实际页面抓取更新
- 元素信息来源于 headless Chrome 渲染后的 DOM 分析
- 弹窗内容（新增/编辑表单字段、导入格式）需进一步获取
