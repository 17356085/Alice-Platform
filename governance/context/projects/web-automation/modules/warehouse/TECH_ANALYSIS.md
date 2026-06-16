# TECH_ANALYSIS — warehouse（环保入库/出库）

> **状态**: Phase 3 技术分析 | **日期**: 2026-06-12
> **输入**: PAGE_CONTEXT(hazard-in-order/out-order) + Selenium 自动抓取 + BasePage API

---

## 技术栈说明

| 组件层 | 技术 | 定位策略 |
|--------|------|----------|
| 页面整体 | Vue 3 SPA | JS hash 导航 `window.location.hash` |
| 搜索/筛选区 | **自定义 Tailwind CSS** (`wh-filter-toolbar`) | ⚠️ 无 `el-form-item__label`，靠 placeholder+XPath |
| 表格 | 标准 `el-table` (class=`el-table--fit el-table--striped el-table--border`) | ✅ BasePage 通用定位器可用 |
| 弹窗 | 标准 `el-dialog` | ✅ BasePage `DIALOG` / `DIALOG_TITLE` / `DIALOG_SAVE` |
| 分页 | 标准 `el-pagination` | ✅ BasePage `TOTAL_COUNT` / `NEXT_PAGE` / `PREV_PAGE` |
| 表单字段(弹窗内) | 标准 `el-input` / `el-date-picker` | ✅ BasePage 元素操作可用 |
| 按钮 | 标准 `el-button--primary/default/danger/warning` | ✅ 文本+class 组合定位 |
| 状态标签 | 标准 `el-tag` | ✅ 按文本+颜色定位 |

> 📌 **结论**：混合框架页面。搜索区需自定义定位（与 [[tank-custom-ui-framework]] 同源），其余全部为标准 Element Plus，BasePage 通用定位器覆盖 80%。

---

## 组件识别

| 组件 | 实际 HTML class | 标准 Element Plus？ | 备注 |
|------|----------------|:-------------------:|------|
| 搜索区容器 | `wh-filter-toolbar` | ❌ 自定义 | 无 `el-form` / `el-form-item` |
| 查询按钮 | `el-button` | ✅ | 文本="查询" |
| 重置按钮 | `el-button` | ✅ | 文本="重置" |
| 新增入库按钮 | `el-button el-button--primary` | ✅ | 文本="新增入库"/"新增出库" |
| 流程状态下拉 | `el-select` + `el-select__input` | ✅ | 需展开后定位选项 |
| 经办人输入框 | `el-input__inner` placeholder="请输入经办人" | ✅ | 最稳定的定位方式 |
| 日期选择器 | `el-date-editor` + `el-input__inner` placeholder="选择日期" | ✅ | |
| 表格 | `el-table--fit el-table--striped el-table--border` | ✅ | 8列 |
| 表格行 | `el-table__row` | ✅ | BasePage `TABLE_ROWS` |
| 分页 | `el-pagination` | ✅ | 共N条 / 10,20,50,100条/页 |
| 弹窗A(新增) | `el-dialog` 920px | ✅ | 标题="新增入库"/"新增出库" |
| 弹窗B(选择危废品) | `el-dialog` (嵌套) | ✅ | 弹窗嵌套，需特殊处理 |
| 弹窗C(查看详情) | `el-dialog` / `el-drawer` | ✅ | 只读模式 |
| 行内查看按钮 | `el-button--primary is-link` | ✅ | 文字="查看" |
| 行内编辑按钮 | `el-button--warning is-link` | ✅ | 文字="编辑"，条件渲染 |
| 清空缓存 | `el-button--danger is-text is-has-bg` | ✅ | ⚠️ 全局浮动，`parent=N/A` |
| Toast | `el-message` | ✅ | BasePage `TOAST` / `TOAST_SUCCESS` / `TOAST_ERROR` |
| 加载遮罩 | `el-loading-mask` | ✅ | BasePage `LOADING_MASK` |

---

## 定位器设计表

### 搜索/筛选区

