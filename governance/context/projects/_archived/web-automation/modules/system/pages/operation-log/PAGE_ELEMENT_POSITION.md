# PAGE_ELEMENT_POSITION — system / operation-log

> 基于 OperationLogPage.py 实际定位器常量

## 搜索区
| 元素 | 定位器常量 | 策略 | 值 |
|------|-----------|------|-----|
| 系统模块输入 | SYSTEM_MODULE_INPUT | XPATH | `//input[contains(@placeholder,"请输入系统模块")]` |
| 操作类型输入 | OPERATION_TYPE_INPUT | XPATH | `//input[contains(@placeholder,"请输入操作类型")]` |
| 操作人员输入 | OPERATOR_INPUT | XPATH | `//input[contains(@placeholder,"请输入操作人员")]` |
| 状态-全部 | STATUS_ALL | XPATH | radio含"全部" |
| 状态-成功 | STATUS_SUCCESS | XPATH | radio含"成功" |
| 状态-失败 | STATUS_FAIL | XPATH | radio含"失败" |
| 状态下拉 | STATUS_SELECT | XPATH | label含"状态"的el-select |
| 开始日期 | DATE_START_INPUT | XPATH | `//input[contains(@placeholder,"开始日期")]` |
| 结束日期 | DATE_END_INPUT | XPATH | `//input[contains(@placeholder,"结束日期")]` |
| 日期选择面板 | DATE_RANGE_PICKER_PANEL | XPATH | el-date-range-picker可见面板 |
| 搜索按钮 | SEARCH_BUTTON_FALLBACK | XPATH | 文字"搜索" |
| 重置按钮 | RESET_BUTTON_FALLBACK | XPATH | 文字"重置" |

## 工具栏
| 元素 | 定位器常量 | 策略 |
|------|-----------|------|
| 清空按钮 | TOOLBAR_CLEAR_FALLBACK | XPATH 文字"清空" |
| 导出按钮 | TOOLBAR_EXPORT_FALLBACK | XPATH 文字"导出" |
| 第1行详情 | FIRST_ROW_DETAIL_FALLBACK | XPATH 第1行第8列按钮 |

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
