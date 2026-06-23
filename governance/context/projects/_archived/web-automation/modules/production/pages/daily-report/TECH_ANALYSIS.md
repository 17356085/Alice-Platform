# TECH_ANALYSIS — production / daily-report

> 基于 DailyReportPage.py + PAGE_ELEMENT_POSITION.md | 2026-06-12
> 页面路由: `#/production/daily-report` | PO: `page/production_page/DailyReportPage.py`
> 页面特点：**4分区卡片 + 4弹窗**，无分页，Element Plus 标准 UI

## 分析对象
- 模块：production（生产管理）
- 页面：日报表管理
- PO 规模：41 个方法，基于实地 HTML 探查（2026-06-12）
- 测试结果：8 passed, 0 failed ✅

## Element Plus 组件识别

| 组件类型 | 用途 | 定位特点 |
|----------|------|----------|
| el-date-picker | 日期选择器 | placeholder="请选择日期"，面板 Teleport 到 body |
| el-button | 操作按钮栏（7个按钮） | primary/success/warning 颜色 + disabled 状态 |
| el-card | 4个分区卡片容器 | section-title 文本区分（产品/原料/公辅工程/冷剂消耗） |
| el-table (striped+border) | 4个分区数据表格 | 无分页，固定条目数 |
| el-dialog | 4种弹窗（录入/补录/趋势/导出） | ⚠️ 多弹窗可共存于DOM |
| el-select | 弹窗内装置下拉 | filterable + Teleport |
| el-tag | 可能用于数值高亮/异常标记 | 待确认 |

## 定位器设计表（从代码 + PAGE_ELEMENT_POSITION 提取）

### 搜索/操作区

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 日期选择器 | CSS | `input[placeholder="请选择日期"]` | A | el-date-picker |
| 查询按钮 | XPATH | `//button[contains(@class,"el-button--primary")][contains(.,"查询")]` | B | primary class + 文本 |
| 录入数据按钮 | XPATH | `//button[contains(.,"录入数据")]` | B | 文本匹配 |
| 补录数据按钮 | XPATH | `//button[contains(.,"补录数据")]` | B | 文本匹配 |
| 调整数据按钮 | XPATH | `//button[contains(.,"调整数据")]` | B | ⚠️ 默认 disabled |
| 趋势按钮 | XPATH | `//button[contains(.,"趋势") and not(contains(.,"分析"))]` | B | 排除弹窗内按钮 |
| 导出按钮 | XPATH | `//button[contains(.,"导出") and not(contains(.,"确认导出"))]` | B | 排除弹窗内按钮 |
| 打印按钮 | XPATH | `//button[contains(.,"打印")]` | B | 触发浏览器原生打印 |

### 数据分区（4个卡片）

| 元素 | 策略 | 定位值 | 稳定性 | 备注 |
|------|------|--------|--------|------|
| 分区卡片模板 | XPATH | `//*[contains(@class,"section-title") and contains(.,"{name}")]/ancestor::div[contains(@class,"el-card")]` | B | 参数化：产品/原料/公辅工程/冷剂消耗 |
| 卡片内表格 | CSS | `.el-table` | A | 相对卡片容器 |
| 表格行 | CSS | `.el-table__body-wrapper tbody tr.el-table__row` | B | |
| 表头 | CSS | `.el-table__header-wrapper th .cell` | A | |
| 空数据 | CSS | `.el-table__empty-block` | B | |

### 弹窗区（4种弹窗，通过标题区分）

| 弹窗 | 定位策略 | 定位值 | 稳定性 | 备注 |
|------|----------|--------|--------|------|
| 弹窗模板(标题) | XPATH | `//div[contains(@class,"el-dialog") and .//span[contains(@class,"el-dialog__title") and contains(.,"{title}")]]` | A | 参数化 |
| 录入-装置下拉 | XPATH | 弹窗内 `//input` | B | 弹窗内只有一个input |
| 录入-确定 | XPATH | 弹窗内 `//button[contains(.,"确定")]` | B | |
| 录入-取消 | XPATH | 弹窗内 `//button[contains(.,"取消")]` | B | |
| 补录-装置下拉 | XPATH | `//input[@placeholder="请选择需要补录的装置"]` | A | placeholder唯一 |
| 趋势-开始日期 | XPATH | `//input[@placeholder="开始日期"]` | A | 弹窗内 |
| 趋势-结束日期 | XPATH | `//input[@placeholder="结束日期"]` | A | 弹窗内 |
| 趋势-查询 | XPATH | 弹窗内 `//button[contains(.,"查询")]` | B | |
| 导出-装置下拉 | XPATH | `//input[@placeholder="请选择需要导出的装置"]` | A | placeholder唯一 |
| 导出-确认导出 | XPATH | 弹窗内 `//button[contains(.,"确认导出")]` | B | |
| 导出-取消 | XPATH | 弹窗内 `//button[contains(.,"取消")]` | B | |

## 已知技术难题

| 问题 | 影响 | 当前处理 |
|------|------|----------|
| 4个el-card包裹的el-table | 表格定位需先定位卡片容器，再相对查找表格 | `_SECTION_CARD_XPATH` 模板参数化 + 相对定位 |
| 多弹窗DOM共存 | 打开录入→关闭→打开补录，录入弹窗DOM可能未从body移除 | 每次操作前确保只有一个可见弹窗 |
| 调整按钮disabled | 功能可能未实现，需选中行后才启用 | 仅验证 disabled 状态，不测试点击 |
| 打印按钮浏览器原生dialog | Selenium 无法操作 | 仅验证按钮存在，不测试实际打印 |
| el-date-picker面板Teleport | 日期选择面板在body层 | WebDriverWait for `.el-picker-panel` |
| 4表格同步刷新 | 查询后需等待4个表格全部完成loading | `wait_loading_disappear()` 全局等待 |

## 异步等待策略

| 场景 | 等待条件 | 实现 |
|------|----------|------|
| 页面加载 | 4个分区卡片出现 | `is_section_visible()` 轮询4个分区 |
| 日期查询 | loading 遮罩消失 | `wait_loading_disappear()` |
| 弹窗打开 | el-dialog visible | `WebDriverWait` for dialog + 标题文本 |
| 弹窗关闭 | el-dialog invisible | `wait.until(EC.invisibility_of_element_located(DIALOG))` |
| 日期面板 | picker-panel body层可见 | `WebDriverWait` for `.el-picker-panel` |
| 录入成功 | toast 出现+消失 | `WebDriverWait` for toast message |

## 自动化代码映射

- Page Object：`page/production_page/DailyReportPage.py`（41个方法，4分区+4弹窗全覆盖）
- 测试脚本：`script/production/test_daily_report.py`（10用例，9 active + 1 skip）
- conftest：`script/production/conftest.py`（module级 driver_setup + daily_report_page fixture + 弹窗清理 teardown）
- 代码质量：✅ 继承BasePage、✅ 无绝对XPath、✅ time.sleep已替换为WebDriverWait、✅ 无print调试

---

<!-- status: complete | completed_by: ai-assistant | completed_at: 2026-06-12 | next_phase: Phase 3.5 | next_agent: automation-agent -->
