# TECH_ANALYSIS — tank / report

## 技术栈说明
- 同 monitor 页面：自定义 UI 组件体系（非 Element Plus）
- 统计卡片使用 `<div class="stat-item">`，与 monitor 一致
- 趋势图使用 ECharts / G2 等可视化库（具体待确认）

## 定位器设计表

| 元素 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|------|-------------|--------|--------|------|
| 储罐选择下拉框 | CSS | `.el-select` 或自定义下拉组件 | B | 需要确认实际 DOM |
| 日期选择器 | CSS | `input[type="text"]` 含日期占位 | B | 待确认 placeholder |
| 导出按钮 | XPATH | `//button[contains(.,"导出")]` | A | 文本匹配 |
| 进气量统计值 | XPATH | `//*[contains(text(),"今日进气量")]/preceding-sibling::*[1]` | B | |
| 出气量统计值 | XPATH | `//*[contains(text(),"今日出气量")]/preceding-sibling::*[1]` | B | |
| 库存量统计值 | XPATH | `//*[contains(text(),"当前库存量")]/preceding-sibling::*[1]` | B | |
| 近7天 Tab | XPATH | `//button[contains(.,"近7天")]` | A | 文本匹配 |
| 近15天 Tab | XPATH | `//button[contains(.,"近15天")]` | A | 文本匹配 |
| 近30天 Tab | XPATH | `//button[contains(.,"近30天")]` | A | 文本匹配 |

## 异步等待策略
- 切换储罐/日期后等待统计卡片数值更新（Vue 异步刷新）
- 切换趋势图 Tab 后等待图表渲染完成

## 自动化风险点
- 趋势图是 canvas/SVG 渲染，无法直接断言图表内容（只能断言 DOM 存在）
- 统计卡片数值来自后端接口，需接口配合断言
- 图表 Tab 切换是高频操作，需注意频繁请求导致的数据竞态
