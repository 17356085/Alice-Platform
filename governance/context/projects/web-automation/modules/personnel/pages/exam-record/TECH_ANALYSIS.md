好的，收到。模块: `personnel`，页面: `exam-record`。基于您提供的占位符分析和常见 Element Plus 后台布局，我将输出技术分析文档。

> ⚠️ 注意：由于缺少真实 HTML 源码和截图，以下分析基于**标准 Element Plus 组件结构和通用业务布局**进行预测。定位器值在真实页面上可能需调整。

---

# TECH_ANALYSIS.md

**页面**: `exam-record`（考试记录）  
**技术栈**: Vue 3 + Element Plus + Selenium 4.15.2  
**分析版本**: 1.0 (基于预测)  
**生成日期**: 2026-06-18

---

## 1. Element Plus 组件识别（预测）

| 组件 | 数量 | 用途 |
|------|------|------|
| `el-input` | 1 | 搜索“人员姓名”输入框 |
| `el-date-picker` | 1 | 搜索“考试日期”范围选择 |
| `el-select` | 2 | 搜索“考试类型”、“状态”下拉选择 |
| `el-table` | 1 | 展示考试记录列表 |
| `el-table-column` | ≥5 | 姓名、类型、成绩、结果、操作列 |
| `el-button` | ≥3 | 搜索、重置、导出（可能还有行内查看/编辑） |
| `el-pagination` | 1 | 表格分页 |
| `el-dialog` | 1 | “查看详情”弹窗（内嵌表单） |
| `el-tag` | 1 | 考试结果（通过/未通过）状态标签 |

---

## 2. DOM 结构分析（预测层级）

```
<div id="app">
  <div class="page-container">
    <!-- 搜索区 -->
    <div class="search-area">
      <el-form>
        <el-form-item label="人员姓名">
          <el-input placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="考试日期">
          <el-date-picker type="daterange" />
        </el-form-item>
        <el-form-item label="考试类型">
          <el-select placeholder="请选择考试类型" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select placeholder="请选择状态" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary">搜索</el-button>
          <el-button>重置</el-button>
        </el-form-item>
      </el-form>
    </div>
    <!-- 操作按钮区 -->
    <div class="action-bar">
      <el-button type="primary" icon="Download">导出</el-button>
    </div>
    <!-- 表格区 -->
    <el-table>
      <el-table-column prop="personName" label="人员姓名" />
      <el-table-column prop="examType" label="考试类型" />
      <el-table-column prop="score" label="成绩" />
      <el-table-column prop="result" label="结果">
        <template #default="scope">
          <el-tag :type="scope.row.result === '通过' ? 'success' : 'danger'">
            {{ scope.row.result }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default>
          <el-button type="text" size="small">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
    <!-- 分页 -->
    <el-pagination layout="total, sizes, prev, pager, next, jumper" />
  </div>
</div>
<!-- 弹窗挂载在 body -->
```

**关键特征**:
- 搜索区使用 `el-form` 包裹，每个 `el-form-item` 有 `label` 属性，可用于定位。
- 表格列使用 `prop` 数据绑定，`label` 属性作为表头文字。
- 弹窗 (`el-dialog`) 被挂载到 `<body>` 下（Element Plus 默认 `append-to-body`）。
- 下拉选项 (`el-option`) 也渲染在 `<body>` 层级（`popper-append-to-body` 默认 true）。

---

## 3. 定位器设计表（A/B/C 三级）