| 元素ID | A级定位（优先） | B级定位（备选） | C级定位（保底） | 稳定性 |
|--------|----------------|----------------|----------------|:--:|
| filter-handler | `//input[@placeholder='请输入经办人']` | `.wh-filter-toolbar input.el-input__inner[placeholder*='经办人']` | `(//input[contains(@class,'el-input__inner')])[2]` | A |
| filter-date | `//input[@placeholder='选择日期']` | `.wh-filter-toolbar input[placeholder='选择日期']` | `//input[contains(@class,'el-input__inner')][@placeholder='选择日期']` | A |
| filter-status | `//div[contains(@class,'wh-filter-toolbar')]//div[contains(@class,'el-select')][1]` | 待确认具体 CSS 路径 | `(//div[contains(@class,'el-select__wrapper')])[1]` | B |
| btn-query | `//button[contains(.,'查询')]` | `.wh-filter-toolbar button.el-button:first-child` | — | A |
| btn-reset | `//button[contains(.,'重置')]` | `.wh-filter-toolbar button.el-button:nth-child(2)` | — | A |

### 工具栏

| 元素ID | A级定位 | B级定位 | 稳定性 |
|--------|---------|---------|:--:|
| btn-add | `//button[contains(.,'新增入库')]` | `.wh-filter-toolbar button.el-button--primary` | A |

### 表格

| 元素ID | A级定位 | 来源 | 稳定性 |
|--------|---------|------|:--:|
| table-rows | `self.TABLE_ROWS` | BasePage 通用 | A |
| table-empty | `self.TABLE_EMPTY` | BasePage 通用 | A |
| col-status-tag | `//span[contains(@class,'el-tag')]` | 行内查找 | A |
| btn-view | `//button[contains(.,'查看')]` | 文本匹配 | A |
| btn-edit | `//button[contains(.,'编辑')]` | 文本匹配 | A |

### 弹窗A（新增入库/出库）

| 元素ID | A级定位 | 来源 | 稳定性 |
|--------|---------|------|:--:|
| dialog | `self.DIALOG` | BasePage 通用 | A |
| dialog-title | `self.DIALOG_TITLE` | BasePage 通用 | A |
| field-in-time | `//input[@placeholder='选择日期']` (弹窗内) | 弹窗内唯一日期选择器 | A |
| field-handler | `//input[@placeholder='请输入经办人']` (弹窗内) | 弹窗内唯一输入框 | A |
| btn-select-waste | `//button[contains(.,'选择危废品')]` | 文本匹配 | A |
| btn-submit | `self.DIALOG_SAVE` / `//button[contains(.,'提交申请')]` | BasePage 通用 / 文本匹配 | A |
| btn-cancel | `//button[contains(.,'取消')]` | 弹窗内取消按钮 | A |

### 弹窗B（选择危废品）

| 元素ID | A级定位 | 稳定性 |
|--------|---------|:--:|
| waste-filter-category | `//div[contains(@class,'el-dialog')][.//span[contains(.,'危废品分类')]]//div[contains(@class,'el-select')]` | B |
| waste-filter-name | `//input[@placeholder='搜索危废品名称']` (待确认placeholder) | A（确认后） |
| waste-table | 待抓取弹窗B具体结构 | — |
| waste-confirm | `//button[contains(.,'确定')]` | A |

### 弹窗C（查看详情）

| 元素ID | A级定位 | 稳定性 |
|--------|---------|:--:|
| view-dialog | `self.DIALOG` / `.el-dialog[aria-label*='查看入库单']` | A |
| status-tag | `//div[contains(@class,'el-dialog')]//span[contains(@class,'el-tag')]` | B |
| detail-table | 弹窗内 `.el-table` | A |

---

## 异步等待策略

| 场景 | 等待条件 | 实现方式 |
|------|---------|----------|
| **页面加载** | 表格列标题稳定（8列） | `self.wait_table_loaded()` (BasePage) |
| **页面加载(保底)** | `el-loading-mask` 消失 + `el-table__row` 出现 | `self._wait_loading_gone()` + `WebDriverWait` |
| **搜索查询后** | 表格行数变化 + loading 消失 | `self.wait_table_refresh()` |
| **弹窗A打开** | `.el-dialog` 可见且无 `display:none` | `self.wait_dialog_visible()` |
| **弹窗A关闭** | `.el-dialog` 消失或 `display:none` | `self.wait_dialog_close()` |
| **弹窗B(嵌套)** | 第二个 `.el-dialog` 可见 | ⚠️ 需先确认弹窗A已打开，再等待弹窗B |
| **弹窗B关闭** | 第二个 `.el-dialog` 消失 | 注意区分：弹窗A应保持打开 |
| **弹窗C打开** | `.el-dialog[aria-label*='查看']` 可见 | 点击"查看"后等待 |
| **提交申请后** | Toast 出现（成功/失败）+ 弹窗关闭 + 表格刷新 | `self.wait_toast()` → `self.wait_dialog_close()` → `self.wait_table_refresh()` |
| **审批流转后** | 表格行内 el-tag 文本变化 | `WebDriverWait` + `EC.text_to_be_present_in_element` |

