# PAGE_ELEMENT_POSITION — production / daily-report

> **版本**: 1.0 | **创建**: 2026-06-12 | **基于**: 实地页面探查 HTML 分析
> 参考 Page Object: `ZJSN_Test-master526/page/production_page/DailyReportPage.py`（待生成）

## 定位策略优先级
- **A级**（优先）：placeholder / 唯一 class 组合 / data-* 属性
- **B级**（备选）：CSS Selector 基于 el-* class
- **C级**（保底）：XPath 文本匹配

---

## 1. 搜索/操作区

| 元素ID | 定位策略 | 定位值 | 评级 | 说明 |
|--------|----------|--------|------|------|
| date-picker | CSS | `input[placeholder='请选择日期']` | A | el-date-picker 的 input |
| btn-search | XPATH | `//button[contains(.,'查询')]` | C | 文字匹配，el-button--primary |
| btn-enter-data | XPATH | `//button[contains(.,'录入数据')]` | C | 文字匹配 |
| btn-supplement | XPATH | `//button[contains(.,'补录数据')]` | C | 带 el-button--success |
| btn-adjust | XPATH | `//button[contains(.,'调整数据')]` | C | 默认 disabled，带 el-button--warning |
| btn-trend | XPATH | `//button[contains(.,'趋势') and not(contains(.,'分析'))]` | C | 精确匹配，避免和弹窗内按钮冲突 |
| btn-export | XPATH | `//button[contains(.,'导出') and not(contains(.,'确认导出'))]` | C | 区分弹窗内按钮 |
| btn-print | XPATH | `//button[contains(.,'打印')]` | C | 文字匹配 |

---

## 2. 数据表格区（4 个分区卡片）

> 每个分区由 `el-card` 包裹，内含 `el-table`。卡片标题通过 `el-card__header` 中的 `section-title` 区分。

### 2.1 产品表 (section-product)

| 元素ID | 定位策略 | 定位值 | 评级 | 说明 |
|--------|----------|--------|------|------|
| card-product | XPATH | `//span[contains(@class,'section-title') and contains(.,'产品')]/ancestor::div[contains(@class,'el-card')]` | B | 通过标题定位卡片容器 |
| table-product | CSS | `.el-card:has(.section-title:contains('产品')) .el-table` | B | 或使用 XPATH 祖先定位 |
| table-product-rows | CSS | (同上) `tbody tr.el-table__row` | B | 表格数据行 |
| col-prod-category | CSS | (同上) `td:nth-child(1)` | B | 第1列-类别 |
| col-prod-name | CSS | (同上) `td:nth-child(2)` | B | 第2列-名称 |
| col-prod-unit | CSS | (同上) `td:nth-child(3)` | B | 第3列-单位 |
| col-prod-design | CSS | (同上) `td:nth-child(4)` | B | 第4列-设计值 |
| col-prod-actual | CSS | (同上) `td:nth-child(5)` | B | 第5列-实际值 |
| col-prod-sales | CSS | (同上) `td:nth-child(6)` | B | 第6列-销售量 |
| col-prod-inventory | CSS | (同上) `td:nth-child(7)` | B | 第7列-库存量 |
| col-prod-monthly-acc | CSS | (同上) `td:nth-child(8)` | B | 第8列-产量月累计 |

### 2.2 原料表 (section-material)

| 元素ID | 定位策略 | 定位值 | 评级 | 说明 |
|--------|----------|--------|------|------|
| card-material | XPATH | `//span[contains(@class,'section-title') and contains(.,'原料')]/ancestor::div[contains(@class,'el-card')]` | B | |
| table-material | CSS | (卡片内) `.el-table` | B | 同产品表结构 |
| col-mat-category | CSS | `td:nth-child(1)` | B | |
| col-mat-name | CSS | `td:nth-child(2)` | B | |
| col-mat-unit | CSS | `td:nth-child(3)` | B | |
| col-mat-design | CSS | `td:nth-child(4)` | B | |
| col-mat-actual | CSS | `td:nth-child(5)` | B | |
| col-mat-lng-design | CSS | `td:nth-child(6)` | B | LNG单耗设计值 |
| col-mat-lng-actual | CSS | `td:nth-child(7)` | B | LNG单耗实际值 |
| col-mat-monthly-acc | CSS | `td:nth-child(8)` | B | 产量月累计 |

### 2.3 公辅工程表 (section-utilities)

| 元素ID | 定位策略 | 定位值 | 评级 | 说明 |
|--------|----------|--------|------|------|
| card-utilities | XPATH | `//span[contains(@class,'section-title') and contains(.,'公辅工程')]/ancestor::div[contains(@class,'el-card')]` | B | |
| table-utilities | CSS | (卡片内) `.el-table` | B | 列结构同原料表 |

### 2.4 冷剂消耗表 (section-refrigerant)

