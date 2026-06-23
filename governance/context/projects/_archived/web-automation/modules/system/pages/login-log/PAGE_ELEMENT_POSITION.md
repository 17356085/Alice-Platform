# PAGE_ELEMENT_POSITION — system / login-log

> 基于 LoginLogPage.py 实际定位器常量

## 搜索区
| 元素 | 定位器常量 | 策略 | 值 |
|------|-----------|------|-----|
| 用户名输入 | USERNAME_INPUT | XPATH | `//input[contains(@placeholder,"请输入用户名")]` |
| 状态-全部 | STATUS_ALL | XPATH | radio含"全部" |
| 状态-成功 | STATUS_SUCCESS | XPATH | radio含"成功" |
| 状态-失败 | STATUS_FAIL | XPATH | radio含"失败" |
| 状态下拉 | STATUS_SELECT | XPATH | label含"登录状态"或"状态"的el-select |
| 开始日期 | DATE_START_INPUT | XPATH | placeholder含"开始日期" |
| 结束日期 | DATE_END_INPUT | XPATH | placeholder含"结束日期" |
| 日期选择面板 | DATE_RANGE_PICKER_PANEL | XPATH | el-date-range-picker可见面板 |
| 搜索按钮 | SEARCH_BUTTON_FALLBACK | XPATH | 文字"搜索" |
| 重置按钮 | RESET_BUTTON_FALLBACK | XPATH | 文字"重置" |

## 工具栏
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 清空按钮 | TOOLBAR_CLEAR_FALLBACK | XPATH 文字"清空" |
| 导出按钮 | TOOLBAR_EXPORT_FALLBACK | XPATH 文字"导出" |

## 表格区
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 表格行 | TABLE_ROWS (继承BasePage) | XPATH |
| 空文本 | EMPTY_TEXT | CSS `.el-table__empty-text` |
| 表头 | TABLE_HEADERS | XPATH `//div[contains(@class,"el-table__header-wrapper")]//th//div` |
| loading | LOADING_MASK (继承BasePage) | CSS `.el-loading-mask` |

## 详情弹窗
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 详情弹窗标题 | DETAIL_DIALOG_TITLE | XPATH `//*[contains(@class,"el-dialog__title") and normalize-space(.)="登录日志详情"]` |
| 详情标题回退 | DETAIL_TITLE_STRICT | XPATH login-log-detail-dialog内el-dialog__title |

## 弹窗区
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 确认弹窗 | MESSAGEBOX_CONFIRM | XPATH el-message-box含确定按钮 |

## toast
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| toast文本 | TOAST_TEXT | CSS `.el-message__content` |
| toast增强 | TOAST_MESSAGE_ENHANCED | XPATH el-message__content非空 |

## 公共组件复用
| 方法 | 来源 |
|------|------|
| click_search_button() / click_reset_button() | BasePage JS文本搜索 |
| get_table_rows() / get_total_count() | BasePage |
