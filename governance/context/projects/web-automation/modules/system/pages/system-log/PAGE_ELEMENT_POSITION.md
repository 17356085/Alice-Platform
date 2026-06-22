# PAGE_ELEMENT_POSITION — system / system-log

> 基于 SystemLogPage.py 实际定位器常量

## 搜索区
| 元素 | 定位器常量 | 策略 | 值 |
|------|-----------|------|-----|
| 日志类型下拉 | LOG_TYPE_INPUT | XPATH | label含"日志类型"的el-select 或 placeholder含"请选择日志类型" |
| 日志级别下拉 | LOG_LEVEL_INPUT | XPATH | label含"日志级别"的el-select 或 placeholder含"请选择日志级别" |
| 模块名称输入 | MODULE_NAME_INPUT | XPATH | `//input[contains(@placeholder,"请输入模块名称")]` |
| 开始日期 | DATE_START_INPUT | XPATH | `//input[contains(@placeholder,"开始日期")]` |
| 结束日期 | DATE_END_INPUT | XPATH | `//input[contains(@placeholder,"结束日期")]` |
| 日期选择面板 | DATE_RANGE_PICKER_PANEL | XPATH | el-date-range-picker可见面板 |
| 下拉选项面板 | SELECT_DROPDOWN_PANEL | XPATH | `(//div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))])[last()]` |
| 搜索按钮 | SEARCH_BUTTON | XPATH | 文字"搜索" |
| 重置按钮 | RESET_BUTTON | XPATH | 文字"重置" |

## 工具栏
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 清空按钮 | TOOLBAR_CLEAR | XPATH 文字"清空" |

## 表格区
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 表格行 | TABLE_ROWS | XPATH `//div[contains(@class,"el-table__body-wrapper")]//table/tbody/tr` |
| 空文本 | EMPTY_TEXT | CSS `.el-table__empty-text` |
| 表头 | TABLE_HEADERS | XPATH `//div[contains(@class,"el-table__header-wrapper")]//th//div` |
| loading | LOADING_MASK | CSS `.el-loading-mask` |

## 分页区
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 分页器 | PAGINATION | CSS `.el-pagination` |
| 当前页 | CURRENT_PAGE | CSS `.el-pagination .el-pager li.active` |
| 下一页 | NEXT_PAGE | CSS `.el-pagination button.btn-next:not([disabled])` |

## 弹窗区
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 确认弹窗 | MESSAGEBOX_CONFIRM | XPATH el-message-box含确定按钮 |

## toast
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| toast文本 | TOAST_TEXT | CSS `.el-message__content` |

## 注意事项
- 日志类型和级别下拉使用 `el-select`，需点击触发→等待下拉面板→选择选项
- 下拉面板使用 `[last()]` 索引（页面可能有多个隐藏下拉面板）
- 无详情弹窗，表格直接展示日志内容
