# PAGE_CONTEXT — production / monthly-report

## 基本信息
- 页面ID：monthly-report
- 页面名称：生产月报表
- 所属模块：生产管理（production）
- 页面入口：左侧菜单 → 生产管理 → 生产月报表
- 路由：`#/production/monthly-report`
- 面包屑：首页 > 生产管理 > 生产月报表
- UI 框架：**Element Plus** + 自定义月份导航器（`month-nav` / `current-month`）
- 页面容器：`monthly-report-container`

## 页面职责
- 按月展示生产统计数据（产品/原料/公辅工程/冷剂消耗四类）
- 月份选择通过自定义 ← → 箭头导航器（非 el-date-picker）
- 提供月报的趋势查看、导出、打印功能
- **纯只读页面**，无数据录入功能

## 核心元素

### 月份选择区（自定义 month-nav）
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| btn-prev-month | 上一月按钮 | el-button (is-circle) | 月份导航 | 左侧箭头 `←` |
| current-month | 当前月份显示 | span.current-month | 月份导航 | 格式="2026年5月" |
| btn-next-month | 下一月按钮 | el-button (is-circle) | 月份导航 | 右侧箭头 `→` |

### 操作按钮
| 元素ID | 元素描述 | 控件类型 | 所在区域 | 备注 |
|--------|----------|----------|----------|------|
| btn-generate | 生成报表按钮 | el-button (primary) | 操作区 | **初始 disabled**，切换月份后可能启用 |
| btn-trend | 趋势按钮 | el-button | 操作区 | 文字="趋势" |
| btn-export | 导出按钮 | el-button | 操作区 | 文字="导出" |
| btn-print | 打印按钮 | el-button | 操作区 | 文字="打印" |

### 统计卡片区（3个指标卡片）
| 元素ID | 元素描述 | 控件类型 | 备注 |
|--------|----------|----------|------|
| stat-lng-monthly | LNG月产量 | stat-card | -1771.32t（数值示例） |
| stat-lin-monthly | 液氮月产量 | stat-card | 1991.68t |
| stat-gas-monthly | 脱碳气月产量 | stat-card | 14211.71t |

### 数据展示区（4 个分区卡片）

#### 1. 产品 (section-product)
| 列 | 名称 | 类型 |
|:--:|------|:----:|
| 1 | 类别 | text |
| 2 | 名称 | text |
| 3 | 单位 | text |
| 4 | 实际值 | number |
| 5 | 设计值 | number |
| 6 | 产量月累计 | number |
| 7 | 备注 | text |

#### 2. 原料 (section-material)
| 列 | 名称 | 类型 |
|:--:|------|:----:|
| 1 | 类别 | text |
| 2 | 名称 | text |
| 3 | 单位 | text |
| 4 | 实际值 | number |
| 5 | 产量月累计 | number |
| 6 | 备注 | text |

#### 3. 公辅工程 (section-utilities)
同原料表 6 列结构

#### 4. 冷剂消耗 (section-refrigerant)
同原料表 6 列结构

## 关键交互
- **月份切换**：点击 ← / → 按钮 → 月份文字变化 → 表格数据刷新
- **生成报表**：切换月份后「生成报表」按钮启用 → 点击 → 当前月数据重新加载
- **趋势查看**：点击「趋势」→ 弹窗（含日期范围+图表）
- **导出**：点击「导出」→ 弹窗选择装置
- **打印**：点击「打印」→ 浏览器打印

## 特殊行为
- **自定义月份导航**：非 Element Plus 标准组件，用 `el-button.is-circle` + `span.current-month`
- **生成报表 disabled 逻辑**：初始加载时 disabled；切换月份后启用
- **统计卡片**：页面顶部展示 3 个核心月产量指标
- **表格列数**：产品 7 列，其余 3 区 6 列（均含备注列）

## 与 daily-report 的差异
| 特征 | 日报表 | 月报表 |
|------|--------|--------|
| 时间维度 | 日（el-date-picker） | 月（自定义 month-nav） |
| 操作按钮 | 7个（录入/补录/调整/趋势/导出/打印/查询） | 4个（生成报表/趋势/导出/打印） |
| 统计卡片 | 无独立卡片 | 3个月产量卡片 |
| 表格列 | 8列（含销售量/库存量） | 6-7列（含备注） |
| 数据录入 | 支持录入/补录/调整 | 纯只读 |
