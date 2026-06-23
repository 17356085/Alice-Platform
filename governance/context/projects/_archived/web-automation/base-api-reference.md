# Base 层 API 参考

> **加载者**: automation-agent（必需）, project-agent（审计用）
> **来源**: `ZJSN_Test-master526/base/`

## BasePage — Page Object 基类

> 文件：`ZJSN_Test-master526/base/base_page.py`
> 所有新 Page Object **必须继承 BasePage**。

### 通用定位器（子类直接复用，无需重复定义）

| 定位器 | 类型 | 用途 |
|--------|------|------|
| `DIALOG` | CSS | 可见 el-dialog |
| `DIALOG_TITLE` | CSS | 弹窗标题 |
| `DIALOG_SAVE` | CSS | 弹窗 primary 按钮 |
| `DIALOG_CANCEL` | CSS | 弹窗取消按钮 |
| `TOAST` | CSS | el-message__content |
| `TOAST_ERROR` / `TOAST_SUCCESS` | CSS | 错误/成功 Toast |
| `FORM_ERROR` | CSS | el-form-item__error |
| `LOADING_MASK` | CSS | el-loading-mask |
| `MESSAGE_BOX` / `MESSAGE_BOX_CONFIRM` | CSS | MessageBox 弹窗及其确认按钮 |
| `DROPDOWN_OPTIONS` | CSS | body 下展开的下拉选项 |
| `TABLE_ROWS` | CSS | el-table__body-wrapper tbody tr.el-table__row |
| `TABLE_EMPTY` | CSS | 表格空状态 |
| `TOTAL_COUNT` | CSS | el-pagination__total |
| `NEXT_PAGE` / `PREV_PAGE` | CSS | 分页翻页按钮 |
| `SEARCH_BUTTON_CSS` / `SEARCH_BUTTON_XPATH` | CSS+XPATH | 搜索/查询按钮 |
| `RESET_BUTTON_CSS` / `RESET_BUTTON_XPATH` | CSS+XPATH | 重置按钮 |

### 核心方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `navigate_to(*menu_path)` | 变长参数 | 侧边栏导航 |
| `find(locator, timeout)` | → WebElement | 等待存在后返回 |
| `find_visible(locator, timeout)` | → WebElement | 等待可见后返回 |
| `find_clickable(locator, timeout)` | → WebElement | 等待可点击后返回 |
| `find_all(locator)` | → List[WebElement] | 返回所有匹配元素 |
| `click(locator, timeout)` | → WebElement | 智能点击（原生→JS→MouseEvent 三级降级） |
| `js_click(locator, timeout)` | → WebElement | JS 直接点击（绕过遮罩） |
| `input_text(locator, value, clear=True)` | → WebElement | 自动清空 + 输入 + v-model 触发 |
| `get_text(locator, timeout)` | → str | 获取元素文本 |
| `get_attribute(locator, name)` | → str | 获取属性值 |
| `is_visible(locator, timeout=3)` | → bool | 是否可见 |
| `is_present(locator, timeout=3)` | → bool | 是否在 DOM 中 |
| `wait_until_gone(locator, timeout)` | — | 等待元素从 DOM 消失 |
| `wait_until_visible(locator, timeout)` | → WebElement | 等待可见（Vue 渲染后常用） |
| `wait_page_ready(timeout=30)` | — | 等待 document.readyState == complete |
| `wait_vue_stable(timeout=5)` | — | 等待 Vue 动画完成（best-effort） |
| `wait_overlay_gone(timeout=10)` | — | 等待 Element Plus 遮罩消失 |
| `wait_dialog_open(timeout)` | → WebElement | 等待弹窗出现 |
| `wait_dialog_close(timeout)` | — | 等待弹窗关闭 |
| `get_dialog_title(timeout)` | → str | 获取弹窗标题 |
| `fill_dialog_input(label_text, value)` | — | 通过 label 定位并填充弹窗输入框 |
| `clear_dialog_input(label_text)` | — | 清空弹窗输入框 |
| `select_dialog_dropdown(label_text, option_text)` | — | 选择弹窗下拉选项 |
| `click_dialog_save(timeout=15)` | — | 点击弹窗保存（CSS→XPath→JS 三级降级） |
| `click_dialog_cancel()` | — | 点击弹窗取消 |
| `get_toast(timeout=5)` | → str | 获取 Toast 消息 |
| `wait_for_toast_text(timeout=6)` | → str | 轮询等待 Toast 出现 |
| `get_form_error(timeout=3)` | → str | 获取表单校验错误 |
| `confirm_message_box(timeout=8)` | — | 确认 MessageBox |
| `get_message_box_text(timeout=5)` | → str | 获取 MessageBox 文本 |
| `get_table_headers(min_columns=0)` | → list | JS 提取表头（含重试） |
| `get_table_row_count()` | → int | 当前页表格行数 |
| `get_column_data(col_index)` | → list | 获取指定列数据（1-based） |
| `get_cell(row_index, col_index)` | → str | 获取指定单元格 |
| `click_row_button(row_identifier, button_text)` | — | 表格行内按钮点击 |
| `is_row_present(text)` | → bool | 表格是否包含指定文本的行 |
| `get_total_count()` | → int | 获取分页总数 |
| `click_next_page()` | — | 翻到下一页 |
| `click_search_button(timeout)` | — | 搜索按钮（CSS→XPath→JS 三级降级） |
| `click_reset_button()` | — | 重置按钮（CSS→XPath→JS 三级降级） |
| `save_debug_snapshot(prefix)` | — | 保存诊断截图+HTML |
| `build_locator(by, value)` | → tuple | 便捷构造 `(By.XXX, "selector")` |

## BaseDriver — 浏览器驱动管理

> 文件：`ZJSN_Test-master526/base/browser_driver.py`

| 方法 | 说明 |
|------|------|
| `BaseDriver().open_browser()` | 启动 Chrome + 访问 BASE_URL（含重试） |
| `BaseDriver().close_browser()` | 关闭浏览器 + 停止 driver service |
| `ensure_logged_in(driver, username, password)` | 检测登录状态，按需执行登录 |

## ElementPlusHelper — Element Plus 组件操作

> 文件：`ZJSN_Test-master526/base/element_plus_helper.py`
> 提供 select_option / get_select_value / get_table_data / get_pagination_info / DatePicker 等操作

## SidebarNavigator — 侧边栏导航

> 文件：`ZJSN_Test-master526/base/sidebar_navigator.py`
> `SidebarNavigator(driver).navigate_to("一级菜单", "二级菜单", ...)` — 自动展开折叠菜单 + 滚动 + 点击
