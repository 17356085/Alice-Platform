# PAGE_ELEMENT_POSITION — tank / monitor

> 基于 PAGE_CONTEXT (Selenium 实测 DOM) | 2026-06-11
> ⚠️ 本页面使用自定义 UI 框架（非 Element Plus），定位器已调整为自定义 class 体系

## 统计卡片区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 储罐总数 | CSS+XPATH | `.stats-cards .stat-card:nth-child(1) .stat-value` | B | 按位置 |
| 正常运行 | CSS+XPATH | `.stats-cards .stat-card:nth-child(2) .stat-value` | B | |
| 检修维护 | CSS+XPATH | `.stats-cards .stat-card:nth-child(3) .stat-value` | B | |
| 报警储罐 | CSS+XPATH | `.stats-cards .stat-card:nth-child(4) .stat-value` | B | |

## 搜索/筛选区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 搜索输入框 | XPATH | `//input[@placeholder='储罐名称/编号']` | A | |
| 储罐类型下拉 | XPATH | `//div[contains(@class,'filter-item')][.//label[contains(.,'储罐类型')]]//select` | B | 自定义 select |
| 介质类型下拉 | XPATH | `//div[contains(@class,'filter-item')][.//label[contains(.,'介质类型')]]//select` | B | |
| 运行状态下拉 | XPATH | `//div[contains(@class,'filter-item')][.//label[contains(.,'运行状态')]]//select` | B | |
| 查询按钮 | XPATH | `//button[contains(.,'查询')]` | A | |
| 重置按钮 | XPATH | `//button[contains(.,'重置')]` | A | |
| 新增储罐 | XPATH | `//button[contains(.,'新增储罐')]` | A | |
| 导入 | XPATH | `//button[contains(.,'导入')]` | A | |
| 导出 | XPATH | `//button[contains(.,'导出')]` | A | |

## 数据表格 (自定义 data-table)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表格容器 | CSS | `table.data-table` | A | 原生 table |
| 表格行 | CSS | `table.data-table tbody tr` | B | |
| 储罐编号 | XPATH | `//tr[.//td[contains(.,'TANK-')]]/td[1]` | B | |
| 操作-查看 | XPATH | `.//button[contains(.,'查看')]` | A | per-row |
| 操作-历史数据 | XPATH | `.//button[contains(.,'历史数据')]` | A | per-row |
| 操作-编辑 | XPATH | `.//button[contains(.,'编辑')]` | A | per-row |
| 运行状态tag | XPATH | `.//span[contains(@class,'status-tag')]` | B | 自定义组件 |

## 分页 (Element Plus)

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 分页器 | CSS | `.el-pagination` | A | 仅此组件使用 EP |
| 总数 | CSS | `.el-pagination__total` | A | |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