| 元素ID | 定位策略 | 定位值 | 评级 | 说明 |
|--------|----------|--------|------|------|
| card-refrigerant | XPATH | `//span[contains(@class,'section-title') and contains(.,'冷剂消耗')]/ancestor::div[contains(@class,'el-card')]` | B | |
| table-refrigerant | CSS | (卡片内) `.el-table` | B | 6列（无销售量/库存量列） |
| col-ref-category | CSS | `td:nth-child(1)` | B | |
| col-ref-name | CSS | `td:nth-child(2)` | B | |
| col-ref-unit | CSS | `td:nth-child(3)` | B | |
| col-ref-design | CSS | `td:nth-child(4)` | B | |
| col-ref-actual | CSS | `td:nth-child(5)` | B | |
| col-ref-monthly-acc | CSS | `td:nth-child(6)` | B | 产量月累计 |

---

## 3. 弹窗/对话框

### 3.1 录入数据弹窗

| 元素ID | 定位策略 | 定位值 | 评级 | 说明 |
|--------|----------|--------|------|------|
| dialog-enter | XPATH | `//div[contains(@class,'el-dialog') and .//span[contains(@class,'el-dialog__title') and contains(.,'录入数据')]]` | B | 通过标题定位 |
| enter-device-select | XPATH | `//div[contains(@class,'el-dialog') and .//span[contains(.,'录入数据')]]//input` | B | 弹窗内输入框 |
| enter-btn-confirm | XPATH | `//div[contains(@class,'el-dialog') and .//span[contains(.,'录入数据')]]//button[contains(.,'确定')]` | C | |
| enter-btn-cancel | XPATH | `//div[contains(@class,'el-dialog') and .//span[contains(.,'录入数据')]]//button[contains(.,'取消')]` | C | |

### 3.2 补录数据弹窗

| 元素ID | 定位策略 | 定位值 | 评级 | 说明 |
|--------|----------|--------|------|------|
| dialog-supplement | XPATH | `//div[contains(@class,'el-dialog') and .//span[contains(.,'补录数据')]]` | B | |
| supplement-device-select | XPATH | (弹窗内) `//input[@placeholder='请选择需要补录的装置']` | A | placeholder 唯一匹配 |
| supplement-btn-confirm | XPATH | (弹窗内) `//button[contains(.,'确定')]` | C | |
| supplement-btn-cancel | XPATH | (弹窗内) `//button[contains(.,'取消')]` | C | |

### 3.3 趋势分析弹窗

| 元素ID | 定位策略 | 定位值 | 评级 | 说明 |
|--------|----------|--------|------|------|
| dialog-trend | XPATH | `//div[contains(@class,'el-dialog') and .//span[contains(.,'趋势分析')]]` | B | |
| trend-start-date | XPATH | (弹窗内) `//input[@placeholder='开始日期']` | A | placeholder 唯一 |
| trend-end-date | XPATH | (弹窗内) `//input[@placeholder='结束日期']` | A | placeholder 唯一 |
| trend-btn-query | XPATH | (弹窗内) `//button[contains(.,'查询')]` | C | |

### 3.4 导出弹窗

| 元素ID | 定位策略 | 定位值 | 评级 | 说明 |
|--------|----------|--------|------|------|
| dialog-export | XPATH | `//div[contains(@class,'el-dialog') and .//span[contains(.,'生产日报表')]]` | B | 标题="生产日报表" |
| export-device-select | XPATH | (弹窗内) `//input[@placeholder='请选择需要导出的装置']` | A | placeholder 唯一 |
| export-btn-confirm | XPATH | (弹窗内) `//button[contains(.,'确认导出')]` | C | |
| export-btn-cancel | XPATH | (弹窗内) `//button[contains(.,'取消')]` | C | |

---

## 4. 特殊关注

### 4.1 ⚠️ 调整数据按钮的 disabled 状态
- 初始加载时为 `is-disabled`，可能在选中表格行后启用
- 定位时需考虑 `:not(.is-disabled)` 筛选
- 如果该功能未实现（始终 disabled），则从测试范围中排除

### 4.2 ⚠️ 打印按钮触发浏览器原生打印
- `window.print()` 会弹出浏览器打印对话框，Selenium 无法操作
- 自动化测试中跳过打印按钮的实际点击验证
- 仅验证打印按钮存在且可点击即可

### 4.3 多表格同步刷新
- 查询/录入后会同时刷新 4 个表格
- 等待策略：监测 `el-loading-mask` 消失（全局等待）+ 任一表格数据变化确认

### 4.4 日期选择器的 Element Plus 渲染
- el-date-picker 的面板通过 Teleport 挂载在 `body` 下
- 选择日期时需使用 `body > .el-picker-panel` 定位面板
- 参考 EP-001 坑位
