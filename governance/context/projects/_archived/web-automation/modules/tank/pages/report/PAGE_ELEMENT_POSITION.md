# PAGE_ELEMENT_POSITION — tank / report

> 基于 PAGE_CONTEXT (Selenium 实测 DOM) | 2026-06-11
> 页面类型: 统计卡片 + 趋势图(ECharts/G2) — 轻量页面

## 筛选区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 储罐选择 | XPATH | `//div[contains(@class,'el-select')][.//input[@placeholder*='储罐']]` | B | el-select |
| 日期选择 | XPATH | `//div[contains(@class,'el-date-editor')]//input` | B | el-date-picker |
| 导出按钮 | XPATH | `//button[.//span[text()='导出']]` | A | |

## 统计卡片区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 今日进气量 | XPATH | `//div[contains(@class,'stat-card')][.//span[contains(.,'进气量')]]//span[contains(@class,'value')]` | B | |
| 今日出气量 | XPATH | `//div[contains(@class,'stat-card')][.//span[contains(.,'出气量')]]//span[contains(@class,'value')]` | B | |
| 当前库存量 | XPATH | `//div[contains(@class,'stat-card')][.//span[contains(.,'库存量')]]//span[contains(@class,'value')]` | B | |

## 趋势图区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 图表容器 | CSS | `.chart-container` | A | canvas/SVG渲染 |
| 近7天Tab | XPATH | `//div[contains(@class,'tab')]//span[contains(.,'近7天')]` | B | |
| 近15天Tab | XPATH | `//div[contains(@class,'tab')]//span[contains(.,'近15天')]` | B | |
| 近30天Tab | XPATH | `//div[contains(@class,'tab')]//span[contains(.,'近30天')]` | B | |

## 趋势图断言策略

图表为 ECharts/G2 canvas 渲染，不支持 DOM 直接断言。三级降级策略：
1. **canvas 数据提取**: JS `echarts.getInstanceByDom().getOption()` 获取 series data
2. **SVG 降级**: 如 ECharts 配置为 SVG 渲染，读取 SVG text 元素
3. **图例兜底**: 校验图表图例文字和颜色

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-11 -->