| 元素ID (建议) | 元素描述 | 推荐定位策略 | 定位值 | 稳定性 | 备注 |
|---------------|----------|--------------|--------|--------|------|
| `search_person_name` | 人员姓名输入框 | CSS (placeholder) | `input[placeholder*='请输入姓名']` | A | 唯一 placeholder |
| `search_exam_date` | 考试日期范围选择器 | CSS (class + placeholder) | `.el-date-editor--daterange input` | B | 标准日期选择器，可能有多个同类元素，需结合所在 form-item |
| `search_exam_type` | 考试类型下拉 | CSS (label) | `.el-form-item:has(.el-form-item__label:text("考试类型")) .el-select` | B | 更稳定的方式：结合 label 文本 |
| `search_status` | 状态下拉 | CSS (同上) | `.el-form-item:has(.el-form-item__label:text("状态")) .el-select` | B | 同上 |
| `btn_search` | 搜索按钮 | XPATH (text) | `//button[.//span[text()='搜索']]` | A | 文本稳定 |
| `btn_reset` | 重置按钮 | XPATH (text) | `//button[.//span[text()='重置']]` | A | 文本稳定 |
| `btn_export` | 导出按钮 | XPATH (text) | `//button[.//span[text()='导出']]` | A | 可含图标，span 包含文本 |
| `table` | 表格容器 | CSS (class) | `.el-table` | A | |
| `table_header` | 表头行 | CSS | `.el-table__header-wrapper th` | B | 动态列顺序 |
| `table_row` | 表格行 | CSS | `.el-table__body-wrapper .el-table__row` | B | 动态 |
| `table_cell_姓名` | 某行中的姓名单元格 | XPATH (行内) | `//tr[contains(@class,'el-table__row')][{n}]/td[1]//div[@class='cell']` | C | 依赖列顺序 |
| `pagination` | 分页组件 | CSS (class) | `.el-pagination` | A | |
| `pagination_total` | 总记录数 | CSS (class) | `.el-pagination__total` | A | |
| `btn_view` (行内) | 查看按钮 | XPATH (text + 行内) | `//tr[contains(@class,'el-table__row')][{n}]//button[.//span[text()='查看']]` | B | 需要结合行索引 |
| `dialog_detail` | 详情弹窗 | CSS (class) | `.el-dialog` | A | 配合可选的标题 `aria-label` |
| `dialog_title` | 弹窗标题 | CSS (class) | `.el-dialog__title` | B | 文本内容：`考试记录详情` |
| `dialog_btn_confirm` | 弹窗确定按钮 | XPATH (text) | `//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]` | A | 限定在弹窗内 |
| `loading_mask` | 加载遮罩 | CSS (class) | `.el-loading-mask` | A | 加载中显示 |
| `date_picker_panel` | 日期选择面板 | CSS (class) | `.el-picker-panel` | B | 渲染在 body 层 |
| `select_dropdown` | 下拉选项列表 | CSS (class) | `.el-select-dropdown` | B | 渲染在 body 层 |

---

## 4. Vue 异步等待策略

| 场景 | 等待条件 | WebDriverWait 示例 | 说明 |
|------|----------|--------------------|------|
| 页面初始加载 | 表格出现 | `wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-table")))` | |
| 搜索/重置后 | loading 消失 + 表格数据刷新 | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-loading-mask")))` | 避免捕捉到旧数据 |
| 下拉框展开 | 下拉选项列表可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-select-dropdown")))` | 下拉面板渲染在 body |
| 日期选择器打开 | 日期面板可见 | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-picker-panel")))` | 同上 |
| 弹窗打开 | 弹窗可见（有动画） | `wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))` | Element Plus 弹窗带过渡 |
| 弹窗关闭 | 弹窗不可见 | `wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".el-dialog")))` | 点击确定后 |
| 表格行数量变化（如翻页） | 行元素重新加载 | 自定义条件：`wait.until(lambda d: len(d.find_elements(*TABLE_ROWS)) > 0)` | 翻页后行内容改变 |
| 导出下载 | 下载完成 | Selenium 无法直接等待，需结合文件系统监听或 API 方式 | 建议使用 `requests` 拦截导出请求 |

---

## 5. 自动化风险点