### 弹窗嵌套特殊处理

```python
# 伪代码 — 弹窗A → 弹窗B → 弹窗B关闭 → 弹窗A保持
def select_waste_in_dialog(self):
    self.wait_dialog_visible()                    # 等待弹窗A
    self.click_element(self.BTN_SELECT_WASTE)     # 点击"选择危废品"
    self.wait_dialog_visible(timeout=10)          # 等待弹窗B（第二个 dialog）
    # ... 操作弹窗B ...
    self.click_element(self.WASTE_CONFIRM)        # 弹窗B确认
    self.wait_dialog_close()                      # 等待弹窗B关闭
    # 此时弹窗A应仍可见
    assert self.is_dialog_visible()
```

---

## 自动化风险点

| 风险 | 等级 | 缓解方案 |
|------|:----:|----------|
| **搜索区无 label**：`wh-filter-toolbar` 不包含标准 `el-form-item__label`，无法按标签定位 | 🔴 高 | 统一使用 `placeholder` 属性+XPath 定位 |
| **弹窗嵌套**：弹窗A中打开弹窗B，双层 `el-dialog` 同时存在 | 🔴 高 | 定位器限定了 `:not([style*="display:none"])`，需验证嵌套时正确性 |
| **动态行按钮**：`v-if` 控制"查看"与"编辑"按钮显隐 | 🟡 中 | 用 `find_elements` + 文本匹配，配合状态判断 |
| **Vue scoped style**：`data-v-*` 属性随构建变化 | 🟡 中 | 不依赖 `data-v-*` 定位 |
| **清空缓存按钮**：全局浮动，可能干扰弹窗操作 | 🟡 中 | 不主动触发；必要时 JS 隐藏 |
| **弹窗C结构未完全抓取**：4区块布局待 Selenium 实际进入确认 | 🟡 中 | 先实现基本定位，后续迭代补充 |
| **审批流跨页面**：提交后需切换到系统管理/待我审批 | 🟡 中 | 端到端测试需多页面 Page Object 协作 |

---

## BasePage 通用定位器适用性

| BasePage 属性 | 可用？ | 说明 |
|---------------|:------:|------|
| `DIALOG` | ✅ | 标准 el-dialog |
| `DIALOG_TITLE` | ✅ | |
| `DIALOG_SAVE` | ✅ | 对应"提交申请"按钮 |
| `DIALOG_CANCEL` | ✅ | 对应"取消"按钮 |
| `TOAST` / `TOAST_SUCCESS` / `TOAST_ERROR` | ✅ | 标准 el-message |
| `FORM_ERROR` | ✅ | 弹窗内表单校验 |
| `LOADING_MASK` | ✅ | 表格 loading |
| `MESSAGE_BOX` / `MESSAGE_BOX_CONFIRM` | ✅ | 删除确认等 |
| `TABLE_ROWS` | ✅ | 标准 el-table |
| `TABLE_EMPTY` | ✅ | |
| `TOTAL_COUNT` | ✅ | el-pagination |
| `NEXT_PAGE` / `PREV_PAGE` | ✅ | |
| `DROPDOWN_OPTIONS` | ⚠️ | el-select 选项，需确认 teleport 层级 |

---

## 治理备注

- 技术分析与 [[tank-custom-ui-framework]] 共享自定义 UI 定位策略
- 弹窗B（选择危废品）的具体结构需 Selenium 交互后进一步抓取确认
- 建议在 PageObject 中为 `wh-filter-toolbar` 区域封装专区定位方法
