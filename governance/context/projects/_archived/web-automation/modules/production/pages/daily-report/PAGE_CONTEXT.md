# PAGE_CONTEXT — production / daily-report

## 基本信息
- 页面ID：daily-report
- 页面名称：生产日报表
- 所属模块：生产管理（production）
- 页面入口：左侧菜单 → 生产管理 → 日报表管理
- 路由：`#/production/daily-report`
- 面包屑：首页 > 生产管理 > 生产日报表
- UI 框架：**Element Plus**（el-table / el-button / el-date-picker）

## 页面职责
- 按日期展示当日生产数据，覆盖产品、原料、公辅工程、冷剂消耗四大类
- 提供日报数据的查询、录入、补录、调整、趋势查看、导出、打印功能
- 页面为只读展示型，数据录入通过独立弹窗或子页面完成

## 核心元素

### 搜索/操作区
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| date-picker | 日期选择器 | el-date-picker | 搜索区 | placeholder="请选择日期"，单日期选择 |
| btn-search | 查询按钮 | el-button (primary) | 搜索区 | 文字="查询" |
| btn-enter-data | 录入数据按钮 | el-button | 搜索区 | 文字="录入数据" |
| btn-supplement | 补录数据按钮 | el-button | 搜索区 | 文字="补录数据" |
| btn-adjust | 调整数据按钮 | el-button (warning) | 搜索区 | 文字="调整数据"，**默认 disabled**，需选中数据行后启用 |
| btn-trend | 趋势按钮 | el-button | 搜索区 | 文字="趋势"，可能打开图表弹窗 |
| btn-export | 导出按钮 | el-button | 搜索区 | 文字="导出" |
| btn-print | 打印按钮 | el-button | 搜索区 | 文字="打印" |

### 数据展示区（4 个分区卡片）

#### 1. 产品 (section-product)
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| table-product | 产品数据表格 | el-table (striped+border) | 产品区 | el-table--striped el-table--border |
| col-prod-category | 类别列 | text | 产品表 | |
| col-prod-name | 名称列 | text | 产品表 | |
| col-prod-unit | 单位列 | text | 产品表 | |
| col-prod-design | 设计值列 | number | 产品表 | |
| col-prod-actual | 实际值列 | number | 产品表 | |
| col-prod-sales | 销售量列 | number | 产品表 | |
| col-prod-inventory | 库存量列 | number | 产品表 | |
| col-prod-monthly-acc | 产量月累计列 | number | 产品表 | |

#### 2. 原料 (section-material)
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| table-material | 原料数据表格 | el-table (striped+border) | 原料区 | |
| col-mat-category | 类别列 | text | 原料表 | |
| col-mat-name | 名称列 | text | 原料表 | |
| col-mat-unit | 单位列 | text | 原料表 | |
| col-mat-design | 设计值列 | number | 原料表 | |
| col-mat-actual | 实际值列 | number | 原料表 | |
| col-mat-lng-design | LNG单耗设计值列 | number | 原料表 | |
| col-mat-lng-actual | LNG单耗实际值列 | number | 原料表 | |
| col-mat-monthly-acc | 产量月累计列 | number | 原料表 | |

#### 3. 公辅工程 (section-utilities)
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| table-utilities | 公辅工程数据表格 | el-table (striped+border) | 公辅工程区 | |
| col-util-category | 类别列 | text | 公辅工程表 | |
| col-util-name | 名称列 | text | 公辅工程表 | |
| col-util-unit | 单位列 | text | 公辅工程表 | |
| col-util-design | 设计值列 | number | 公辅工程表 | |
| col-util-actual | 实际值列 | number | 公辅工程表 | |
| col-util-lng-design | LNG单耗设计值列 | number | 公辅工程表 | |
| col-util-lng-actual | LNG单耗实际值列 | number | 公辅工程表 | |
| col-util-monthly-acc | 产量月累计列 | number | 公辅工程表 | |

#### 4. 冷剂消耗 (section-refrigerant)
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| table-refrigerant | 冷剂消耗数据表格 | el-table (striped+border) | 冷剂消耗区 | |
| col-ref-category | 类别列 | text | 冷剂消耗表 | |
| col-ref-name | 名称列 | text | 冷剂消耗表 | |
| col-ref-unit | 单位列 | text | 冷剂消耗表 | |
| col-ref-design | 设计值列 | number | 冷剂消耗表 | |
| col-ref-actual | 实际值列 | number | 冷剂消耗表 | |
| col-ref-monthly-acc | 产量月累计列 | number | 冷剂消耗表 | |

### 弹窗/对话框（✅ 已实地验证 2026-06-12）

