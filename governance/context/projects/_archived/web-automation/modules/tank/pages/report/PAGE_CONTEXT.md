# PAGE_CONTEXT — tank / report

## 基本信息
- 页面ID：tank-report
- 页面名称：储罐日报表
- 所属模块：储罐管理（tank）
- 页面入口：左侧菜单 → 储罐管理 → 储罐日报表
- 路由：`#/tank/report`

## 页面职责
- 按储罐+日期维度展示每日进气量、出气量、库存量统计
- 提供近7日/15日/30日趋势图可视化

## 核心元素

### 筛选区
| 元素ID | 元素描述 | 控件类型 | 区域 | 备注 |
|--------|----------|----------|------|------|
| select-tank | 选择储罐下拉框 | el-select | 筛选区 | 选项：全部储罐 / TANK-LNG-001 - LNG储罐 |
| date-picker | 选择日期 | el-date-picker | 筛选区 | 单日选择 |
| btn-export | 导出按钮 | el-button | 筛选区 | 文字="导出" |

### 统计卡片区
| 元素ID | 元素描述 | 控件类型 | 区域 | 备注 |
|--------|----------|----------|------|------|
| stat-intake | 今日进气量 | el-statistic / text | 统计卡片 | 单位：t（吨），e.g. 0 t |
| stat-outgas | 今日出气量 | el-statistic / text | 统计卡片 | 单位：t，e.g. 0 t |
| stat-inventory | 当前库存量 | el-statistic / text | 统计卡片 | 单位：t，e.g. 3,775 t |

### 趋势图区
| 元素ID | 元素描述 | 控件类型 | 区域 | 备注 |
|--------|----------|----------|------|------|
| trend-chart | 近7日趋势图 | 图表组件（ECharts / G2） | 图表区 | 可视化曲线 |
| tab-7d | 近7天Tab | el-tab / button | 图表区 | 默认选中 |
| tab-15d | 近15天Tab | el-tab / button | 图表区 | 切换显示15天趋势 |
| tab-30d | 近30天Tab | el-tab / button | 图表区 | 切换显示30天趋势 |

## 关键交互
- 选择储罐 → 选择日期 → 统计卡片和趋势图联动刷新
- 点击导出 → 下载日报表 Excel/PDF
- 切换趋势图时间段（7天/15天/30天）

## 权限与角色
- 可见角色：admin、储罐管理员
- 可操作角色：admin（全部）、储罐管理员（导出受限？）
- 特殊限制：操作工可能不可见

## 特殊行为
- 异步加载：切换储罐/日期后数据异步刷新，loading 遮罩
- 动态渲染：趋势图使用 ECharts / G2 可视化库渲染
- 前端校验：日期范围合法性

## 依赖
- 接口：GET /api/tank/report?tankId=&date=, GET /api/tank/report/export
- 上下游页面：上游=储罐监控管理（tank/monitor）

## 治理备注
- 本文件于 2026-06-11 基于 Selenium 实际页面抓取更新
- 元素信息来源于 headless Chrome 渲染后的 DOM 分析
- 趋势图组件细节（是否可交互缩放、数据点详情Tooltip）需进一步确认
