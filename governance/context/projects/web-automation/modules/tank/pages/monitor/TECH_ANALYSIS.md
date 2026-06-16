# TECH_ANALYSIS — tank / monitor

## 技术栈说明
- **UI 框架**：自定义组件体系（非 Element Plus），使用 scoped style（`data-v-1f09d3f9`）
- 与 equipment 模块不同，储罐管理模块使用独立的 CSS class 命名
- 定位器设计更简单：无 Element Plus teleport/overlay 问题

## 组件识别

| 组件类型 | 实际 HTML | 说明 |
|----------|-----------|------|
| 按钮 | `<button class="btn btn-primary/btn-success/btn-info/btn-default">` | 自定义按钮，防抖需自行实现 |
| 输入框 | `<input class="filter-input" placeholder="...">` | 普通文本框 |
| 下拉框 | 需进一步确认（页面加载时下拉框未展开） | 可能有 el-select 或原生 select |
| 表格 | `<table class="data-table">` | 原生 HTML 表格，非 el-table |
| 统计卡片 | `<div class="stats-cards"><div class="stat-card">` | 自定义卡片组件 |
| 分页器 | 自定义分页组件 | 非 el-pagination |

## 定位器设计表

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 搜索输入框 | CSS | `input.filter-input` | A | class 稳定 |
| 搜索输入框（备选） | CSS | `input[placeholder="储罐名称/编号"]` | A | placeholder 稳定 |
| 查询按钮 | CSS | `button.btn.btn-primary` | A | 唯一 primary 按钮 |
| 查询按钮（备选） | XPATH | `//button[contains(.,"查询")]` | A | 文本匹配 |
| 重置按钮 | CSS | `button.btn.btn-default` 含文本"重置" | B | 有多个 default 按钮 |
| 重置按钮（备选） | XPATH | `//button[contains(.,"重置")]` | A | 文本匹配 |
| 新增储罐 | CSS | `button.btn.btn-success` | A | 唯一 success 按钮 |
| 新增储罐（备选） | XPATH | `//button[contains(.,"新增储罐")]` | A | 文本匹配 |
| 导入按钮 | CSS | `button.btn.btn-info` | B | info 样式也可能用于其他 |
| 导入按钮（备选） | XPATH | `//button[contains(.,"导入")]` | A | 文本匹配 |
| 导出按钮 | XPATH | `//button[contains(.,"导出")]` | A | 文本匹配 |
| 统计卡片-总数 | CSS | `.stat-card:nth-child(1) .value` | B | 依赖顺序 |
| 统计卡片-正常运行 | CSS | `.stat-card:nth-child(2) .value` | B | |
| 统计卡片-检修维护 | CSS | `.stat-card:nth-child(3) .value` | B | |
| 统计卡片-报警储罐 | CSS | `.stat-card:nth-child(4) .value` | B | |
| 表格 | CSS | `table.data-table` | A | class 稳定 |
| 表头行 | CSS | `table.data-table thead tr` | A | |
| 表格行 | CSS | `table.data-table tbody tr` | A | |
| 查看按钮 | XPATH | `//button[contains(.,"查看")]` | A | 表格行内 |
| 历史数据按钮 | XPATH | `//button[contains(.,"历史数据")]` | A | 表格行内 |
| 编辑按钮 | XPATH | `//button[contains(.,"编辑")]` | A | 表格行内 |
| 页码按钮 | CSS | `button.page-btn` | B | |
| 页码-激活 | CSS | `button.page-btn.active` | A | |

## 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例 |
|------|---------|-------------------|
| 页面加载 | 表格出现 | `wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.data-table tbody tr")))` |
| 搜索查询后 | 表格行变化或空数据提示 | 等待旧行消失或新行出现（Vue 异步刷新） |
| 弹窗打开 | 弹窗可见 | 需识别弹窗具体 class（待补充） |
| 弹窗关闭 | 弹窗不可见 | 待补充 |

## 自动化风险点
- **非 Element Plus**：BasePage 中的 DIALOG/TOAST/TABLE_ROWS 等通用定位器不可用，需要自定义
- 自定义组件无统一的 loading 指示器，等待策略需依赖 DOM 变化
- scoped style `data-v-1f09d3f9` 可能随版本变化，不要用于定位
- 弹窗组件 class 未识别，需进一步获取