| 风险 | 影响 | 应对策略 |
|------|------|----------|
| `el-select` 下拉选项渲染在 `body` 层，不在触发元素内部 | 常规父级定位失败 | 使用 `.el-select-dropdown` 全局定位，结合选项文本 |
| `el-date-picker` 面板也在 `body` 层 | 定位困难 | 先点击输入框激活，再等待 `.el-picker-panel` 出现 |
| 表格行动态生成，无稳定 `data-row-key` | 难精确定位某行 | 结合行内文本/顺序，或给每个 `el-table-column` 添加 `class-name` 自定义属性 |
| 弹窗关闭动画未完成即操作其他元素 | 点击穿透或状态冲突 | 使用 `invisibility_of_element_located` 等待弹窗完全消失 |
| `el-tag` 背景色随状态变化（通过/未通过） | 无法用颜色断言 | 断言文本内容而非样式 |
| 搜索时输入框 `clearable` 导致输入后出现清除按钮 | 可能干扰后续输入 | 先清除再输入，或使用 `clear()` 方法 |
| Vue 动态 class 哈希（如 `el-input--suffix`） | CSS 选择器可能失效 | 优先使用属性选择器（如 `placeholder`、`aria-label`）而非 class |
| 导出按钮受权限控制，可能隐藏 | 定位不到元素 | 使用 `wait.until` + 超时返回 None 判断是否存在 |

---

## 6. 建议的定位器代码片段（示例，用于 PageObject）

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# 搜索区
SEARCH_NAME_INPUT = (By.CSS_SELECTOR, "input[placeholder*='请输入姓名']")
SEARCH_DATE_PICKER = (By.CSS_SELECTOR, ".el-date-editor--daterange input")
SEARCH_TYPE_SELECT = (By.XPATH, "//label[text()='考试类型']/../..//div[contains(@class,'el-select')]")
SEARCH_STATUS_SELECT = (By.XPATH, "//label[text()='状态']/../..//div[contains(@class,'el-select')]")
BTN_SEARCH = (By.XPATH, "//button[.//span[text()='搜索']]")
BTN_RESET = (By.XPATH, "//button[.//span[text()='重置']]")
BTN_EXPORT = (By.XPATH, "//button[.//span[text()='导出']]")

# 表格
TABLE = (By.CSS_SELECTOR, ".el-table")
TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body-wrapper .el-table__row")
TABLE_LOADING = (By.CSS_SELECTOR, ".el-loading-mask")

# 分页
PAGINATION = (By.CSS_SELECTOR, ".el-pagination")

# 弹窗
DIALOG = (By.CSS_SELECTOR, ".el-dialog")
DIALOG_TITLE = (By.CSS_SELECTOR, ".el-dialog__title")
DIALOG_CONFIRM = (By.XPATH, "//div[contains(@class,'el-dialog')]//button[.//span[text()='确定']]")

# 下拉面板（body层）
SELECT_DROPDOWN = (By.CSS_SELECTOR, ".el-select-dropdown")
SELECT_OPTION = (By.CSS_SELECTOR, ".el-select-dropdown__item")

# 日期面板
DATE_PANEL = (By.CSS_SELECTOR, ".el-picker-panel")
```

---

## 7. 与 BasePage 的集成建议

- 利用 `wait_table_loaded()` 等待表格加载：检测 `TABLE_ROWS` 出现且 `TABLE_LOADING` 消失。
- 利用 `wait_dialog_visible()` 等待弹窗：`wait.until(EC.visibility_of_element_located(DIALOG))`
- 利用 `wait_loading_disappear()` 处理搜索/翻页时的 loading 遮罩。
- 对于 `el-select`，推荐在 `ElementPlusHelper` 中封装 `select_option_by_label(driver, trigger_locator, option_text)`，自动处理点击触发展开 → 等待下拉面板 → 点击选项的逻辑。
- 对于 `el-date-picker`，封装 `set_date_range(driver, input_locator, start_date, end_date)`，通过 JS 直接设置 `el-date-picker` 的 `value` 属性可避免复杂交互。

---

> ℹ️ 此分析基于预测的页面结构。真实页面上可能有所不同，请务必基于实际 HTML 和截图进行验证调整。定位器稳定性评级 (A/B/C) 仅代表在 Elment Plus 组件标准写法下的预估可靠性。