# PAGE_ELEMENT_POSITION — lab / gas-analysis-report

> 基于 PAGE_CONTEXT + GasAnalysisReportPage.py 代码提取 | 2026-06-12
> A级=稳定属性 / B级=CSS Selector / C级=XPath保底

## 取样位置标签栏

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 标签栏容器内Tab | XPATH | `//div[contains(@class,"tab") or contains(@class,"tag")]//*[contains(normalize-space(.),"{text}")]` | B | 优先策略，精确定位 |
| 全局Tab（排除菜单/表格） | XPATH | `//*[contains(normalize-space(.),"{text}") and not(ancestor::table)][not(ancestor::nav) and not(ancestor::ul[contains(@class,"el-menu")])]` | C | 保底策略 |
| 当前选中Tab | CSS | `.el-tabs__item.is-active, [class*="tab"][class*="active"], [class*="tag"][class*="active"]` | B | 蓝色下划线标识 |
| 已知位置列表（22个） | — | 界区原料气 / 除雾除尘出口原料气 / 脱油脱萘 / 低温水洗塔 / 甲烷化产品气 / 精脱硫1A / 精脱硫1B / 精脱硫2A / 精脱硫2B / 超精入口 / 超精出口 / 冷箱入口原料气 / 富氢 / 富氮 / LNG冷箱 / LNG储罐 / LNG装车站 / 制冷剂 / 合成氨入塔气 / 合成氨出塔气 / 液氨 / 加样 | — | 硬编码列表，用于存在性检查 |

## 搜索/筛选区

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 开始日期 | CSS | `input[placeholder*="开始日期"]` | A | placeholder 稳定 |
| 结束日期 | CSS | `input[placeholder*="结束日期"]` | A | placeholder 稳定 |
| 日期选择器图标 | CSS | `.el-date-editor .el-icon-date, .el-date-editor .el-input__prefix .el-icon` | B | 触发日期面板 |
| 查询按钮（主） | CSS | `.search-form .el-button--primary:first-of-type, .el-form .el-button--primary` | B | 双策略CSS |
| 查询按钮（保底） | XPATH | `//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"查询")]/parent::button` | A | 文本匹配保底 |
| 重置按钮（主） | CSS | `.search-form .el-button--default, .el-form .el-button:not(.el-button--primary):first-of-type` | B | 双策略CSS |
| 重置按钮（保底） | XPATH | `//button[not(contains(@class,"el-button--primary"))]//span[contains(normalize-space(.),"重置")]/parent::button` | A | 文本匹配保底 |

## 工具栏

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 新增按钮（主） | CSS | `.toolbar .el-button--primary, button.el-button--primary:has(.el-icon-plus), .el-button--primary .el-icon-plus` | B | 多策略CSS |
| 新增按钮（保底） | XPATH | `//button[contains(@class,"el-button--primary")]//span[contains(normalize-space(.),"新增")]/parent::button` | A | 文本匹配 |
| 导出按钮（主） | CSS | `button.el-button--default .el-icon-download, .toolbar .el-button--default:last-of-type` | B | 多策略CSS |
| 导出按钮（保底） | XPATH | `//button[contains(@class,"el-button")]//span[contains(normalize-space(.),"导出")]/parent::button` | A | 文本匹配 |

## 侧边栏导航

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 父级菜单（化验室取样） | XPATH | `//span[normalize-space(.)="{text}"]` | A | SidebarNavigator 统一使用 |
| 菜单链接 | CSS | `a[href="{route}"]` | A | route=#/lab/gas/report |

## 数据表格

> ⚠️ 实测：本页表格为自定义 `<table class="report-table">`，**不是** Element Plus el-table。
> 表头有两行：第一行 `group-header`（分组标题），第二行为具体列名。定位器取 `thead tr:last-child th`。

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 表格容器 | CSS | `.table-wrapper .report-table` | A | 自定义 report-table |
| 表头（首选） | CSS | `thead tr:last-child th` | A | 取最后一行，兼容多行表头 |
| 表头（EP降级） | CSS | `.el-table__header-wrapper th .cell` | B | 标准 EP 页面保底 |
| 数据行（首选） | CSS | `tbody tr:not(.group-header):not([class*=average]):not([class*=summary])` | B | 排除分组行和统计行 |
| 数据行（EP降级） | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | B | |
| 空数据提示 | CSS | `.el-table__empty-text, .el-table-empty, [class*=empty]` | B | |

## 统计行

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 统计行容器 | CSS | `tfoot tr, .el-table__footer-wrapper tr, tr.average-row, [class*="statistics"], [class*="average"]` | B | 多策略兼容 |
| 平均值标签 | — | 第一列文本="平均值" | — | |

## 弹窗 — 新增报告单

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| 弹窗标题 | — | "新增报告单" | — | 通过 BasePage._get_visible_dialog 获取 |
| 检验员* | BasePage API | `fill_dialog_input("检验员", value)` | A | 必填，label定位 |
| 复核员* | BasePage API | `fill_dialog_input("复核员", value)` | A | 必填，label定位 |
| 日期 | BasePage API | `fill_dialog_input("日期", value)` | A | el-date-picker |
| 取样时间 | BasePage API | `fill_dialog_input("取样时间", value)` | B | el-time-picker |
| 取样位置 | BasePage API | `select_dialog_dropdown("取样位置", value)` | B | el-select，默认"界区原料气" |
| 班组 | BasePage API | `select_dialog_dropdown("班组", value)` | B | el-select |
| 备注 | BasePage API | `fill_dialog_input("备注", value)` | B | el-textarea |
| 气体组分(13项) | BasePage API | `fill_dialog_input("<气体名>", value)` | B | el-input-number，逐项填充 |
| 保存按钮 | BasePage API | `click_dialog_save()` | A | 文字："保存报告" |
| 取消按钮 | BasePage API | `click_dialog_cancel()` | B | 文字："取消" |

## Toast

| 元素 | 策略 | 定位值 | 等级 | 备注 |
|------|------|--------|:--:|------|
| Toast消息 | BasePage API | `wait_for_toast_text()` | A | 自动获取最新toast |

## 与 PO 差异注意点

| 差异 | PO预期 | 实测 | 定位影响 |
|------|--------|------|----------|
| 取样位置标签 | 非标准el-tabs，自定义Tab组件 | 蓝色下划线标识选中 | 不能用 `.el-tabs__item` 单一定位，需文本匹配 |
| 表格类型 | 可能为标准HTML table非el-table | 实测见THEAD/TBODY结构 | 所有表格定位器均双策略兼容 |
| 保存按钮文字 | "保存报告" 非 "确定" | 按钮文字特殊 | BasePage.click_dialog_save 用CSS不依赖文字，已兼容 |
| 导出按钮 | 可能被遮挡 | JS click 降级 | click_export 三层降级策略 |

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 -->