#### 1. 录入数据弹窗 (dialog-enter-data)
| 元素ID | 元素描述 | 控件类型 | 备注 |
|--------|----------|----------|------|
| dialog-enter | 弹窗容器 | el-dialog | 标题="录入数据" |
| enter-device-select | 装置选择下拉 | el-select | 选项含：1#装置, 2#装置, LNG装置, 液氮后备装置, 脱盐水补水/供水, 循环水给水/回水 |
| enter-btn-cancel | 取消按钮 | el-button | 文字="取消" |
| enter-btn-confirm | 确定按钮 | el-button (primary) | 文字="确定"，点击后 toast "录入成功" |

#### 2. 补录数据弹窗 (dialog-supplement-data)
| 元素ID | 元素描述 | 控件类型 | 备注 |
|--------|----------|----------|------|
| dialog-supplement | 弹窗容器 | el-dialog | 标题="补录数据" |
| supplement-device-select | 装置选择下拉 | el-select | placeholder="请选择需要补录的装置" |
| supplement-btn-cancel | 取消按钮 | el-button | 文字="取消" |
| supplement-btn-confirm | 确定按钮 | el-button (primary) | 文字="确定" |

#### 3. 趋势分析弹窗 (dialog-trend-analysis)
| 元素ID | 元素描述 | 控件类型 | 备注 |
|--------|----------|----------|------|
| dialog-trend | 弹窗容器 | el-dialog | 标题="趋势分析" |
| trend-start-date | 开始日期 | el-date-picker | placeholder="开始日期" |
| trend-end-date | 结束日期 | el-date-picker | placeholder="结束日期" |
| trend-text | 文本输入框 | el-input | type="text" |
| trend-btn-query | 查询按钮 | el-button | 文字="查询" |

#### 4. 导出弹窗 (dialog-export)
| 元素ID | 元素描述 | 控件类型 | 备注 |
|--------|----------|----------|------|
| dialog-export | 弹窗容器 | el-dialog | 标题="生产日报表" |
| export-device-select | 装置选择下拉 | el-select | placeholder="请选择需要导出的装置" |
| export-btn-cancel | 取消按钮 | el-button | 文字="取消" |
| export-btn-confirm | 确认导出按钮 | el-button (primary) | 文字="确认导出" |

## 关键交互
- **日期查询**：选择日期 → 点击「查询」→ 四个分区表格异步刷新
- **录入数据**：点击「录入数据」→ 弹出录入表单 → 填写 → 确认 → 表格刷新 + toast
- **补录数据**：点击「补录数据」→ 弹出补录表单（可能含历史日期选择）
- **调整数据**：点击「调整数据」→ 弹出调整表单（可能含调整原因字段）
- **趋势查看**：点击「趋势」→ 可能弹窗展示折线图/柱状图（canvas/SVG）
- **导出**：点击「导出」→ 可能触发文件下载
- **打印**：点击「打印」→ 可能调用 `window.print()` 或打开打印预览

## 页面状态
- **加载中**：el-table 显示 loading 遮罩（el-loading-mask），数据异步请求期间
- **空数据**：当日无生产数据时，表格可能显示空状态（el-table__empty-block）
- **错误状态**：接口异常时可能有 error toast 或表格区域显示错误提示
- **日期未选择**：默认显示当天数据？或需手动选择日期后查询

## 权限与角色
- 可见角色：生产管理人员、系统管理员
- 可操作角色：
  - 查询：所有可见角色
  - 录入/补录/调整：生产操作员、生产管理人员（需编辑权限）
  - 导出/打印：所有可见角色
- 特殊限制：待实地确认（可能需要根据登录角色验证按钮显隐）

## 特殊行为
- **异步加载**：四个分区表格数据根据日期异步加载，查询后同时刷新
- **无分页**：每日数据固定条目数，不涉及翻页
- **表格结构**：el-table 带 striped+border 样式，固定列不涉及滚动
- **数据联动**：四个分区的数据由同一日期参数驱动，切换日期后全部同步刷新
- **⚠️ 待确认**：录入/补录/调整 对应的弹窗结构和表单字段

## 依赖
- 接口：待确认（推测 GET/POST /api/production/daily-report?date=xxx）
- 上游页面：无直接上游
- 下游页面：无（功能自包含）

## 与现有模块的差异
| 特征 | 典型 Element Plus 页面 | 本页面 |
|------|----------------------|--------|
| 表格数量 | 1 个 el-table | **4 个 el-table**（分区展示） |
| 搜索区 | 表单行内排列 | 日期选择器 + 操作按钮栏 |
| 分页 | 通常有 el-pagination | **无分页** |
| 新增入口 | 表格上方「新增」按钮 | 「录入数据」按钮（待确认弹窗/页面跳转） |
